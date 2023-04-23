from dataclasses import dataclass
from os import getcwd
from typing import List, Dict, cast

from aws_cdk import Stack, App, Duration
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy, PolicyDocument, PolicyStatement, Effect
from aws_cdk.aws_lambda import Function, DockerImageFunction, DockerImageCode
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct


class MatchProcessorStack(Stack):
    def __init__(self, scope: Construct):
        super().__init__(scope, 'tastytrade-bot')

        buy_spy = create_function(
            self,
            name='buy-spy',
            cmd='src.buy_spy.lambda_handler',
            env={},
            memory_size=256,
            reserved_concurrent_executions=100
        )


@dataclass
class Allow:
    actions: List[str]
    resources: List[str]


def create_function(scope: Construct, name: str, cmd: str, env: Dict[str, str], allows: List[Allow] = tuple([]),
                    memory_size: int = 512, reserved_concurrent_executions: int = 1) -> Function:
    return DockerImageFunction(
        scope,
        f'{name}-function',
        function_name=name,
        reserved_concurrent_executions=reserved_concurrent_executions,
        memory_size=memory_size,
        timeout=Duration.minutes(15),
        log_retention=RetentionDays.FIVE_DAYS,
        code=DockerImageCode.from_image_asset(
            directory=getcwd(),
            platform=cast(Platform, Platform.LINUX_AMD64),
            file='Dockerfile',
            cmd=[cmd]
        ),
        environment=env,
        role=Role(
            scope,
            f'{name}-role',
            assumed_by=ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')],
            inline_policies={
                'Policies': PolicyDocument(statements=[
                    PolicyStatement(
                        effect=Effect.ALLOW,
                        actions=allow.actions,
                        resources=allow.resources
                    )
                    for allow in allows
                ])
            }
        )
    )


if __name__ == '__main__':
    app = App()
    MatchProcessorStack(app)
    app.synth()
