import tomllib
from dataclasses import dataclass
from typing import List

from injector import singleton, inject


@singleton
@dataclass
class Config:
    portfolio_symbols: List[str]
    min_allocation: float
    max_allocation: float
    allocation_change_threshold: float

    @inject
    def __init__(self):
        with open("config.toml", "rb") as f:
            config = tomllib.load(f)
            self.portfolio_symbols = config['portfolio_symbols']
            self.min_allocation = config['min_allocation']
            self.max_allocation = config['max_allocation']
            self.allocation_change_threshold = config['allocation_change_threshold']

