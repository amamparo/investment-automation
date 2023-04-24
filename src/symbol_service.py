from typing import Iterator

from injector import inject

from src.tastytrade_api import TastytradeApi


class SymbolService:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api

    def get_liquid_optionable_underlying_symbols(self) -> Iterator[str]:
        page_offset = 0
        while True:
            result = self.__api.get('/instruments/equities/active', {'page-offset': page_offset})
            for item in result['data']['items']:
                if 'option-tick-sizes' not in item or item['is-options-closing-only'] or item['is-illiquid']:
                    pass
                yield item['symbol']
            if not result['pagination']['current-item-count']:
                return
            page_offset += 1
