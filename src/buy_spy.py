from typing import Dict, Any

from injector import inject, Injector

from src.config import LocalModule, AwsModule
from src.api import TastytradeApi


class Main:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api

    def run(self):
        print(self.__api.buy('SPY', 100))


def lambda_handler(event: Dict = None, context: Any = None) -> None:
    Injector(AwsModule).get(Main).run()


if __name__ == '__main__':
    Injector(LocalModule).get(Main).run()
