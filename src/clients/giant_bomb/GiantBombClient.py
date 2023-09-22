import urllib.parse
from datetime import datetime
from typing import Any, Dict, List

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator


class GiantBombClient(ClientBase):
    __BASE_GIANTBOMB_URL = "https://www.giantbomb.com/api"

    __api_key: str

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            RateLimit(
                200,
                DatePart.HOUR,
                rate_limit_per_route=True,
                get_route_path=lambda s: urllib.parse.urlparse(s).path.split("/")[2],
            ),
        )
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

    async def releases(self, game_id: int):
        return await self._make_request(
            "releases", params={"filter": f"game:{game_id}"}
        )

    async def search(self, query: str) -> Any:
        return await self._make_request(
            "search/", params={"query": query, "resources": "game"}
        )

    async def get_release_years(self, guid: str, platform: str) -> List[int]:
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

        if game.get("original_release_date") is not None:
            years.append(
                datetime.strptime(game["original_release_date"], "%Y-%m-%d").year
            )

        releases = await self.releases(game["id"])

        for release in releases.get("results") or []:
            release_platform = (release.get("platform") or {}).get("name")

            if release_platform is None or not self.validator.verify_platform(
                platform, [release_platform]
            ):
                continue

            date = release.get("release_date")

            if date is None and release.get("expected_release_year") is not None:
                years.append(release["expected_release_year"])
            elif date is not None:
                years.append(datetime.strptime(date, "%Y-%m-%d %H:%M:%S").year)

        return years

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        results = await self.search(game.title)
        matches: List[GameMatch] = []

        for res in results["results"]:
            if res.get("platforms") is None:
                continue

            platforms = [p["name"] for p in res["platforms"]]
            match = self.validator.validate(game, res["name"], platforms)

            if match.likely_match:
                match.date_matched = self.validator.verify_release_year(
                    game.release_year,
                    await self.get_release_years(res["guid"], game.platform),
                )

                matches.append(
                    GameMatch(
                        res["name"], res["site_detail_url"], res["guid"], res, match
                    ),
                )
            elif res.get("aliases") is not None:
                if any(
                    match.likely_match
                    for match in [
                        self.validator.validate(game, alias, platforms)
                        for alias in res["aliases"].split("\n")
                    ]
                ):
                    match.date_matched = self.validator.verify_release_year(
                        game.release_year,
                        await self.get_release_years(res["guid"], game.platform),
                    )

                    matches.append(
                        GameMatch(
                            res["name"],
                            res["site_detail_url"],
                            res["guid"],
                            res,
                            match,
                        ),
                    )
        return matches
