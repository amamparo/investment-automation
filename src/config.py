import json
from dataclasses import dataclass
from os import environ

import boto3
from dotenv import load_dotenv
from injector import Module, provider, singleton

load_dotenv()


@dataclass
class Environment:
    login: str
    password: str
    api_base_url: str = environ.get('API_BASE_URL')


class LocalModule(Module):
    @singleton
    @provider
    def provide_environment(self) -> Environment:
        return Environment(
            login=environ.get('LOGIN'),
            password=environ.get('PASSWORD')
        )


class LambdaModule(Module):
    @singleton
    @provider
    def provide_environment(self) -> Environment:
        secret = json.loads(
            boto3.client('secretsmanager').get_secret_value(SecretId=environ.get('SECRET_ID'))['SecretString']
        )
        return Environment(
            login=secret['LOGIN'],
            password=secret['PASSWORD']
        )
