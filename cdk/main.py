from aws_cdk import App, Environment as CdkEnvironment
from lib.resources_stack import ResourcesStack
from lib.app_stack import AppStack
from lib.pipeline_stack import PipelineStack
from constants import (
    resources_stack_name, stack_name, pipeline_stack_name,
    aws_account, aws_region,
    repository_owner, repository, repository_branch
)

app = App()
environment = app.node.try_get_context('environment') or 'LOCAL'

# 1. Resources Stack
resources_stack = ResourcesStack(app, resources_stack_name(environment),
    environment=environment,
    env=CdkEnvironment(account=aws_account, region=aws_region(environment)),
)

# 2. App Stack
app_stack = AppStack(app, stack_name(environment),
    environment=environment,
    vpc=resources_stack.vpc,
    cluster=resources_stack.cluster,
    backend_repository=resources_stack.backend_repository,
    agents_repository=resources_stack.agents_repository,
    frontend_bucket=resources_stack.frontend_bucket,
    env=CdkEnvironment(account=aws_account, region=aws_region(environment)),
)

# 3. Pipeline Stack
pipeline_stack = PipelineStack(app, pipeline_stack_name(environment),
    environment=environment,
    repository_owner=repository_owner,
    repository=repository,
    repository_branch=repository_branch,
    backend_repository=resources_stack.backend_repository,
    agents_repository=resources_stack.agents_repository,
    frontend_bucket=resources_stack.frontend_bucket,
    env=CdkEnvironment(account=aws_account, region=aws_region(environment)),
)

app.synth()

