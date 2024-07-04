from datetime import datetime, UTC
import requests
from injector import singleton
from pandas import DataFrame, Series


@singleton
class MarketData:
    @staticmethod
    def get_daily_returns(symbol: str) -> Series:
        result = requests.get(
            f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}',
            params={'interval': '1d', 'range': '5y'},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        ).json()['chart']['result'][0]
        indicators = result['indicators']
        candles = DataFrame.from_records([
            {
                'date': datetime.fromtimestamp(timestamp, UTC).strftime('%Y-%m-%d'),
                'adjusted_close': indicators['adjclose'][0]['adjclose'][i],
            }
            for i, timestamp in enumerate(result['timestamp'])
        ]).set_index(['date'])
        return candles['adjusted_close'].pct_change().dropna()
