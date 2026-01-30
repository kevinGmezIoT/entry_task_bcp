from constructs import Construct
from aws_cdk import (
    Stack,
    SecretValue,
    Fn,
    aws_codepipeline as codepipeline,
    aws_ssm as ssm,
    aws_chatbot as chatbot,
    aws_ecr as ecr,
    aws_codestarnotifications as codestarnotifications,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_iam as iam
)


class PipelineStack(Stack):

    def __init__(self, scope: Construct, id: str,
        environment='',
        repository_owner='',
        repository='',
        repository_branch='',
        backend_repository=None,
        agents_repository=None,
        frontend_bucket=None,
        policy_bucket=None,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.__repository = repository
        self.__repository_branch = repository_branch
        self.__repository_owner = repository_owner
        self.__environment = environment
        self.__backend_repository = backend_repository
        self.__agents_repository = agents_repository
        self.__frontend_bucket = frontend_bucket
        self.__policy_bucket = policy_bucket
        self.createPipeline();
        self.createSourceStage();
        self.createBuildStage();

    def createPipeline(self):
        self.pipeline = codepipeline.Pipeline(
            self,
            'EntryPipeline' + self.__environment,
            pipeline_type=codepipeline.PipelineType.V2
        )

    def createSourceStage(self):
        self.source_output = codepipeline.Artifact('SourceOutput')
        source_action = codepipeline_actions.GitHubSourceAction(
            action_name='Github',
            output=self.source_output,
            oauth_token=SecretValue.secrets_manager('GITHUB-TOKEN'),
            owner=self.__repository_owner,
            repo=self.__repository,
            branch=self.__repository_branch
        )
        self.pipeline.add_stage(
            stage_name='Source',
            actions=[source_action]
        )

    def createBuildStage(self):
        # Resolve repository names
        backend_repo_name = self.__backend_repository.repository_name if self.__backend_repository else Fn.import_value("EntryBackendRepoName-" + self.__environment)
        agents_repo_name = self.__agents_repository.repository_name if self.__agents_repository else Fn.import_value("EntryAgentsRepoName-" + self.__environment)
        frontend_bucket_name = self.__frontend_bucket.bucket_name if self.__frontend_bucket else Fn.import_value("EntryFrontendBucketName-" + self.__environment)

        project = codebuild.PipelineProject(self, 'BuildProject',
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=True,
            ),
            environment_variables={
                'AWS_ACCOUNT_ID': codebuild.BuildEnvironmentVariable(value=Stack.of(self).account),
                'AWS_DEFAULT_REGION': codebuild.BuildEnvironmentVariable(value=Stack.of(self).region),
                'BACKEND_REPO_NAME': codebuild.BuildEnvironmentVariable(value=backend_repo_name),
                'AGENTS_REPO_NAME': codebuild.BuildEnvironmentVariable(value=agents_repo_name),
                'FRONTEND_BUCKET_NAME': codebuild.BuildEnvironmentVariable(value=frontend_bucket_name),
                'ENVIRONMENT': codebuild.BuildEnvironmentVariable(value=self.__environment),
            },
            build_spec=codebuild.BuildSpec.from_object({
                'version': '0.2',
                'phases': {
                    'install': {
                        'runtime-versions': {
                            'python': '3.12',
                            'nodejs': '20'
                        },
                        'commands': [
                            'pip install -r cdk/requirements.txt',
                            'npm install aws-cdk -g'
                        ]
                    },
                    'pre_build': {
                        'commands': [
                            'echo Logging in to Amazon ECR...',
                            'aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com'
                        ]
                    },
                    'build': {
                        'commands': [
                            'echo Building Backend Docker image...',
                            'docker build -t $BACKEND_REPO_NAME:latest ./backend',
                            'docker tag $BACKEND_REPO_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$BACKEND_REPO_NAME:latest',
                            
                            'echo Building Agents Docker image...',
                            'docker build -t $AGENTS_REPO_NAME:latest ./agents',
                            'docker tag $AGENTS_REPO_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$AGENTS_REPO_NAME:latest',
                            
                            'echo Building Frontend...',
                            'BACKEND_URL=$(aws cloudformation describe-stacks --stack-name EntryTaskBcp$ENVIRONMENT --query "Stacks[0].Outputs[?OutputKey==\'BackendURL\'].OutputValue" --output text)',
                            'cd frontend && npm install && VITE_API_URL=${BACKEND_URL}/api npm run build && cd ..'
                        ]
                    },
                    'post_build': {
                        'commands': [
                            'echo Pushing Docker images...',
                            'docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$BACKEND_REPO_NAME:latest',
                            'docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$AGENTS_REPO_NAME:latest',
                            
                            'echo Syncing Frontend to S3...',
                            'aws s3 sync frontend/dist s3://$FRONTEND_BUCKET_NAME --delete',
                            
                            'echo Deploying CDK stacks...',
                            'cdk deploy --all --app "python cdk/main.py" --require-approval never -c environment=' + self.__environment,
                            
                            'echo Running Migrations and RAG Ingestion...',
                            'CLUSTER_NAME=$(aws cloudformation describe-stacks --stack-name EntryTaskBcpResources$ENVIRONMENT --query "Stacks[0].Outputs[?ExportName==\'EntryClusterName-$ENVIRONMENT\'].OutputValue" --output text)',
                            'SERVICE_NAME=$(aws ecs list-services --cluster $CLUSTER_NAME --query "serviceArns[?contains(@, \'BackendService\')]" --output text | cut -d "/" -f 3)',
                            'TASK_DEFINITION=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --query "services[0].taskDefinition" --output text)',
                            'VPC_ID=$(aws cloudformation describe-stacks --stack-name EntryTaskBcpResources$ENVIRONMENT --query "Stacks[0].Outputs[?ExportName==\'EntryVpcId-$ENVIRONMENT\'].OutputValue" --output text)',
                            'SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Public*" --query "Subnets[*].SubnetId" --output text | sed "s/\\t/,/g")',
                            'SG_ID=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --query "services[0].networkConfiguration.awsvpcConfiguration.securityGroups[0]" --output text)',
                            
                            'aws ecs run-task --cluster $CLUSTER_NAME --task-definition $TASK_DEFINITION --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" --overrides "{\\\"containerOverrides\\\": [{\\\"name\\\": \\\"BackendContainer\\\", \\\"command\\\": [\\\"python\\\", \\\"manage.py\\\", \\\"seed_data\\\"]}]}"',
                            'aws ecs run-task --cluster $CLUSTER_NAME --task-definition $TASK_DEFINITION --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" --overrides "{\\\"containerOverrides\\\": [{\\\"name\\\": \\\"BackendContainer\\\", \\\"command\\\": [\\\"python\\\", \\\"manage.py\\\", \\\"ingest_rag\\\"]}]}"'
                        ]
                    },
                }
            })
        )
        
        # Grant permissions
        project.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "ecr:*", 
                "s3:*", 
                "ssm:*", 
                "secretsmanager:*", 
                "ecs:*", 
                "elasticloadbalancing:*", 
                "iam:*", 
                "cloudfront:*",
                "ec2:*", 
                "sts:AssumeRole",
                "cloudformation:*"
            ],
            resources=["*"]
        ))
        
        build_output = codepipeline.Artifact('BuildOutput')
        build_action = codepipeline_actions.CodeBuildAction(
            action_name='BuildAndDeploy',
            project=project,
            input=self.source_output,
            outputs=[build_output],
        )
        self.pipeline.add_stage(
            stage_name='BuildAndDeploy',
            actions=[build_action]
        )

