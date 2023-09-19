from __future__ import annotations

import re
import urllib.parse
from typing import Dict, List, Optional, Tuple

from clients.ClientBase import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelRegion
from game_match import GameMatch
from match_validator import MatchValidator, ValidationInfo


class MetacriticGame:
    title: str
    platform: str
    score: int
    url: str
    release_year: int

    def __init__(
        self, title: str, platform: str, score: int, url: str, release_year: int
    ):
        self.title = title
        self.platform = platform
        self.score = score
        self.url = url
        self.release_year = release_year


class MetacriticClient(ClientBase):
    __BASE_FANDOM_METACRITIC_URL = (
        "https://fandom-prod.apigee.net/v1/xapi/composer/metacritic/pages"
    )
    __BASE_METACRITIC_URL = "https://www.metacritic.com"
    # From Metacritic's network request query parameters
    __api_key = "1MOZgmNFxvmljaQR1X9KAij9Mo4xAY3u"

    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config, RateLimit(30, DatePart.MINUTE))

    async def search(self, game: str, offset: int = 0, limit: int = 30) -> dict:
        return await self.get(
            f"{self.__BASE_FANDOM_METACRITIC_URL}/search/{urllib.parse.quote(game)}/web",
            params={
                "apiKey": self.__api_key,
                "offset": offset,
                "limit": limit,
                "mcoTypeId": 13,
                "componentName": "search-tabs",
                "componentDisplayName": "Search+Page+Tab+Filters",
                "componentType": "FilterConfig",
            },
        )

    async def critic_reviews(self, game_slug: str, platform_slug: str) -> dict:
        return await self.get(
            f"{self.__BASE_FANDOM_METACRITIC_URL}/games-critic-reviews/{game_slug}/platform/{platform_slug}/web",
            params={"filter": "all", "sort": "score", "apiKey": self.__api_key},
        )

    async def user_reviews(self, game_slug: str, platform_slug: str) -> dict:
        return await self.get(
            f"{self.__BASE_FANDOM_METACRITIC_URL}/games-user-reviews/{game_slug}/platform/{platform_slug}/web",
            params={"filter": "all", "sort": "date", "apiKey": self.__api_key},
        )

    def _sluggify(self, s: str) -> str:
        return "".join(
            filter(
                lambda _s: str.isalnum(_s) or str.isspace(_s),
                s.lower(),
            )
        ).replace(" ", "-")

    async def match_game(
        self, game: ExcelGame
    ) -> List[Tuple[GameMatch, ValidationInfo]]:
        if game.release_region != ExcelRegion.NORTH_AMERICA:
            return []

        matches: List[Tuple[GameMatch, ValidationInfo]] = []
        validator = MatchValidator()

        def get_results_from_component(
            res: dict, component_name: str = "search"
        ) -> Optional[dict]:
            components: List[Dict] = res.get("components")

            res_comp: Optional[dict] = next(
                (c for c in components if c["meta"]["componentName"] == component_name),
                None,
            )

            if res_comp is None or res_comp.get("data") is None:
                return None

            return res_comp

        async def get_matches_from_search_results(search_items: list):
            for r in search_items:
                platform = next(
                    (
                        p["name"]
                        for p in r["platforms"]
                        if validator.verify_platform(game.platform, [p["name"]])
                    ),
                    None,
                )

                if platform is None:
                    continue
                match = validator.validate(game, r["title"], [platform])
                if match.matched:
                    resp = await self.critic_reviews(
                        r["slug"], self._sluggify(platform)
                    )

                    critic_reviews = get_results_from_component(resp, "product")
                    p_score: dict = next(
                        (
                            p["criticScoreSummary"]
                            for p in critic_reviews["data"]["item"]["platforms"]
                            if p["name"] == platform
                        ),
                        None,
                    )

                    if p_score is None or p_score.get("score") is None:
                        continue

                    resp = await self.user_reviews(r["slug"], self._sluggify(platform))
                    user_reviews = get_results_from_component(
                        resp, "user-score-summary"
                    )
                    u_score = user_reviews["data"]["item"]

                    metacritic_info = {
                        "critics": p_score,
                        "users": u_score,
                    }

                    matches.append(
                        (
                            GameMatch(
                                r["title"],
                                f"{self.__BASE_METACRITIC_URL}{r['criticScoreSummary']['url']}",
                                r["id"],
                                metacritic_info,
                            ),
                            match,
                        )
                    )

        offset = 0
        page_size = 30

        resp = await self.search(game.title)

        results = get_results_from_component(resp)

        if results is None or results["data"].get("items") is None:
            return []

        await get_matches_from_search_results(results["data"]["items"])

        while not any(matches) and results["data"]["totalResults"] > offset + page_size:
            offset += page_size
            resp = await self.search(game.title, offset=offset)

            if (
                resp is None
                or resp.get("data") is None
                or resp["data"].get("items") is None
            ):
                break

            await get_matches_from_search_results(results["data"]["items"])

        return matches
