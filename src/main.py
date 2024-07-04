import logging
from math import floor
from typing import Dict, Any

from injector import inject, Injector, Module
from tastytrade_sdk import Tastytrade, Order, Leg, PositionsParams

from src.config import Config
from src.environment import Environment
from src.modules import LocalModule, LambdaModule
from src.calculate_porfolio_weights import calculate_optimal_portfolio_weights


class Main:
    @inject
    def __init__(self, env: Environment, tasty: Tastytrade, config: Config):
        self.__tasty = tasty
        self.__account_number = env.account_number
        self.__config = config

    def run(self) -> None:
        is_market_open = self.__tasty.api.get('/market-time/equities/sessions/current')['data']['state'] == 'Open'
        if not is_market_open:
            print('Market is closed')
            return

        target_portfolio_weights = calculate_optimal_portfolio_weights(self.__config.portfolio_symbols,
                                                                       self.__config.min_allocation,
                                                                       self.__config.max_allocation)
        print(f'Target weights: {target_portfolio_weights}')

        self.__cancel_orders()

        position_quantities = {
            **{symbol: 0 for symbol in target_portfolio_weights.keys()},
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
                params=[('symbols[]', x) for x in position_quantities.keys()]
            )['data']['items']
        }

        position_liquidities = {
            symbol: quantity * float(market_data[symbol]['bid'])
            for symbol, quantity in position_quantities.items()
        }

        total_liquidity = sum(position_liquidities.values()) + float(
            self.__tasty.accounts.get_balances(self.__account_number)['equity-buying-power']
        )

        target_position_liquidities = {
            symbol: total_liquidity * target_portfolio_weights.get(symbol, 0)
            for symbol, liquidity
            in position_liquidities.items()
        }

        if not self.__should_adjust(total_liquidity, position_liquidities, target_position_liquidities,
                                    self.__config.allocation_change_threshold):
            print('No adjustments needed')
            return

        liquidity_deltas = {
            symbol: target_liquidity - position_liquidities[symbol]
            for symbol, target_liquidity in target_position_liquidities.items()
        }

        for symbol, delta in [(symbol, delta) for symbol, delta in liquidity_deltas.items() if delta < 0]:
            self.__adjust(symbol, delta, float(market_data[symbol]['bid']))

        for symbol, delta in [(symbol, delta) for symbol, delta in liquidity_deltas.items() if delta > 0]:
            self.__adjust(symbol, delta, float(market_data[symbol]['ask']))

    @staticmethod
    def __should_adjust(total_liquidity: float, current_position_liquidities: Dict[str, float],
                        target_position_liquidities: Dict[str, float], allocation_change_threshold: float) -> bool:
        current_weights = {
            symbol: liquidity / total_liquidity
            for symbol, liquidity in current_position_liquidities.items()
        }
        target_weights = {
            symbol: liquidity / total_liquidity
            for symbol, liquidity in target_position_liquidities.items()
        }
        all_symbols = set(current_weights.keys()) | set(target_weights.keys())
        weight_deltas = {
            symbol: abs(target_weights.get(symbol, 0) - current_weights.get(symbol, 0))
            for symbol in all_symbols
        }
        return any(delta >= allocation_change_threshold for delta in weight_deltas.values())

    def __adjust(self, symbol: str, delta: float, bid_or_ask: float) -> None:
        quantity = floor(abs(delta / bid_or_ask))
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

    def __cancel_orders(self) -> None:
        order_ids = [
            x['id'] for x in
            self.__tasty.api.get(
                f'/accounts/{self.__account_number}/orders',
                params={'status[]': 'Received'}
            )['data']['items']
        ]
        for order_id in order_ids:
            self.__tasty.api.delete(f'/accounts/{self.__account_number}/orders/{order_id}')


def main(module: Module) -> None:
    Injector(module).get(Main).run()


# pylint: disable=unused-argument
def lambda_handler(event: Dict = None, context: Any = None) -> None:
    main(LambdaModule())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(LocalModule())
