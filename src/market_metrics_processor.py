from datetime import timedelta, datetime
from typing import List, Dict

from dateutil.tz import UTC
from injector import inject
from tastytrade_sdk import Tastytrade
from tastytrade_sdk.market_metrics import MarketMetric


class MarketMetricsProcessor:
    @inject
    def __init__(self, tastytrade: Tastytrade):
        self.__tastytrade = tastytrade
        self.__symbol_batch: List[str] = []
        self.__buffer: List[MarketMetric] = []

    def process(self, symbol: str) -> None:
        self.__symbol_batch.append(symbol)
        if len(self.__symbol_batch) == 100:
            self.__buffer.extend(self.__get(self.__symbol_batch))
            self.__symbol_batch = []

    def get(self) -> Dict[str, MarketMetric]:
        if self.__symbol_batch:
            self.__buffer.extend(self.__get(self.__symbol_batch))
        return {x.symbol: x for x in self.__buffer}

    def __get(self, symbols: List[str]) -> List[MarketMetric]:
        return [
            x for x in self.__tastytrade.market_metrics.get_market_metrics(symbols)
            if
            x.implied_volatility_percentile is not None and x.implied_volatility_rank is not None and x.updated_at and
            x.updated_at >= (datetime.utcnow() - timedelta(days=3)).replace(tzinfo=UTC)
        ]
