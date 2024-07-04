import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, UTC

import requests
from injector import singleton, inject
from playwright.async_api import async_playwright

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
        self.__access_token = asyncio.run(M1.__get_access_token(env.m1_login, env.m1_password))

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

    def __update_pie(self, allocations: list[Allocation]) -> None:
        pass

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

    def __graphql(self, operation_name: str, variables: dict, query: str) -> dict:
        return requests.post(
            'https://lens.m1.com/graphql',
            headers={'Authorization': f'Bearer {self.__access_token}'},
            json={
                "operationName": operation_name,
                "variables": variables,
                "query": query
            }
        ).json()['data']

    @staticmethod
    async def __get_access_token(login: str, password: str) -> str:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True, devtools=False, chromium_sandbox=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--no-zygote',
                '--window-size=1920,1080',
            ]
        )
        page = await browser.new_page()
        await page.goto('https://dashboard.m1.com/login')
        await page.fill('input[name="username"]', login)
        await page.fill('input[name="password"]', password)
        async with page.expect_navigation():
            await page.click('button[type="submit"]')
        token = await page.evaluate('JSON.parse(sessionStorage.getItem("m1_finance_auth.accessToken"));')
        await page.close()
        return token
