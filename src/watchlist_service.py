from typing import List

from injector import inject

from src.tastytrade_api import TastytradeApi


class WatchlistService:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api

    def update(self, name: str, symbols: List[str]) -> None:
        self.__api.put(f'/watchlists/{name}', {
            'name': name,
            'watchlist-entries': [{'symbol': x} for x in symbols]
        })
