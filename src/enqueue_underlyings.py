from injector import inject, Injector

from src.queue import UnderlyingsQueue
from src.symbol_service import SymbolService


@inject
def enqueue_underlyings(symbol_service: SymbolService, queue: UnderlyingsQueue) -> None:
    for underlying in symbol_service.get_liquid_optionable_underlying_symbols():
        queue.enqueue(underlying)


if __name__ == '__main__':
    Injector().call_with_injection(enqueue_underlyings)
