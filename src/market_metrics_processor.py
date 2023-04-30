from functools import reduce
from typing import Dict, List

from injector import inject

from src.tastytrade_api import TastytradeApi


class MarketMetricsProcessor:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api

    def get_market_metrics(self, symbols: List[str]) -> Dict[str, dict]:
        items = self.__api.get('/market-metrics', {'symbols': ','.join(symbols)})['data']['items']
        return reduce(lambda agg, item: {**agg, **{item['symbol']: item}}, items, {})
