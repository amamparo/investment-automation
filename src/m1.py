import imaplib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, UTC
from email import policy
from email.parser import BytesParser

import requests
from injector import singleton, inject

from src.environment import Environment


@dataclass
class Allocation:
    security_id: str
    target_percentage: int


@singleton
class M1:
    @inject
    def __init__(self, env: Environment):
        self.__pie_id = env.m1_pie_id
        self.__access_token = self.__get_access_token(env)

    def update_pie(self, target_allocations: dict[str, int]) -> None:
        allocations = [
            Allocation(self.__lookup_symbol_id(symbol), percentage)
            for symbol, percentage
            in target_allocations.items()
        ]
        update_result = self.__graphql(
            "UpdatePieTree",
            {
                "input": {
                    "serializedTree": json.dumps({
                        "id": self.__pie_id,
                        "description": f"Updated at {datetime.now(UTC).isoformat()}",
                        "name": "Automated",
                        "type": "old_pie",
                        "slices": [
                            {
                                "percentage": x.target_percentage,
                                "to": {
                                    "id": x.security_id,
                                    "type": "security"
                                }
                            } for x in allocations
                        ]
                    }),
                }
            },
            """
                mutation UpdatePieTree($input: UpdatePieTreeInput!) {
                  updatePieTree(input: $input) {
                    result {
                      didSucceed
                      inputError
                    }
                  }
                }
            """
        )['updatePieTree']['result']
        if not update_result['didSucceed']:
            raise Exception(f"Failed to update pie: {update_result['inputError']}")

    def __lookup_symbol_id(self, symbol: str) -> str:
        return self.__graphql(
            "DiscoverSearch",
            {"query": symbol},
            """
                query DiscoverSearch($query: String!) {
                    viewer { search: searchSliceables(first: 1, query: $query) { edges { node { id } } } }
                }
            """
        )['viewer']['search']['edges'][0]['node']['id']

    def __graphql(self, operation_name: str, variables: dict, query: str, authenticated: bool = True) -> dict:
        return requests.post(
            'https://lens.m1.com/graphql',
            headers={'Authorization': f'Bearer {self.__access_token}'} if authenticated else {},
            json={
                "operationName": operation_name,
                "variables": variables,
                "query": query
            }
        ).json()['data']

    def __get_access_token(self, env: Environment) -> str:
        auth_response = self.__auth_request(env.m1_login, env.m1_password)
        auth_result = auth_response['result']
        if not auth_result['didSucceed'] and 'mfa' in auth_result['inputError'].lower():
            print('MFA required, fetching')
            time.sleep(5)
            mfa_code = self.__get_mfa_code(env.workmail_email_address, env.workmail_password)
            auth_response = self.__auth_request(env.m1_login, env.m1_password, mfa_code)
        access_token = auth_response['accessToken']
        if not access_token:
            raise Exception('Failed to get M1 access token')
        return access_token

    def __auth_request(self, m1_login: str, m1_password: str, mfa_code: str = None) -> dict:
        input = {
            'username': m1_login,
            'password': m1_password
        }
        if mfa_code:
            input['emailCode'] = mfa_code
        return self.__graphql(
            'Authenticate',
            {
                'input': input
            },
            """
            mutation Authenticate($input: AuthenticateInput!) {
                authenticate(input: $input) {
                    result {
                      didSucceed
                      inputError
                    }
                    accessToken
                  }
                }
            """,
            False
        )['authenticate']

    @staticmethod
    def __get_mfa_code(email_address, email_password) -> str:
        mail = imaplib.IMAP4_SSL('imap.mail.us-east-1.awsapps.com')
        mail.login(email_address, email_password)
        mail.select('inbox')
        result, data = mail.search(None, 'ALL')
        email_ids = data[0].split()
        result, data = mail.fetch(email_ids[-1], '(RFC822)')
        msg = BytesParser(policy=policy.default).parsebytes(data[0][1])
        body = msg.get_body(preferencelist=('plain')).get_content()
        return re.search(r'\b\d{6}\b', body).group(0)
