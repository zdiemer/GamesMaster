from __future__ import annotations

import aiohttp
import urllib.parse
from datetime import datetime
from enum import Enum
from typing import Dict, List

from config import Config
from excel_game import ExcelGame
from match_validator import MatchValidator


class GiantBombFormat(Enum):
    JSON = "json"
    XML = "xml"


class GiantBombClient:
    __BASE_GIANTBOMB_URL = "https://www.giantbomb.com/api"
    __headers = {}

    __api_key: str

    def __init__(self, api_key: str, user_agent: str):
        self.__api_key = api_key
        self.__headers = {"User-Agent": user_agent}

    @staticmethod
    async def create(config: Config = None) -> GiantBombClient:
        if config is None:
            config = Config.create()

        return GiantBombClient(config.giant_bomb_api_key, config.user_agent)

    async def _make_request(
        self,
        route: str = "",
        params: Dict = {},
        format: GiantBombFormat = GiantBombFormat.JSON,
        api_detail_url: str = None,
    ):
        if params.get("api_key") is None:
            params["api_key"] = self.__api_key

        if params.get("format") is None:
            params["format"] = format.value

        encoded_params = urllib.parse.urlencode(params)

        base_url = (
            api_detail_url
            if api_detail_url is not None
            else f"{self.__BASE_GIANTBOMB_URL}/{route}"
        )

        url = f"{base_url}?{encoded_params}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.__headers) as res:
                return await res.json()

    async def game(self, guid: str):
        return await self._make_request(f"game/{guid}")

    async def release(self, guid: str):
        return await self._make_request(f"release/{guid}")

    async def search(self, query: str, format: GiantBombFormat = GiantBombFormat.JSON):
        return await self._make_request(
            "search/", params={"query": query, "resources": "game"}, format=format
        )

    async def get_release_years(self, guid: str) -> List[int]:
        results = await self.game(guid)

        if results.get("number_of_total_results") != 1:
            return []

        game = results["results"]
        years = []

        if (
            game.get("original_release_date") is None
            and game.get("expected_release_year") is not None
        ):
            years.append(game["expected_release_year"])

        for rel in game.get("releases") or []:
            release = (await self._make_request(api_detail_url=rel["api_detail_url"]))[
                "results"
            ]

            date = release.get("release_date")

            if date is None and release.get("expected_release_year") is not None:
                years.append(release["expected_release_year"])
            elif date is not None:
                years.append(datetime.strptime(date, "%Y-%m-%d %H:%M:%S").year)

        return years

    async def match_game(self, game: ExcelGame):
        results = await self.search(game.title)
        matches = []
        validator = MatchValidator()

        async def get_years(guid: str):
            return await self.get_release_years(guid)

        for r in results["results"]:
            if r.get("platforms") is None:
                continue
            platforms = [p["name"] for p in r["platforms"]]
            match = validator.validate(game, r["name"], platforms)
            if match.matched:
                if MatchValidator.verify_release_year(
                    game.release_date.year, await get_years(r["guid"])
                ):
                    matches.append((r, match))
            elif r.get("aliases") is not None:
                if any(
                    match.matched
                    for match in [
                        validator.validate(game, alias, platforms)
                        for alias in r["aliases"].split("\n")
                    ]
                ):
                    if MatchValidator.verify_release_year(
                        game.release_date.year, await get_years(r["guid"])
                    ):
                        matches.append((r, match))
        return matches
