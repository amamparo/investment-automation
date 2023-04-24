from typing import Iterator

from injector import inject
from tqdm import tqdm

from src.tastytrade_api import TastytradeApi


class SymbolService:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api

    def get_liquid_optionable_underlying_symbols(self) -> Iterator[str]:
        page_offset = 0
        result = self.__get(0)
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
                result = self.__get(page_offset)

    def __get(self, page_offset: int) -> dict:
        return self.__api.get('/instruments/equities/active',
                              {'lendability': 'Easy To Borrow', 'page-offset': page_offset})
