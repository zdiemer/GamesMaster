from __future__ import annotations

import urllib.parse
from typing import Dict, List, Optional

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelRegion
from game_match import GameMatch
from match_validator import MatchValidator


class MetacriticClient(ClientBase):
    # From Metacritic's network request query parameters
    __API_KEY = "1MOZgmNFxvmljaQR1X9KAij9Mo4xAY3u"

    __BASE_FANDOM_METACRITIC_URL = (
        "https://fandom-prod.apigee.net/v1/xapi/composer/metacritic/pages"
    )

    __BASE_METACRITIC_URL = "https://www.metacritic.com"

    __VALID_REVIEW_PLATFORMS = set(
        [
            "android",
            "dsiware",
            "game boy advance",
            "game boy color",
            "google stadia",
            "mac os",
            "n-gage",
            "n-gage 2.0",
            "new nintendo 3ds",
            "nintendo 3ds",
            "nintendo 64",
            "nintendo ds",
            "nintendo dsi",
            "nintendo gamecube",
            "nintendo switch",
            "nintendo wii",
            "nintendo wii u",
            "oculus quest",
            "ouya",
            "pc",
            "playstation",
            "playstation 2",
            "playstation 3",
            "playstation 4",
            "playstation 5",
            "playstation portable",
            "playstation vita",
            "playdate",
            "sega dreamcast",
            "sega saturn",
            "wiiware",
            "xbox",
            "xbox 360",
            "xbox one",
            "xbox series x|s",
            "ios",
        ]
    )

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(4, DatePart.SECOND))

    async def search(self, game: str, offset: int = 0, limit: int = 30) -> dict:
        return await self.get(
            f"{self.__BASE_FANDOM_METACRITIC_URL}/search/{urllib.parse.quote(str(game).replace('/', ''))}/web",
            params={
                "apiKey": self.__API_KEY,
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
            params={"filter": "all", "sort": "score", "apiKey": self.__API_KEY},
        )

    async def user_reviews(self, game_slug: str, platform_slug: str) -> dict:
        return await self.get(
            f"{self.__BASE_FANDOM_METACRITIC_URL}/games-user-reviews/{game_slug}/platform/{platform_slug}/web",
            params={"filter": "all", "sort": "date", "apiKey": self.__API_KEY},
        )

    def _sluggify(self, s: str) -> str:
        return "".join(
            filter(
                lambda _s: str.isalnum(_s) or str.isspace(_s),
                s.lower(),
            )
        ).replace(" ", "-")

    def should_skip(self, game: ExcelGame) -> bool:
        return (
            game.release_region
            not in set([ExcelRegion.NORTH_AMERICA, ExcelRegion.EUROPE])
            or game.platform.lower() not in self.__VALID_REVIEW_PLATFORMS
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        matches: List[GameMatch] = []
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
            for search_item in search_items:
                if search_item["criticScoreSummary"]["score"] == 0:
                    continue

                platform = next(
                    (
                        p["name"]
                        for p in search_item["platforms"]
                        if validator.verify_platform(game.platform, [p["name"]])
                    ),
                    None,
                )

                if platform is None:
                    continue

                match = validator.validate(
                    game,
                    search_item["title"],
                    [platform],
                    [search_item["premiereYear"]],
                )

                if match.likely_match:
                    resp = await self.critic_reviews(
                        search_item["slug"], self._sluggify(platform)
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

                    resp = await self.user_reviews(
                        search_item["slug"], self._sluggify(platform)
                    )

                    user_reviews = get_results_from_component(
                        resp, "user-score-summary"
                    )

                    u_score = user_reviews["data"]["item"]

                    p_score["url"] = f"{self.__BASE_METACRITIC_URL}{p_score['url']}"
                    u_score["url"] = f"{self.__BASE_METACRITIC_URL}{u_score['url']}"

                    metacritic_info = {
                        "critics": p_score,
                        "users": u_score,
                    }

                    matches.append(
                        GameMatch(
                            search_item["title"],
                            (
                                f"{self.__BASE_METACRITIC_URL}"
                                f"{search_item['criticScoreSummary']['url']}"
                            ),
                            search_item["id"],
                            metacritic_info,
                            match,
                        ),
                    )

        offset = 0
        page_size = 30

        resp = await self.search(game.title)

        results = get_results_from_component(resp)

        if results is None or results["data"].get("items") is None:
            return []

        await get_matches_from_search_results(results["data"]["items"])

        if any(m.is_guaranteed_match() for m in matches):
            return matches

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
