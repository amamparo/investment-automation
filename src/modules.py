import json
from os import environ

import boto3
from injector import singleton, provider, Module

from src.environment import Environment

from dotenv import load_dotenv

load_dotenv()


class LocalModule(Module):
    @singleton
    @provider
    def provide_environment(self) -> Environment:
        return Environment(
            m1_login=environ.get('M1_LOGIN'),
            m1_password=environ.get('M1_PASSWORD'),
            m1_pie_id=environ.get('M1_PIE_ID')
        )


class LambdaModule(Module):
    @singleton
    @provider
    def provide_environment(self) -> Environment:
        secret = json.loads(
            boto3.client('secretsmanager').get_secret_value(SecretId=environ.get('SECRET_ID'))['SecretString']
        )
        return Environment(
            m1_login=secret['M1_LOGIN'],
            m1_password=secret['M1_PASSWORD'],
            m1_pie_id=secret['M1_PIE_ID']
        )
