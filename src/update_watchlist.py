from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import List, Optional, Dict

from dateutil import parser
from dateutil.tz import UTC
from injector import inject, Injector

from src.market_metrics_service import MarketMetricsService
from src.symbol_service import SymbolService
from src.tastytrade_api import TastytradeApi


@dataclass
class MarketMetrics:
    iv_percentile: Optional[float] = None
    iv_rank: Optional[float] = None
    n_option_contracts: Optional[int] = None

    def merge(self, other: 'MarketMetrics') -> None:
        if other.iv_percentile is not None:
            self.iv_percentile = other.iv_percentile
        if other.iv_rank is not None:
            self.iv_rank = other.iv_rank
        if other.n_option_contracts is not None:
            self.n_option_contracts = other.n_option_contracts


class WatchlistUpdater:
    @inject
    def __init__(self, symbol_service: SymbolService, market_metrics_service: MarketMetricsService, api: TastytradeApi):
        self.__symbol_service = symbol_service
        self.__market_metrics_service = market_metrics_service
        self.__api = api

    def run(self) -> None:
        batch: List[str] = []
        underlyings: Dict[str, MarketMetrics] = {}
        for symbol in self.__symbol_service.get_symbols():
            n_option_contracts = self.__get_n_option_contracts(symbol)
            if not n_option_contracts:
                continue
            underlyings[symbol] = MarketMetrics(n_option_contracts=n_option_contracts)
            batch.append(symbol)
            if len(batch) == 100:
                for key, metrics in self.__get_market_metrics(batch).items():
                    underlyings[key].merge(metrics)
                batch = []
        if batch:
            for key, metrics in self.__get_market_metrics(batch).items():
                underlyings[key].merge(metrics)

        mean_n_option_contracts = mean([x.n_option_contracts for x in underlyings.values()])

        underlyings = {x: y for x, y in underlyings.items() if y.n_option_contracts >= mean_n_option_contracts}

        mean_iv_percentile = mean([x.iv_percentile for x in underlyings.values()])
        stdev_iv_percentile = stdev([x.iv_percentile for x in underlyings.values()])
        iv_percentile_cutoff = min(mean_iv_percentile + (2 * stdev_iv_percentile), 90)

        mean_iv_rank = mean([x.iv_rank for x in underlyings.values()])
        stdev_iv_rank = stdev([x.iv_rank for x in underlyings.values()])
        iv_rank_cutoff = min(mean_iv_rank + (2 * stdev_iv_rank), 90)

        self.__update_watchlist(
            [x for x, y in underlyings.items() if y.iv_percentile > iv_percentile_cutoff and y.iv_rank > iv_rank_cutoff]
        )

    def __update_watchlist(self, symbols: List[str]) -> None:
        name = 'High IV'
        self.__api.put(f'/watchlists/{name}', {
            'name': name,
            'watchlist-entries': [{'symbol': x} for x in symbols]
        })

    def __get_market_metrics(self, symbols: List[str]) -> Dict[str, MarketMetrics]:
        return {
            key: MarketMetrics(
                iv_percentile=float(value['implied-volatility-percentile']),
                iv_rank=float(value['implied-volatility-index-rank'])
            )
            for key, value in self.__market_metrics_service.get_market_metrics(symbols).items()
            if 'implied-volatility-percentile' in value and 'implied-volatility-index-rank' in value
               and 'updated-at' in value and parser.parse(value['updated-at']).replace(tzinfo=UTC) >= (
                   datetime.utcnow() - timedelta(days=3)).replace(tzinfo=UTC)
        }

    def __get_n_option_contracts(self, symbol: str) -> int:
        option_chains = self.__api.get(f'/option-chains/{symbol}/compact')
        if not option_chains:
            return 0
        regular = next(x for x in option_chains['data']['items'] if x['expiration-type'] == 'Regular')
        return len(regular['symbols'])


if __name__ == '__main__':
    Injector().get(WatchlistUpdater).run()
