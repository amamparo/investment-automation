from injector import inject, Injector

from src.option_chain_service import OptionChainService
from src.queue import UnderlyingsQueue


class UnderlyingProcessor:
    @inject
    def __init__(self, option_chain_service: OptionChainService):
        self.__option_chain_service = option_chain_service

    def process(self, underlying: str) -> None:
        print(self.__option_chain_service.get_option_chains(underlying))


@inject
def process_underlyings(queue: UnderlyingsQueue, underlying_processor: UnderlyingProcessor) -> None:
    queue.process(underlying_processor.process)


if __name__ == '__main__':
    Injector().call_with_injection(process_underlyings)
