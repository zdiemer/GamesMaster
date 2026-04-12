from typing import Any, List

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class FlashpointClient(ClientBase):
    FLASHPOINT_DATABASE_URL = (
        "https://flashpointproject.github.io/flashpoint-database/search/"
    )

    def __init__(self, validator: MatchValidator = None, config: Config = None):
        validator = validator or MatchValidator()
        config = config or Config.create()
        super().__init__(validator, config, base_url="https://db-api.unstable.life")

    async def search(self, title: str) -> List[Any]:
        return await self.get(
            f"{self.base_url}/search",
            params={
                "smartSearch": title,
                "filter": "true",
                "fields": "*",
            },
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform != ExcelPlatform.BROWSER

    async def get_results(self, game: ExcelGame) -> List[Any]:
        return await self.search(game.title)

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch | None:
        try:
            year = int(result["releaseDate"][:4])
        except ValueError:
            year = None

        match = self.validator.validate(
            game,
            result["title"],
            [game.platform.value],
            [year],
            [result["publisher"]],
            [result["developer"]],
        )

        if match.likely_match:
            return GameMatch(
                result["title"],
                f"{self.FLASHPOINT_DATABASE_URL}#{result['id']}",
                result["id"],
                result,
                match,
            )

        return None
