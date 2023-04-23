import json
from abc import ABC, abstractmethod

import boto3
from dotenv import load_dotenv
from os import environ

load_dotenv()


class Environment(ABC):
    @property
    def api_base_url(self) -> str:
        return environ.get('API_BASE_URL')

    @property
    @abstractmethod
    def login(self) -> str:
        pass

    @property
    @abstractmethod
    def password(self) -> str:
        pass

    @property
    @abstractmethod
    def account(self) -> str:
        pass


class LocalEnvironment(Environment):
    @property
    def login(self) -> str:
        return environ.get('LOGIN')

    @property
    def password(self) -> str:
        return environ.get('PASSWORD')

    @property
    def account(self) -> str:
        return environ.get('ACCOUNT')


class AwsEnvironment(Environment):
    def __init__(self):
        self.__secret: dict = json.loads(
            boto3.client('secretsmanager')
            .get_secret_value(SecretId=environ.get('SECRET_ID'))
            .get('SecretString')
        )

    @property
    def login(self) -> str:
        return self.__secret.get('LOGIN')

    @property
    def password(self) -> str:
        return self.__secret.get('PASSWORD')

    @property
    def account(self) -> str:
        return self.__secret.get('ACCOUNT')
