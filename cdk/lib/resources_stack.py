from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_s3 as s3,
    aws_ssm as ssm,
    aws_iam as iam,
    RemovalPolicy
)


class ResourcesStack(Stack):

    def __init__(self, scope: Construct, id: str,
        environment='',
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # 1. VPC For the Cluster - Configured without NAT Gateways to avoid EIP limits
        self.vpc = ec2.Vpc(self, "McpVpc",
            max_azs=2,
            nat_gateways=0, 
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # 2. ECS Cluster
        self.cluster = ecs.Cluster(self, "EntryTaskCluster",
            vpc=self.vpc
        )

        # 3. ECR Repositories
        self.backend_repository = ecr.Repository(self, "BackendRepo",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True
        )

        self.agents_repository = ecr.Repository(self, "AgentsRepo",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True
        )

        # 4. S3 Bucket for Frontend Hosting
        self.frontend_bucket = s3.Bucket(self, "FrontendBucket",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Exporting values
        CfnOutput(self, "VpcId", value=self.vpc.vpc_id, export_name="EntryVpcId-" + environment)
        CfnOutput(self, "ClusterName", value=self.cluster.cluster_name, export_name="EntryClusterName-" + environment)
        CfnOutput(self, "BackendRepoName", value=self.backend_repository.repository_name, export_name="EntryBackendRepoName-" + environment)
        CfnOutput(self, "AgentsRepoName", value=self.agents_repository.repository_name, export_name="EntryAgentsRepoName-" + environment)
        CfnOutput(self, "FrontendBucketName", value=self.frontend_bucket.bucket_name, export_name="EntryFrontendBucketName-" + environment)

