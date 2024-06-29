from __future__ import annotations

import datetime
from typing import Any, Dict, List

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
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
        return game.platform != "PC" or game.notes in (
            "Steam",
            "Epic Games Store",
            "GOG",
            "uPlay",
            "Twitch",
            "Amazon",
            "Battle.net",
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        matches: List[GameMatch] = []

        results = await self.search(game.title)

        games = (results.get("payload") or {}).get("games") or []

        for g in games:
            if any(m.is_guaranteed_match() for m in matches):
                break

            developer = (g.get("developer") or {}).get("display_name") or None

            match = self.validator.validate(
                game,
                g["title"],
                [game.platform],
                [datetime.datetime.fromtimestamp(int(g["posted_on"]) / 1000.0)],
                [developer] if developer else None,
            )

            if match.likely_match:
                matches.append(
                    GameMatch(
                        g["title"],
                        f"https://gamejolt.com/games/{g['slug']}/{g['id']}",
                        g["id"],
                        g,
                        match,
                    )
                )

        return matches
