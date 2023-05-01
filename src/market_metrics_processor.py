from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import List, Dict

from dateutil import parser
from dateutil.tz import UTC
from injector import inject

from src.tastytrade_api import TastytradeApi


@dataclass
class MarketMetrics:
    symbol: str
    iv_percentile: float
    iv_rank: float


class MarketMetricsProcessor:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api
        self.__symbol_batch: List[str] = []
        self.__buffer: List[MarketMetrics] = []

    def process(self, symbol: str) -> None:
        self.__symbol_batch.append(symbol)
        if len(self.__symbol_batch) == 100:
            self.__buffer.extend(self.__get(self.__symbol_batch))
            self.__symbol_batch = []

    def get(self) -> Dict[str, MarketMetrics]:
        if self.__symbol_batch:
            self.__buffer.extend(self.__get(self.__symbol_batch))
        return {x.symbol: x for x in self.__buffer}

    def __get(self, symbols: List[str]) -> List[MarketMetrics]:
        return [
            MarketMetrics(
                symbol=x['symbol'],
                iv_percentile=float(x['implied-volatility-percentile']),
                iv_rank=float(x['implied-volatility-index-rank'])
            )
            for x in self.__api.get('/market-metrics', {'symbols': ','.join(symbols)})['data']['items']
            if 'implied-volatility-percentile' in x and 'implied-volatility-index-rank' in x
               and 'updated-at' in x and parser.parse(x['updated-at']).replace(tzinfo=UTC) >= (
                   datetime.utcnow() - timedelta(days=3)).replace(tzinfo=UTC)
        ]
