import json
from dataclasses import dataclass
from os import environ
from typing import List

import boto3
from dotenv import load_dotenv
from injector import Module, provider, singleton
from tastytrade_sdk import Tastytrade

load_dotenv()


@dataclass
class Environment:
    login: str
    password: str
    portfolio_symbols: List[str]
    account_number: str


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
            account_number=environ.get('ACCOUNT_NUMBER'),
            portfolio_symbols=environ.get('PORTFOLIO_SYMBOLS').split(',')
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
            account_number=secret['ACCOUNT_NUMBER'],
            portfolio_symbols=environ.get('PORTFOLIO_SYMBOLS').split(',')
        )
