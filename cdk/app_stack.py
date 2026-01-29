from aws_cdk import App
from lib.app_stack import AppStack
import constants

app = App()
environment = app.node.try_get_context('environment') or 'LOCAL'
AppStack(app, constants.stack_name(environment),
         environment=environment,
         reevalua_api_notification_url=constants.reevalua_api_notification_url,
         env={
             'account': constants.aws_account,
             'region': constants.aws_region(environment),
         }
         )

app.synth()
