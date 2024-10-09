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
        params: Dict[str, Any] = None,
        api_detail_url: str = None,
    ) -> Any:
        params = params or {}

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

    async def concept(self, guid: str) -> Any:
        return await self._make_request(f"concept/{guid}")

    async def location(self, guid: str) -> Any:
        return await self._make_request(f"location/{guid}")

    async def releases(self, game_id: int) -> Any:
        return await self._make_request(
            "releases", params={"filter": f"game:{game_id}"}
        )

    async def search(self, query: str) -> Any:
        return await self._make_request(
            "search/", params={"query": query, "resources": "game"}
        )

    async def get_release_years(self, game_id: int, platform: str) -> List[int]:
        years = []

        releases = await self.releases(game_id)

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

    async def get_results(self, game: ExcelGame) -> List[Any]:
        response = await self.search(game.title)
        return response["results"]

    async def result_to_match(self, game: ExcelGame, result: Any) -> GameMatch | None:
        if result.get("platforms") is None:
            return None

        platforms = [p["name"] for p in result["platforms"]]
        years = []

        if (
            result.get("original_release_date") is None
            and result.get("expected_release_year") is not None
        ):
            years.append(result["expected_release_year"])

        if result.get("original_release_date") is not None:
            years.append(
                datetime.strptime(result["original_release_date"], "%Y-%m-%d").year
            )

        match = self.validator.validate(game, result["name"], platforms, years)

        if match.likely_match:
            if not match.date_matched:
                match.date_matched = self.validator.verify_release_year(
                    game.release_year,
                    await self.get_release_years(result["id"], game.platform.value),
                )

            game_info = await self.game(result["guid"])
            developers = []
            publishers = []
            franchises = []

            if game_info.get("results"):
                if any(game_info["results"].get("developers") or []):
                    developers.extend(
                        d["name"] for d in game_info["results"]["developers"]
                    )
                if any(game_info["results"].get("publishers") or []):
                    publishers.extend(
                        p["name"] for p in game_info["results"]["publishers"]
                    )
                if any(game_info["results"].get("franchises") or []):
                    franchises.extend(
                        f["name"] for f in game_info["results"]["franchises"]
                    )

            match.developer_matched = self.validator.verify_component(
                game.developer, developers
            )

            match.publisher_matched = self.validator.verify_component(
                game.publisher, publishers
            )

            match.franchise_matched = self.validator.verify_franchise(
                game.franchise, franchises
            )

            return GameMatch(
                result["name"], result["site_detail_url"], result["guid"], result, match
            )
        elif result.get("aliases") is not None:
            for alias in result["aliases"].split("\n"):
                match = self.validator.validate(game, alias, platforms, years)

                if match.likely_match:
                    if not match.date_matched:
                        match.date_matched = self.validator.verify_release_year(
                            game.release_year,
                            await self.get_release_years(
                                result["id"], game.platform.value
                            ),
                        )

                    return GameMatch(
                        result["name"],
                        result["site_detail_url"],
                        result["guid"],
                        result,
                        match,
                    )

        return None
