from typing import Iterator

from injector import inject, Injector
from tqdm import tqdm

from src.queue import UnderlyingsQueue
from src.tastytrade_api import TastytradeApi


class UnderlyingsEnqueuer:
    @inject
    def __init__(self, queue: UnderlyingsQueue, api: TastytradeApi):
        self.__queue = queue
        self.__api = api

    def run(self) -> None:
        for underlying in self.__get_symbols():
            self.__queue.enqueue(underlying)

    def __get_symbols(self) -> Iterator[str]:
        page_offset = 0
        result = self.__get_symbols_page(0)
        with tqdm(total=result['pagination']['total-items']) as progress:
            while True:
                for item in result['data']['items']:
                    progress.update(1)
                    if 'option-tick-sizes' not in item or item['is-options-closing-only'] or item['is-illiquid']:
                        continue
                    yield item['symbol']
                if not result['pagination']['current-item-count']:
                    return
                page_offset += 1
                result = self.__get_symbols_page(page_offset)

    def __get_symbols_page(self, page_offset: int) -> dict:
        return self.__api.get('/instruments/equities/active',
                              {'lendability': 'Easy To Borrow', 'page-offset': page_offset})


if __name__ == '__main__':
    Injector().get(UnderlyingsEnqueuer).run()
