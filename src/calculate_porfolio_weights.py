from datetime import datetime
from math import sqrt
from typing import Dict, List

import numpy as np
import requests
from pandas import DataFrame, Series
from scipy.optimize import minimize


def calculate_portfolio_weights(symbols: List[str]) -> Dict[str, float]:
    rows = []
    for symbol in symbols:
        daily_returns = _get_daily_returns(symbol)
        average_daily_return = daily_returns.mean()
        volatility = sqrt(((daily_returns - average_daily_return) ** 2).sum() / daily_returns.size)
        expected_return = (1 + average_daily_return) ** 252 - 1
        rows.append({'symbol': symbol, 'expected_return': expected_return, 'volatility': volatility})
    portfolio = DataFrame.from_records(rows).set_index(['symbol'])

    def sharpe_ratio_objective(weights):
        port_return = np.dot(weights, portfolio['expected_return'].values)
        port_volatility = np.sqrt(np.dot(weights ** 2, portfolio['volatility'].values ** 2))
        return - (port_return / port_volatility)

    num_assets = len(portfolio)
    portfolio['weight'] = minimize(
        fun=sharpe_ratio_objective,
        x0=num_assets * [1. / num_assets],
        method='SLSQP',
        bounds=tuple((0, 1) for _ in range(num_assets)),
        constraints=({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    ).x
    return {index: row['weight'] for index, row in portfolio.iterrows()}


def _get_daily_returns(symbol: str) -> Series:
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
            'open': indicators['quote'][0]['open'][i],
            'high': indicators['quote'][0]['high'][i],
            'low': indicators['quote'][0]['low'][i],
            'close': indicators['quote'][0]['close'][i],
            'adjusted_close': indicators['adjclose'][0]['adjclose'][i],
            'volume': indicators['quote'][0]['volume'][i]
        }
        for i, timestamp in enumerate(result['timestamp'])
    ]).set_index(['date'])
    return candles['adjusted_close'].pct_change().dropna()
