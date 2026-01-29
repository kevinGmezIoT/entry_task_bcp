from aws_cdk import App
from lib.resources_stack import ResourcesStack
import constants

app = App()
environment = app.node.try_get_context('environment') or 'LOCAL'
ResourcesStack(app, constants.resources_stack_name(environment),
         environment=environment,
         env={
             'account': constants.aws_account,
             'region': constants.aws_region(environment),
         }
         )

app.synth()
