from types import MappingProxyType
from typing import Optional, Any, Dict

import requests
from injector import singleton, inject

from src.env import Environment


@singleton
class TastytradeApi:
    @inject
    def __init__(self, env: Environment):
        self.__base_url = env.api_base_url
        self.__token = self.__login(env.login, env.password)

    def get(self, path: str, params: Optional[Dict[str, Any]] = MappingProxyType({})) -> dict:
        return requests.get(
            f'{self.__base_url}{path}',
            params=params,
            headers={'Authorization': self.__token, 'content-type': 'application/json'}
        ).json()

    def __login(self, login: str, password: str) -> str:
        return requests.post(f'{self.__base_url}/sessions', data={
            'login': login,
            'password': password
        }).json()['data']['session-token']