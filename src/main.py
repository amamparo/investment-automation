from typing import Dict, Any

from injector import inject, Injector, Module
from tastytrade_sdk import Tastytrade

from src.config import LambdaModule, LocalModule


class Main:
    @inject
    def __init__(self, tasty: Tastytrade):
        self.__tasty = tasty

    def run(self) -> None:
        self.__tasty.logout()


def main(module: Module) -> None:
    Injector(module).get(Main).run()


# pylint: disable=unused-argument
def lambda_handler(event: Dict = None, context: Any = None) -> None:
    main(LambdaModule())


if __name__ == '__main__':
    main(LocalModule())
