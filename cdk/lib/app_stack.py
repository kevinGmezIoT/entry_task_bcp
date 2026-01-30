from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    Fn,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_secretsmanager as secretsmanager,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_servicediscovery as servicediscovery,
    CfnOutput
)


class AppStack(Stack):

    def __init__(self, scope: Construct, id: str,
                 environment='',
                 vpc=None,
                 cluster=None,
                 backend_repository=None,
                 agents_repository=None,
                 frontend_bucket=None,
                 policy_bucket=None,
                 origin_access_identity=None,
                 **kwargs

                 ) -> None:
        super().__init__(scope, id, **kwargs)

        # 1. Get resources (either passed in or looked up from Exports)
        if vpc is None:
             vpc_id = Fn.import_value("EntryVpcId-" + environment)
             vpc = ec2.Vpc.from_vpc_attributes(self, "VpcLookup", 
                vpc_id=vpc_id,
                availability_zones=["us-east-1a", "us-east-1b"]
             )
        
        if cluster is None:
            cluster = ecs.Cluster.from_cluster_attributes(self, "ClusterLookup",
                cluster_name=Fn.import_value("EntryClusterName-" + environment),
                vpc=vpc
            )
        
        if backend_repository is None:
            backend_repository = ecr.Repository.from_repository_name(self, "BackendRepoLookup", 
                Fn.import_value("EntryBackendRepoName-" + environment)
            )

        if agents_repository is None:
            agents_repository = ecr.Repository.from_repository_name(self, "AgentsRepoLookup", 
                Fn.import_value("EntryAgentsRepoName-" + environment)
            )
            
        if frontend_bucket is None:
            frontend_bucket = s3.Bucket.from_bucket_name(self, "FrontendBucketLookup",
                Fn.import_value("EntryFrontendBucketName-" + environment)
            )

        if policy_bucket is None:
            policy_bucket = s3.Bucket.from_bucket_name(self, "PolicyBucketLookup",
                Fn.import_value("EntryPolicyBucketName-" + environment)
            )

        # 2. Define Environment Variables and Secrets
        
        # Common Secrets (Bedrock, OpenAI, etc) - From Secrets Manager
        common_secrets = {
            "TAVILY_API_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(self, "TavilySecret", "TAVILY_API_KEY")
            ),
            "LANGCHAIN_API_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(self, "LangChainSecret", "LANGCHAIN_API_KEY")
            ),
        }

        backend_secrets = {
            **common_secrets,
            "DJANGO_SECRET_KEY": ecs.Secret.from_secrets_manager(
                secretsmanager.Secret.from_secret_name_v2(self, "DjangoSecret", "DJANGO_SECRET_KEY")
            ),
        }

        # Backend specific env from Parameter Store + Dynamic Resources
        backend_env = {
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_DEBUG": ssm.StringParameter.value_for_string_parameter(self, f"/entry-task/{environment}/django-debug"),
            "DATABASE_URL": ssm.StringParameter.value_for_string_parameter(self, f"/entry-task/{environment}/database-url"),
            "S3_POLICY_BUCKET": policy_bucket.bucket_name,
            "AWS_REGION": Stack.of(self).region,
            "AGENTS_SERVICE_URL": "http://agents.local:5001",
        }

        # Agents specific env from Parameter Store
        agents_env = {
            "BEDROCK_KB_ID": ssm.StringParameter.value_for_string_parameter(self, f"/entry-task/{environment}/bedrock-kb-id"),
            "BEDROCK_DS_ID": ssm.StringParameter.value_for_string_parameter(self, f"/entry-task/{environment}/bedrock-ds-id"),
            "AWS_REGION": Stack.of(self).region,
        }

        # 3. Define Fargate Services

        # Backend Service with Load Balancer
        backend_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "BackendService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            public_load_balancer=True,
            assign_public_ip=True,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.X86_64
            ),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(backend_repository, "latest"),
                container_port=8000,
                container_name="BackendContainer",
                environment=backend_env,
                secrets=backend_secrets,
                log_driver=ecs.LogDrivers.aws_logs(stream_prefix="Backend")
            ),
            health_check_grace_period=Duration.seconds(60)
        )

        # Agents Service (Separate Service)
        agents_task_def = ecs.FargateTaskDefinition(self, "AgentsTaskDef",
            cpu=512,
            memory_limit_mib=1024
        )
        
        agents_task_def.add_container("AgentsContainer",
            image=ecs.ContainerImage.from_ecr_repository(agents_repository, "latest"),
            environment=agents_env,
            secrets=common_secrets,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="Agents"),
            port_mappings=[ecs.PortMapping(container_port=5001)]
        )

        agents_service = ecs.FargateService(self, "AgentsService",
            cluster=cluster,
            task_definition=agents_task_def,
            desired_count=1,
            assign_public_ip=True,
            cloud_map_options=ecs.CloudMapOptions(
                name="agents",
                dns_record_type=servicediscovery.DnsRecordType.A,
                dns_ttl=Duration.seconds(60)
            )
        )


        # Allow Backend to talk to Agents
        # Note: In a real prod environment, we would use CloudMap/Service Discovery.
        # Since we are in a challenge, let's keep it simple: the backend will talk to agents via their private IP
        # as they are in the same VPC. For more robust discovery, we'd use 'agents.local'.
        agents_service.connections.allow_from(backend_service.service, ec2.Port.tcp(5001))

        # Health checks
        backend_service.target_group.configure_health_check(
            path="/api/health/",
            interval=Duration.seconds(30)
        )

        # 4. CloudFront for Frontend
        if origin_access_identity is None:
            origin_access_identity = cloudfront.OriginAccessIdentity.from_origin_access_identity_id(
                self, "OAI", Fn.import_value("EntryOaiId-" + environment)
            )

        distribution = cloudfront.Distribution(self, "FrontendDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_identity(
                    frontend_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html"
                )
            ]
        )


        # 5. IAM Permissions and Outputs
        # Grant permissions to Backend for S3 and Bedrock
        policy_bucket.grant_read_write(backend_service.task_definition.task_role)
        
        bedrock_policy = iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel", 
                "bedrock:Retrieve", 
                "bedrock:RetrieveAndGenerate",
                "bedrock:StartIngestionJob"
            ],
            resources=["*"]
        )
        backend_service.task_definition.task_role.add_to_policy(bedrock_policy)
        agents_task_def.task_role.add_to_policy(bedrock_policy)

        CfnOutput(self, "BackendURL", value=f"http://{backend_service.load_balancer.load_balancer_dns_name}")
        CfnOutput(self, "FrontendURL", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "PolicyBucketName", value=policy_bucket.bucket_name)
