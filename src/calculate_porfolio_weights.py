from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from math import sqrt
from typing import Dict, List, Callable

import numpy as np
import requests
from pandas import DataFrame, Series
from scipy.optimize import minimize


def calculate_optimal_portfolio_weights(symbols: List[str], min_allocation: float,
                                        max_allocation: float) -> Dict[str, float]:
    rows = []
    for symbol in symbols:
        daily_returns = __get_daily_returns(symbol)
        average_daily_return = daily_returns.mean()
        volatility = sqrt(((daily_returns - average_daily_return) ** 2).sum() / daily_returns.size)
        expected_return = (1 + average_daily_return) ** 252 - 1
        rows.append({'symbol': symbol, 'expected_return': expected_return, 'volatility': volatility})
    portfolio = DataFrame.from_records(rows).set_index(['symbol'])

    num_assets = len(portfolio)
    portfolio['weight'] = minimize(
        fun=__sharpe_ratio_objective(portfolio),
        x0=np.array([1. / num_assets for _ in range(num_assets)]),
        method='SLSQP',
        bounds=tuple((min_allocation, max_allocation) for _ in range(num_assets)),
        constraints=({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    ).x
    return {str(index): __truncate(float(row['weight'])) for index, row in portfolio.iterrows()}


def __truncate(value: float):
    return float(Decimal(str(value)).quantize(Decimal('0.00'), rounding=ROUND_DOWN))


def __sharpe_ratio_objective(portfolio: DataFrame) -> Callable[[np.ndarray], float]:
    def __objective_function(weights: np.ndarray) -> float:
        port_return = np.dot(weights, portfolio['expected_return'].values)
        port_volatility = np.sqrt(np.dot(weights ** 2, portfolio['volatility'].values ** 2))
        return - (port_return / port_volatility)

    return __objective_function


def __get_daily_returns(symbol: str) -> Series:
    result = requests.get(
        f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}',
        params={'interval': '1d', 'range': '5y'},
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=5
    ).json()['chart']['result'][0]
    indicators = result['indicators']
    candles = DataFrame.from_records([
        {
            'date': datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d'),
            'adjusted_close': indicators['adjclose'][0]['adjclose'][i],
        }
        for i, timestamp in enumerate(result['timestamp'])
    ]).set_index(['date'])
    return candles['adjusted_close'].pct_change().dropna()
