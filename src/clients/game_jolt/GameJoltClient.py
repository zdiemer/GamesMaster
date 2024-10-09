from __future__ import annotations

import datetime
from typing import Any, Dict, List

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class GameJoltClient(ClientBase):
    __BASE_GAME_JOLT_URL = "https://gamejolt.com/site-api/web"

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator, config, RateLimit(600, DatePart.HOUR), spoof_headers=True
        )

    def search(self, query: str) -> Dict[str, Any]:
        return self.get(
            f"{self.__BASE_GAME_JOLT_URL}/search",
            params={"q": query, "post-feed-use-offset": 1},
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform != ExcelPlatform.PC or game.notes in (
            "Steam",
            "Epic Games Store",
            "GOG",
            "uPlay",
            "Twitch",
            "Amazon",
            "Battle.net",
        )

    async def get_results(self, game: ExcelGame) -> List[Any]:
        results = await self.search(game.title)
        return (results.get("payload") or {}).get("games") or []

    async def result_to_match(self, game: ExcelGame, result: Any) -> GameMatch | None:
        developer = (result.get("developer") or {}).get("display_name") or None

        match = self.validator.validate(
            game,
            result["title"],
            [game.platform.value],
            [datetime.datetime.fromtimestamp(int(result["posted_on"]) / 1000.0)],
            [developer] if developer else None,
        )

        if match.likely_match:
            return GameMatch(
                result["title"],
                f"https://gamejolt.com/games/{result['slug']}/{result['id']}",
                result["id"],
                result,
                match,
            )

        return None
