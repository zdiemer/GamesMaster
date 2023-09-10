from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from clients.ClientBase import ClientBase
from config import Config
from excel_game import ExcelGame
from match_validator import MatchValidator, ValidationInfo


class GiantBombClient(ClientBase):
    __BASE_GIANTBOMB_URL = "https://www.giantbomb.com/api"

    __api_key: str

    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config)
        self.__api_key = self._config.giant_bomb_api_key

    async def _make_request(
        self,
        route: str = "",
        params: Dict[str, Any] = {},
        api_detail_url: str = None,
    ) -> Any:
        if params.get("api_key") is None:
            params["api_key"] = self.__api_key

        if params.get("format") is None:
            params["format"] = "json"

        base_url = (
            api_detail_url
            if api_detail_url is not None
            else f"{self.__BASE_GIANTBOMB_URL}/{route}"
        )

        return await self.get(base_url, params=params)

    async def game(self, guid: str) -> Any:
        return await self._make_request(f"game/{guid}")

    async def release(self, guid: str) -> Any:
        return await self._make_request(f"release/{guid}")

    async def search(self, query: str) -> Any:
        return await self._make_request(
            "search/", params={"query": query, "resources": "game"}
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

    async def match_game(self, game: ExcelGame) -> List[Tuple[Any, ValidationInfo]]:
        results = await self.search(game.title)
        matches: List[Tuple[Any, ValidationInfo]] = []
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
