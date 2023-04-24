from dataclasses import dataclass
from typing import List

from injector import inject

from src.quote_service import QuoteService, Quote
from src.tastytrade_api import TastytradeApi


@dataclass
class Contract:
    symbol: str
    quote: Quote


@dataclass
class Strike:
    price: float
    call: Contract
    put: Contract


@dataclass
class OptionChain:
    expiration: str
    settlement_type: str
    days_to_expiration: int
    strikes: List[Strike]


@dataclass
class OptionChainsResponse:
    underlying: str
    quote: Quote
    option_chains: List[OptionChain]


class OptionChainService:
    @inject
    def __init__(self, api: TastytradeApi, quote_service: QuoteService):
        self.__api = api
        self.__quote_service = quote_service

    def get_option_chains(self, underlying: str) -> OptionChainsResponse:
        raw_nested_chains = self.__api.get(f'/option-chains/{underlying}/nested')['data']['items'][0]
        quote_symbols = [raw_nested_chains['underlying-symbol']]
        raw_expirations = [x for x in raw_nested_chains['expirations'] if x['expiration-type'] == 'Regular']
        for expiration in raw_expirations:
            for strike in expiration['strikes']:
                quote_symbols.extend([strike['call'], strike['put']])
        quotes = self.__quote_service.get_quotes(quote_symbols)

        return OptionChainsResponse(
            underlying=underlying,
            quote=quotes[underlying],
            option_chains=[
                OptionChain(
                    expiration=x['expiration-date'],
                    settlement_type=x['settlement-type'],
                    days_to_expiration=x['days-to-expiration'],
                    strikes=[
                        Strike(
                            price=float(s['strike-price']),
                            call=Contract(
                                symbol=s['call'],
                                quote=quotes[s['call']]
                            ),
                            put=Contract(
                                symbol=s['put'],
                                quote=quotes[s['put']]
                            )
                        )
                        for s in x['strikes']
                    ]
                )
                for x in raw_expirations
            ]
        )
