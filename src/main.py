import logging
from datetime import datetime
from math import floor
from typing import Dict, Any

from injector import inject, Injector, Module
from tastytrade_sdk import Tastytrade, Order, Leg, PositionsParams

from src.config import LambdaModule, LocalModule, Environment
from src.calculate_porfolio_weights import calculate_portfolio_weights


class Main:
    @inject
    def __init__(self, env: Environment, tasty: Tastytrade):
        self.__tasty = tasty
        self.__portfolio_symbols = env.portfolio_symbols
        self.__account_number = env.account_number

    def run(self) -> None:
        target_portfoio_weights = calculate_portfolio_weights(self.__portfolio_symbols)
        print(f'Target weights: {target_portfoio_weights}')

        self.__cancel_stock_orders()

        stock_position_quantities = {
            **{symbol: 0 for symbol in target_portfoio_weights.keys()},
            **{
                x['symbol']: float(x['quantity'])
                for x in self.__tasty.accounts.get_positions(
                    account_number=self.__account_number,
                    params=PositionsParams(instrument_type='Equity')
                )
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

        total_stock_liquidity = sum(stock_position_liquidities.values()) + \
                                float(self.__tasty.accounts.get_balances(self.__account_number)['equity-buying-power'])

        # leave a small % in cash to account for fees and slippage
        total_stock_liquidity = total_stock_liquidity * .98

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
            self.__adjust(symbol, delta, float(market_data[symbol]['bid']))

        for symbol, delta in [(symbol, delta) for symbol, delta in liquidity_deltas.items() if delta > 0]:
            self.__adjust(symbol, delta, float(market_data[symbol]['ask']))

    def __adjust(self, symbol: str, delta: float, bid_ask: float) -> None:
        quantity = floor(abs(delta / bid_ask))
        if quantity <= 0:
            return
        action = 'Sell to Close' if delta < 0 else 'Buy to Open'
        filled = self.__tasty.orders.place_order_and_wait(
            account_number=self.__account_number,
            order=Order(
                order_type='Market',
                time_in_force='Day',
                legs=[Leg(
                    instrument_type='Equity',
                    symbol=symbol,
                    action=action,
                    quantity=quantity
                )]
            ),
            timeout_seconds=10
        )
        if not filled:
            raise Exception(f'Failed to fill "{action}" market order for {quantity} shares of {symbol}')

    def __cancel_stock_orders(self) -> None:
        order_ids = [
            x['id'] for x in
            self.__tasty.api.get(
                f'/accounts/{self.__account_number}/orders',
                params={
                    'status[]': 'Received',
                    'underlying-instrument-type': 'Equity'
                }
            )['data']['items']
            if all(x['instrument-type'] == 'Equity' for x in x['legs'])
        ]
        for order_id in order_ids:
            self.__tasty.api.delete(f'/accounts/{self.__account_number}/orders/{order_id}')


def main(module: Module) -> None:
    Injector(module).get(Main).run()


# pylint: disable=unused-argument
def lambda_handler(event: Dict = None, context: Any = None) -> None:
    weekday = datetime.today().weekday()
    day = datetime.today().day
    is_first_weekday_of_month = (weekday == 0 and day in (1, 2, 3)) or (weekday in (1, 2, 3, 4) and day == 1)
    if not is_first_weekday_of_month:
        print('Not the first weekday of the month. Exiting.')
        return
    main(LambdaModule())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(LocalModule())
