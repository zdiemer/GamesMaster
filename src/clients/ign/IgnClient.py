from __future__ import annotations

import aiohttp.client_exceptions
import urllib.parse
from datetime import datetime
from typing import Any, List

from clients import ClientBase
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator


class IgnClient(ClientBase):
    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            spoof_headers=True,
            base_url="https://mollusk.apis.ign.com",
            immediately_stop_statuses=[403, 401, 429],
        )

    async def search(self, title: str) -> Any:
        l = "{"
        r = "}"
        processed_title = urllib.parse.quote(title.replace('"', ""))

        return await self.get(
            f'{self.base_url}/graphql?operationName=SearchObjectsByName&variables={l}"term":"{processed_title}","count": 20,"objectType":"Game"{r}&extensions={l}"persistedQuery":{l}"version":1,"sha256Hash":"e1c2e012a21b4a98aaa618ef1b43eb0cafe9136303274a34f5d9ea4f2446e884"{r}{r}',
            headers={"Content-Type": "application/json"},
            retry_errors=[
                aiohttp.client_exceptions.ClientOSError,
                aiohttp.client_exceptions.ClientConnectionError,
                aiohttp.client_exceptions.ClientPayloadError,
                aiohttp.client_exceptions.ClientConnectorError,
                aiohttp.client_exceptions.ServerDisconnectedError,
            ],
        )

    async def get_results(self, game: ExcelGame) -> List[Any]:
        results = await self.search(game.title)
        return (
            (results or {})
            .get("data", {})
            .get("searchObjectsByName", {})
            .get("objects", [])
        )

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        names = result.get("metadata", {}).get("names", {})

        titles = [
            result["slug"],
            names.get("name"),
            names.get("short"),
            *names.get("alt", []),
        ]

        release_years = []
        platforms = []

        for region in result.get("objectRegions", []):
            for release in region.get("releases", []):
                if release["date"] is not None:
                    release_year = datetime.strptime(release["date"], "%Y-%m-%d").year
                    release_years.append(release_year)

                platforms.extend(
                    p.get("name") for p in release.get("platformAttributes", [])
                )

        match = self.validator.validate(game, titles, platforms, release_years)

        if match.likely_match:
            return GameMatch(
                titles[1] if len(titles) > 1 else titles[0],
                f"https://www.ign.com{result['url']}",
                result["id"],
                result,
                match,
            )

        return None
