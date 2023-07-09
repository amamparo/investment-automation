import time
from math import floor
from typing import Dict, Any, List

from injector import inject, Injector, Module
from tastytrade_sdk import Tastytrade

from src.config import LambdaModule, LocalModule, Environment
from src.calculate_porfolio_weights import calculate_portfolio_weights


class Main:
    @inject
    def __init__(self, env: Environment, tasty: Tastytrade):
        self.__env = env
        self.__tasty = tasty

    def run(self) -> None:
        target_portfoio_weights = calculate_portfolio_weights(self.__env.portfolio_symbols)
        stock_position_quantities = {
            **{symbol: 0 for symbol in target_portfoio_weights.keys()},
            **{
                x['symbol']: float(x['quantity'])
                for x in self.__tasty.api.get(f'/accounts/{self.__env.account_number}/positions')['data']['items']
                if x['instrument-type'] == 'Equity'
            }
        }

        market_data = {
            x['symbol']: x
            for x in self.__tasty.api.get(
                '/market-data',
                params=[('symbols[]', x) for x in stock_position_quantities.keys()]
            )['data']['items']
        }

        stock_position_liquidities = {
            symbol: quantity * float(market_data[symbol]['bid'])
            for symbol, quantity
            in stock_position_quantities.items()
        }

        stock_buying_power = float(self.__tasty.api.get(
            f'/accounts/{self.__env.account_number}/balances'
        )['data']['equity-buying-power'])

        total_stock_liquidity = sum(stock_position_liquidities.values()) + stock_buying_power

        target_stock_liquidities = {
            symbol: total_stock_liquidity * target_portfoio_weights.get(symbol, 0)
            for symbol, liquidity
            in stock_position_liquidities.items()
        }

        liquidity_deltas = {
            symbol: target_liquidity - stock_position_liquidities[symbol]
            for symbol, target_liquidity in target_stock_liquidities.items()
        }

        for symbol, delta in [(symbol, delta) for symbol, delta in liquidity_deltas.items() if delta < 0]:
            self.__order(symbol, abs(delta / float(market_data[symbol]['bid'])), 'Sell to Close')

        for symbol, delta in [(symbol, delta) for symbol, delta in liquidity_deltas.items() if delta > 0]:
            self.__order(symbol, abs(delta / float(market_data[symbol]['ask'])), 'Buy to Open')

    def __order(self, symbol: str, full_quantity: float, action: str) -> None:
        self.__cancel_orders(symbol)
        whole_quantity = floor(full_quantity)
        fractional_quantity = floor((full_quantity - whole_quantity) * 100) / 100.0
        for quantity in [whole_quantity, fractional_quantity]:
            if quantity <= 0:
                continue
            self.__tasty.api.post(
                f'/accounts/{self.__env.account_number}/orders',
                data={
                    'order-type': 'Market',
                    'time-in-force': 'GTC',
                    'legs': [
                        {
                            'instrument-type': 'Equity',
                            'symbol': symbol,
                            'action': action,
                            'quantity': quantity
                        }
                    ]
                }
            )
        while self.__get_working_order_ids(symbol):
            time.sleep(1)

    def __cancel_orders(self, symbol: str) -> None:
        for order_id in self.__get_working_order_ids(symbol):
            self.__tasty.api.delete(f'/accounts/{self.__env.account_number}/orders/{order_id}')

    def __get_working_order_ids(self, symbol: str) -> List[str]:
        return [
            x['id'] for x in
            self.__tasty.api.get(
                f'/accounts/{self.__env.account_number}/orders',
                params={
                    'status[]': 'Received',
                    'underlying-instrument-type': 'Equity',
                    'underlying-symbol': symbol
                }
            )['data']['items']
        ]


def main(module: Module) -> None:
    Injector(module).get(Main).run()


# pylint: disable=unused-argument
def lambda_handler(event: Dict = None, context: Any = None) -> None:
    main(LambdaModule())


if __name__ == '__main__':
    main(LocalModule())
