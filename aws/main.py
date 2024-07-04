from os import getcwd
from typing import List, cast

from aws_cdk import Stack, App, Duration
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_iam import PolicyStatement, Effect
from aws_cdk.aws_lambda import DockerImageFunction, DockerImageCode, IFunction
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct


class InvestmentAutomationStack(Stack):
    def __init__(self, scope: Construct):
        super().__init__(scope, 'investment-automation')
        secret = Secret(self, 'secret', secret_name='investment-automation-environment')
        function = DockerImageFunction(
            self,
            'function',
            reserved_concurrent_executions=1,
            function_name='investment-automation',
            memory_size=256,
            code=DockerImageCode.from_image_asset(
                directory=getcwd(),
                platform=Platform.LINUX_AMD64,
                cmd=['src.main.lambda_handler']
            ),
            timeout=Duration.minutes(15),
            environment={'SECRET_ID': secret.secret_name}
        )
        secret.grant_read(function)
        Rule(
            self,
            'schedule',
            schedule=Schedule.cron(day='1', hour='13', minute='0')
        ).add_target(LambdaFunction(cast(IFunction, function)))


def allow(actions: List[str], resources: List[str]) -> PolicyStatement:
    return PolicyStatement(
        effect=Effect.ALLOW,
        actions=actions,
        resources=resources
    )


if __name__ == '__main__':
    app = App()
    InvestmentAutomationStack(app)
    app.synth()
