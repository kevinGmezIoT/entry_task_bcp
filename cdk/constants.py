stack = 'EntryTaskBcp'
aws_account = '495297548455'
configuration_by_environment = {
    'DEV': {
        'region': 'us-east-2',
    },
    'PROD': {
        'region': 'us-east-2',
    }
}

repository_owner = 'kevinGmezIoT'
repository = 'entry_task_bcp'
repository_branch = 'master'

def configuration(environment: str):
    global configuration_by_environment
    if environment not in configuration_by_environment:
        raise Exception('Environment ({0}) not defined'.format(environment))

    return configuration_by_environment[environment]


def stack_name(environment: str):
    return stack + environment

def resources_stack_name(environment: str):
    return stack + 'Resources' + environment

def pipeline_stack_name(environment: str):
    return stack + 'Pipeline' + environment

def aws_region(environment: str):
    return configuration(environment)['region']

