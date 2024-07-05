from dataclasses import dataclass


@dataclass
class Environment:
    m1_login: str
    m1_password: str
    m1_pie_id: str
    workmail_email_address: str
    workmail_password: str
