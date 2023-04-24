from injector import inject, Injector

from src.option_chain_service import OptionChainService
from src.queue import UnderlyingsQueue


class ProcessUnderlyings:
    @inject
    def __init__(self, queue: UnderlyingsQueue, option_chain_service: OptionChainService):
        self.__queue = queue
        self.__option_chain_service = option_chain_service

    def run(self) -> None:
        self.__queue.process(self.__process)

    def __process(self, underlying: str) -> None:
        print(self.__option_chain_service.get_option_chains(underlying))


if __name__ == '__main__':
    Injector().get(ProcessUnderlyings).run()
