import json
from abc import ABC, abstractmethod

import boto3
from dotenv import load_dotenv
from os import environ

from injector import singleton

load_dotenv()


@singleton
class Environment(ABC):
    @property
    def api_base_url(self) -> str:
        return environ.get('API_BASE_URL')

    @abstractmethod
    @property
    def login(self) -> str:
        pass

    @abstractmethod
    @property
    def password(self) -> str:
        pass


class LocalEnvironment(Environment):
    login: str = environ.get('LOGIN')
    password: str = environ.get('PASSWORD')


class LambdaEnvironment(Environment):
    def __init__(self):
        secrets_client = boto3.client('secretsmanager')
        self.__secret: dict = json.loads(
            secrets_client.get_secret_value(SecretId=environ.get('SECRET_ID'))['SecretString']
        )

    @property
    def login(self) -> str:
        return self.__secret['LOGIN']

    @property
    def password(self) -> str:
        return self.__secret['PASSWORD']
