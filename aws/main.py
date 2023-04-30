from functools import reduce
from os import getcwd
from typing import List, Dict, cast

from aws_cdk import Stack, App, Environment
from aws_cdk.aws_applicationautoscaling import Schedule
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_ecs import Cluster, ContainerImage, Secret as EcsSecret
from aws_cdk.aws_ecs_patterns import ScheduledFargateTask, ScheduledFargateTaskImageOptions
from aws_cdk.aws_iam import PolicyStatement, Effect
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct

from dotenv import load_dotenv
from os import environ

load_dotenv()

API_BASE_URL: str = 'https://api.tastyworks.com'


class TastytradeAutomationStack(Stack):
    def __init__(self, scope: Construct):
        super().__init__(scope, 'tastytrade-automation',
                         env=Environment(account=environ.get('AWS_REGION'), region=environ.get('AWS_DEFAULT_REGION')))

        container_image = ContainerImage.from_asset(directory=getcwd(), platform=cast(Platform, Platform.LINUX_AMD64))

        cluster = Cluster(self, 'cluster', cluster_name='tastytrade-automation')

        secret = Secret(self, 'secret', secret_name='tastytrade-automation-environment')

        secrets: Dict[str, EcsSecret] = reduce(
            lambda agg, key: {**agg, **{key: EcsSecret.from_secrets_manager(secret, key)}},
            ['LOGIN', 'PASSWORD', 'ACCOUNT'],
            {}
        )

        ScheduledFargateTask(
            self,
            'update-watchlist-task',
            cluster=cluster,
            schedule=Schedule.cron(week_day='MON-FRI', hour='13', minute='0'),
            cpu=256,
            memory_limit_mib=512,
            scheduled_fargate_task_image_options=ScheduledFargateTaskImageOptions(
                image=container_image,
                command=['python', '-m', 'src.update_watchlist'],
                environment={
                    'API_BASE_URL': API_BASE_URL
                },
                secrets=secrets
            )
        )


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
