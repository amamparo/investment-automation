import logging
from typing import Dict, Any

from injector import inject, Injector, Module

from src.config import Config
from src.m1 import M1
from src.modules import LocalModule, LambdaModule
from src.quant import Quant


class Main:
    @inject
    def __init__(self, config: Config, m1: M1, quant: Quant):
        self.__config = config
        self.__quant = quant
        self.__m1 = m1

    def run(self) -> None:
        # target_allocations = self.__quant.suggest_allocations(self.__config.portfolio_symbols,
        #                                                       self.__config.min_allocation,
        #                                                       self.__config.max_allocation)
        self.__m1.update_pie({'VNQ': 91, 'TSLA': 9})


def main(module: Module) -> None:
    Injector(module).get(Main).run()


# pylint: disable=unused-argument
def lambda_handler(event: Dict = None, context: Any = None) -> None:
    main(LambdaModule())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(LocalModule())
