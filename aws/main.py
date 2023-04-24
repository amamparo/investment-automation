from functools import reduce
from os import getcwd
from typing import List, Dict, cast

from aws_cdk import Stack, App, Duration, Environment
from aws_cdk.aws_applicationautoscaling import Schedule, ScalingInterval
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_ecs import Cluster, ContainerImage, Secret as EcsSecret
from aws_cdk.aws_ecs_patterns import ScheduledFargateTask, ScheduledFargateTaskImageOptions, \
    QueueProcessingFargateService
from aws_cdk.aws_iam import PolicyStatement, Effect
from aws_cdk.aws_secretsmanager import Secret
from aws_cdk.aws_sqs import Queue
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

        underlyings_queue = Queue(
            self,
            'underlyings-queue',
            retention_period=Duration.hours(1),
            visibility_timeout=Duration.minutes(15),
            receive_message_wait_time=Duration.seconds(20)
        )

        enqueue_underlyings_task = ScheduledFargateTask(
            self,
            'enqueue-underlyings-task',
            cluster=cluster,
            schedule=Schedule.cron(week_day='MON-FRI', hour='13', minute='0'),
            scheduled_fargate_task_image_options=ScheduledFargateTaskImageOptions(
                image=container_image,
                command=['python', '-m', 'src.enqueue_underlyings'],
                environment={
                    'API_BASE_URL': API_BASE_URL,
                    'UNDERLYINGS_QUEUE_URL': underlyings_queue.queue_url
                },
                secrets=secrets
            )
        )

        enqueue_underlyings_task.task_definition.add_to_task_role_policy(
            allow(['sqs:SendMessage*'], [underlyings_queue.queue_arn])
        )

        process_underlyings_task = QueueProcessingFargateService(
            self,
            'process-underlyings-task',
            cluster=cluster,
            queue=underlyings_queue,
            image=container_image,
            command=['python', '-m', 'src.process_underlyings'],
            environment={
                'API_BASE_URL': API_BASE_URL,
                'UNDERLYINGS_QUEUE_URL': underlyings_queue.queue_url
            },
            secrets=secrets,
            min_scaling_capacity=0,
            max_scaling_capacity=10,
            scaling_steps=[
                ScalingInterval(
                    upper=0,
                    change=-10
                ),
                ScalingInterval(
                    lower=1,
                    change=+10
                )
            ]
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
