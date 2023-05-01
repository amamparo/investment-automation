from dataclasses import dataclass
from typing import List, Dict

from injector import inject

from src.tastytrade_api import TastytradeApi


@dataclass
class ContractCount:
    symbol: str
    count: int


class OptionChainsProcessor:
    @inject
    def __init__(self, api: TastytradeApi):
        self.__api = api
        self.__counts: List[ContractCount] = []

    def process(self, symbol: str) -> None:
        self.__counts.append(ContractCount(
            symbol=symbol,
            count=self.__get(symbol)
        ))

    def get(self) -> Dict[str, ContractCount]:
        return {x.symbol: x for x in self.__counts}

    def __get(self, symbol: str) -> int:
        option_chains = self.__api.get(f'/option-chains/{symbol}/compact')
        if not option_chains:
            return 0
        regular = next(x for x in option_chains['data']['items'] if x['expiration-type'] == 'Regular')
        return len(regular['symbols'])
