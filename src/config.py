import json
from os import environ

import boto3
from dotenv import load_dotenv
from injector import Module, provider, singleton
from tastytrade_sdk import Tastytrade

load_dotenv()


class LocalModule(Module):
    @singleton
    @provider
    def provide_tastytrade(self) -> Tastytrade:
        return Tastytrade(login=environ.get('LOGIN'), password=environ.get('PASSWORD'))


class LambdaModule(Module):
    @singleton
    @provider
    def provide_tastytrade(self) -> Tastytrade:
        secret = json.loads(
            boto3.client('secretsmanager').get_secret_value(SecretId=environ.get('SECRET_ID'))['SecretString']
        )
        return Tastytrade(login=secret['LOGIN'], password=secret['PASSWORD'])
