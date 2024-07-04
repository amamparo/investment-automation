from dataclasses import dataclass


@dataclass
class Environment:
    login: str
    password: str
    account_number: str
