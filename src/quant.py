from math import sqrt
from typing import Dict, List, Callable

import numpy as np
from injector import singleton, inject
from pandas import DataFrame
from scipy.optimize import minimize

from src.market_data import MarketData


@singleton
class Quant:
    @inject
    def __init__(self, market_data: MarketData):
        self.__market_data = market_data

    def suggest_allocations(self, symbols: List[str], min_allocation: float, max_allocation: float) -> Dict[str, int]:
        rows = []
        for symbol in symbols:
            daily_returns = self.__market_data.get_daily_returns(symbol)
            average_daily_return = daily_returns.mean()
            volatility = sqrt(((daily_returns - average_daily_return) ** 2).sum() / daily_returns.size)
            expected_return = (1 + average_daily_return) ** 252 - 1
            rows.append({'symbol': symbol, 'expected_return': expected_return, 'volatility': volatility})
        portfolio = DataFrame.from_records(rows).set_index(['symbol'])

        num_assets = len(portfolio)
        portfolio['weight'] = minimize(
            fun=self.__sharpe_ratio_objective(portfolio),
            x0=np.array([1. / num_assets for _ in range(num_assets)]),
            method='SLSQP',
            bounds=tuple((min_allocation, max_allocation) for _ in range(num_assets)),
            constraints=({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        ).x

        allocations = {str(index): round(row['weight'] * 100) for index, row in portfolio.iterrows()}
        total_allocation = sum(allocations.values())
        if total_allocation > 100:
            surplus = total_allocation - 100
            sorted_symbols = sorted(allocations.keys(), key=lambda x: allocations[x], reverse=False)
            for _ in range(surplus):
                allocations[sorted_symbols.pop()] -= 1
        elif total_allocation < 100:
            deficit = 100 - total_allocation
            sorted_symbols = sorted(allocations.keys(), key=lambda x: allocations[x], reverse=True)
            for _ in range(deficit):
                allocations[sorted_symbols.pop()] += 1
        return allocations

    @staticmethod
    def __sharpe_ratio_objective(portfolio: DataFrame) -> Callable[[np.ndarray], float]:
        def __objective_function(weights: np.ndarray) -> float:
            port_return = np.dot(weights, portfolio['expected_return'].values)
            port_volatility = np.sqrt(np.dot(weights ** 2, portfolio['volatility'].values ** 2))
            return - (port_return / port_volatility)

        return __objective_function
