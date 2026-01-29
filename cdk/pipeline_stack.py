from aws_cdk import App
from lib.pipeline_stack import PipelineStack
import constants

app = App()
environment = app.node.try_get_context('environment') or 'LOCAL'
PipelineStack(app, constants.pipeline_stack_name(environment),
    environment=environment,
    env={
        'account': constants.aws_account,
        'region': constants.aws_region(environment),
    },
    repository_owner=constants.repository_owner,
    repository=constants.repository,
    repository_branch=constants.repository_branch
)

app.synth()
