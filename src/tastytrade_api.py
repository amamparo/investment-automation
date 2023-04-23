import json

import requests
from injector import singleton, inject

from src.env import Environment


@singleton
class TastytradeApi:

    @inject
    def __init__(self, env: Environment):
        self.__env = env
        self.__token = self.__login()

    def buy(self, symbol: str, usd_amount: float) -> dict:
        return requests.post(
            f'{self.__env.api_base_url}/accounts/{self.__env.account}/orders',
            headers={'Authorization': self.__token, 'content-type': 'application/json'},
            data=json.dumps({
                'time-in-force': 'IOC',
                'order-type': 'Notional Market',
                'value': usd_amount,
                'value-effect': 'Debit',
                'legs': [
                    {
                        'instrument-type': 'Equity',
                        'symbol': symbol,
                        'action': 'Buy'
                    }
                ]
            })
        ).json()

    def __login(self) -> str:
        return requests.post(f'{self.__env.api_base_url}/sessions', data={
            'login': self.__env.login,
            'password': self.__env.password
        }).json()['data']['session-token']
