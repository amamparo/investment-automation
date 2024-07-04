import json
from os import environ

import boto3
from injector import singleton, provider, Module
from tastytrade_sdk import Tastytrade

from src.environment import Environment

from dotenv import load_dotenv

load_dotenv()


class CommonModule(Module):
    @singleton
    @provider
    def provide_tastytrade(self, env: Environment) -> Tastytrade:
        return Tastytrade().login(login=env.login, password=env.password)


class LocalModule(CommonModule):
    @singleton
    @provider
    def provide_environment(self) -> Environment:
        return Environment(
            login=environ.get('LOGIN'),
            password=environ.get('PASSWORD'),
            account_number=environ.get('ACCOUNT_NUMBER')
        )


class LambdaModule(CommonModule):
    @singleton
    @provider
    def provide_environment(self) -> Environment:
        secret = json.loads(
            boto3.client('secretsmanager').get_secret_value(SecretId=environ.get('SECRET_ID'))['SecretString']
        )
        return Environment(
            login=secret['LOGIN'],
            password=secret['PASSWORD'],
            account_number=secret['ACCOUNT_NUMBER']
        )
