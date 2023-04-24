from dataclasses import dataclass

from dotenv import load_dotenv
from os import environ

load_dotenv()


@dataclass
class Environment:
    api_base_url: str = environ.get('API_BASE_URL')
    login: str = environ.get('LOGIN')
    password: str = environ.get('PASSWORD')
    account: str = environ.get('ACCOUNT')
    underlyings_queue_url: str = environ.get('UNDERLYINGS_QUEUE_URL')
