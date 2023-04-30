from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import List

from dateutil import parser
from dateutil.tz import UTC
from injector import inject, Injector

from src.market_metrics_service import MarketMetricsService
from src.symbol_service import SymbolService
from src.tastytrade_api import TastytradeApi


@dataclass
class UnderlyingWithMetrics:
    symbol: str
    market_cap: float
    iv_percentile: float
    iv_rank: float
    n_option_contracts: int


class UnderlyingsEnqueuer:
    @inject
    def __init__(self, symbol_service: SymbolService, market_metrics_service: MarketMetricsService, api: TastytradeApi):
        self.__symbol_service = symbol_service
        self.__market_metrics_service = market_metrics_service
        self.__api = api

    def run(self) -> None:
        batch: List[str] = []
        underlyings: List[UnderlyingWithMetrics] = []
        for symbol in self.__symbol_service.get_symbols():
            batch.append(symbol)
            if len(batch) == 100:
                underlyings.extend(self.__get_underlyings_with_metrics(batch))
                batch = []
        if batch:
            underlyings.extend(self.__get_underlyings_with_metrics(batch))

        underlyings = [x for x in underlyings if x.n_option_contracts]

        mean_n_option_contracts = mean([x.n_option_contracts for x in underlyings])

        underlyings = [x for x in underlyings if x.n_option_contracts >= mean_n_option_contracts]

        mean_iv_percentile = mean([x.iv_percentile for x in underlyings])
        stdev_iv_percentile = stdev([x.iv_percentile for x in underlyings])
        iv_percentile_cutoff = min(mean_iv_percentile + (2 * stdev_iv_percentile), 90)

        mean_iv_rank = mean([x.iv_rank for x in underlyings])
        stdev_iv_rank = stdev([x.iv_rank for x in underlyings])
        iv_rank_cutoff = min(mean_iv_rank + (2 * stdev_iv_rank), 90)

        underlyings = [x for x in underlyings if x.iv_percentile > iv_percentile_cutoff and x.iv_rank > iv_rank_cutoff]

        self.__update_watchlist([x.symbol for x in underlyings])

    def __update_watchlist(self, symbols: List[str]) -> None:
        name = 'High IV'
        self.__api.put(f'/watchlists/{name}', {
            'name': name,
            'watchlist-entries': [{'symbol': x} for x in symbols]
        })

    def __get_underlyings_with_metrics(self, symbols: List[str]) -> List[UnderlyingWithMetrics]:
        return [
            UnderlyingWithMetrics(
                symbol=x['symbol'],
                market_cap=float(x['market-cap']),
                iv_percentile=float(x['implied-volatility-percentile']),
                iv_rank=float(x['implied-volatility-index-rank']),
                n_option_contracts=self.__get_n_option_contracts(x['symbol'])
            )
            for x in self.__market_metrics_service.get_market_metrics(symbols).values()
            if 'market-cap' in x and 'implied-volatility-percentile' in x and 'implied-volatility-index-rank' in x
               and 'updated-at' in x and parser.parse(x['updated-at']).replace(tzinfo=UTC) >= (
                   datetime.utcnow() - timedelta(days=3)).replace(tzinfo=UTC)
        ]

    def __get_n_option_contracts(self, symbol: str) -> int:
        option_chains = self.__api.get(f'/option-chains/{symbol}/compact')
        if not option_chains:
            return 0
        regular = next(x for x in option_chains['data']['items'] if x['expiration-type'] == 'Regular')
        return len(regular['symbols'])


if __name__ == '__main__':
    Injector().get(UnderlyingsEnqueuer).run()
