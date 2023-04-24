from injector import inject, Injector

from src.queue import UnderlyingsQueue
from src.symbol_service import SymbolService


@inject
def main(symbol_service: SymbolService, queue: UnderlyingsQueue):
    for symbol in symbol_service.get_liquid_optionable_underlying_symbols():
        queue.enqueue(symbol)


if __name__ == '__main__':
    Injector().call_with_injection(main)
