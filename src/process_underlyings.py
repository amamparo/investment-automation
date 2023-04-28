from injector import inject, Injector

from src.option_chain_service import OptionChainService
from src.queue import UnderlyingsQueue
from src.quote_service import QuoteService


class UnderlyingProcessor:
    @inject
    def __init__(self, option_chain_service: OptionChainService, quote_service: QuoteService):
        self.__option_chain_service = option_chain_service
        self.__quote_service = quote_service

    def process(self, underlying: str) -> None:
        expirations = self.__option_chain_service.get_option_chains(underlying)
        underlying_quote = self.__quote_service.get_quotes(underlying)[underlying]





@inject
def process_underlyings(queue: UnderlyingsQueue, underlying_processor: UnderlyingProcessor) -> None:
    queue.process(underlying_processor.process)


if __name__ == '__main__':
    Injector().call_with_injection(process_underlyings)
