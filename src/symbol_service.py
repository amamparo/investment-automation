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
            symbols = [
                x['symbol'] for x in result['data']['items']
                if 'option-tick-sizes' in x and not x['is-options-closing-only'] and not x['is-illiquid']
            ]
            for symbol in symbols:
                yield symbol
            pagination = result['pagination']
            if not pagination['current-item-count']:
                return
            page_offset += 1
