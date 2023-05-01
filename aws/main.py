from os import getcwd
from typing import List, cast

from aws_cdk import Stack, App, Duration
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_iam import PolicyStatement, Effect, Role, IPrincipal, ServicePrincipal, ManagedPolicy, PolicyDocument
from aws_cdk.aws_lambda import DockerImageFunction, DockerImageCode
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct

API_BASE_URL: str = 'https://api.tastyworks.com'


class TastytradeAutomationStack(Stack):
    def __init__(self, scope: Construct):
        super().__init__(scope, 'tastytrade-automation')
        secret = Secret(self, 'secret', secret_name='tastytrade-automation-environment')
        function = DockerImageFunction(
            self,
            'function',
            reserved_concurrent_executions=1,
            function_name='update-high-iv-watchlist',
            memory_size=512,
            code=DockerImageCode.from_image_asset(
                directory=getcwd(),
                platform=Platform.LINUX_AMD64,
                cmd=['src.update_watchlist.lambda_handler']
            ),
            timeout=Duration.minutes(15),
            environment={
                'API_BASE_URL': API_BASE_URL,
                'SECRET_ID': secret.secret_name
            },
            role=Role(
                self,
                'role',
                role_name='update-high-iv-watchlist-role',
                assumed_by=cast(IPrincipal, ServicePrincipal('lambda.amazonaws.com')),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaVPCAccessExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
                ],
                inline_policies={
                    'Policies': PolicyDocument(statements=[
                        allow(['secretsmanager:GetSecretValue'], [secret.secret_arn])
                    ])
                }
            )
        )
        Rule(
            self,
            'schedule',
            schedule=Schedule.cron(week_day='MON-FRI', hour='13', minute='0')
        ).add_target(LambdaFunction(function))


def allow(actions: List[str], resources: List[str]) -> PolicyStatement:
    return PolicyStatement(
        effect=Effect.ALLOW,
        actions=actions,
        resources=resources
    )


if __name__ == '__main__':
    app = App()
    TastytradeAutomationStack(app)
    app.synth()
