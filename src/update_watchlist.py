from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Dict, Any

from injector import inject, Injector, Module
from tastytrade_sdk import Tastytrade
from tastytrade_sdk.market_metrics import MarketMetric

from src.config import LambdaModule, LocalModule
from src.market_metrics_processor import MarketMetricsProcessor
from src.option_chains_processor import OptionChainsProcessor, ContractCount


@dataclass
class Joined:
    symbol: str
    iv_percentile: float
    iv_rank: float
    contract_count: int

    @staticmethod
    def join(symbol: str, market_metric: MarketMetric, contract_count: ContractCount) -> 'Joined':
        return Joined(
            symbol=symbol,
            iv_percentile=market_metric.implied_volatility_percentile,
            iv_rank=market_metric.implied_volatility_rank,
            contract_count=contract_count.count
        )


class WatchlistUpdater:
    @inject
    def __init__(self, tastytrade: Tastytrade, market_metrics_processor: MarketMetricsProcessor,
                 option_chains_processor: OptionChainsProcessor):
        self.__market_metrics_processor = market_metrics_processor
        self.__option_chains_processor = option_chains_processor
        self.__tastytrade = tastytrade

    def run(self) -> None:
        all_symbols = []
        for equity in self.__tastytrade.instruments.get_active_equities():
            all_symbols.append(equity.symbol)
            self.__market_metrics_processor.process(equity.symbol)
            self.__option_chains_processor.process(equity.symbol)

        market_metrics = self.__market_metrics_processor.get()
        contract_counts = self.__option_chains_processor.get()

        filtered = self.__filter([
            Joined.join(symbol, market_metrics[symbol], contract_counts[symbol])
            for symbol in all_symbols
            if symbol in market_metrics and symbol in contract_counts
        ])

        self.__tastytrade.watchlists.update('High IV', [x.symbol for x in filtered])

    @staticmethod
    def __filter(joined: List[Joined]) -> List[Joined]:
        filtered = [x for x in joined if x.contract_count]

        mean_contract_count = mean([x.contract_count for x in filtered])

        filtered = [x for x in filtered if x.contract_count >= mean_contract_count]

        mean_iv_percentile = mean([x.iv_percentile for x in filtered])
        stdev_iv_percentile = stdev([x.iv_percentile for x in filtered])
        iv_percentile_cutoff = min(mean_iv_percentile + (2 * stdev_iv_percentile), 90)

        mean_iv_rank = mean([x.iv_rank for x in filtered])
        stdev_iv_rank = stdev([x.iv_rank for x in filtered])
        iv_rank_cutoff = min(mean_iv_rank + (2 * stdev_iv_rank), 90)

        return [x for x in filtered if x.iv_percentile > iv_percentile_cutoff and x.iv_rank > iv_rank_cutoff]


def main(module: Module) -> None:
    Injector(module).get(WatchlistUpdater).run()


def lambda_handler(event: Dict = None, context: Any = None) -> None:
    main(LambdaModule())


if __name__ == '__main__':
    main(LocalModule())
