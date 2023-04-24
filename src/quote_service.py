from dataclasses import dataclass
from typing import List, Dict

from injector import inject

from src.tastytrade_api import TastytradeApi


@dataclass
class Quote:
    bid: float
    ask: float
    mid: float


class QuoteService:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api

    def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        quotes: Dict[str, Quote] = {}
        batch_size = 100
        symbol_batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        for batch in symbol_batches:
            items = self.__api.get('/market-data?' + '&'.join(f'symbols[]={x}' for x in batch))['data']['items']
            quotes = {
                **quotes,
                **{
                    quote['symbol']: Quote(
                        bid=float(quote['bid']),
                        ask=float(quote['ask']),
                        mid=float(quote['mid'])
                    )
                    for quote in items
                }
            }
        return quotes
