from __future__ import annotations

import urllib.parse
from datetime import datetime
from typing import Any, List

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class ArduboyClient(ClientBase):
    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            spoof_headers=True,
            base_url="https://community.arduboy.com",
        )

    async def search(self, game: ExcelGame) -> Any:
        return await self.get(
            f"{self.base_url}/search/query?term={urllib.parse.quote(game.title + ' #games')}",
            headers={
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform != ExcelPlatform.ARDUBOY

    async def get_results(self, game: ExcelGame) -> List[Any]:
        return (await self.search(game) or {}).get("topics", [])

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        match = self.validator.validate(
            game,
            result["title"]
            .split(" - ", maxsplit=1)[0]
            .strip()
            .split(": ", maxsplit=1)[0]
            .strip(),
            [ExcelPlatform.ARDUBOY.value],
            [datetime.strptime(result["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").year],
        )

        if match.likely_match:
            return GameMatch(
                result["title"],
                f"{self.base_url}/t/{result['slug']}/{result['id']}",
                result["id"],
                result,
                match,
            )

        return None
