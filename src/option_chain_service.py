from dataclasses import dataclass
from typing import List, Dict

from injector import inject

from src.quote_service import QuoteService
from src.tastytrade_api import TastytradeApi


@dataclass
class Contract:
    symbol: str
    type: str
    strike: float


@dataclass
class Expiration:
    expiration: str
    days_to_expiration: int
    type: str
    contracts: List[Contract]


class OptionChainService:
    @inject
    def __init__(self, api: TastytradeApi, quote_service: QuoteService):
        self.__api = api
        self.__quote_service = quote_service

    def get_option_chains(self, underlying: str) -> List[Expiration]:
        expirations: Dict[str, Expiration] = {}
        for x in self.__api.get(f'/option-chains/{underlying}')['data']['items']:
            expiration_date = x['expiration-date']
            expiration = expirations.get(
                expiration_date,
                Expiration(
                    expiration=expiration_date,
                    days_to_expiration=x['days-to-expiration'],
                    type=x['expiration-type'],
                    contracts=[]
                )
            )
            expiration.contracts.append(Contract(
                symbol=x['symbol'],
                type=x['option-type'],
                strike=float(x['strike-price'])
            ))
            expirations[expiration_date] = expiration
        return list(expirations.values())
