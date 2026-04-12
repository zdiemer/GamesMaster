from typing import Any, List

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class ThumbyClient(ClientBase):
    THUMBY_SLUG = "TinyCircuits-Thumby-Games/master/url_list.txt"
    THUMBY_COLOR_SLUG = "TinyCircuits-Thumby-Color-Games/master/url_list.txt"

    def __init__(self, validator: MatchValidator = None, config: Config = None):
        validator = validator or MatchValidator()
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            base_url="https://raw.githubusercontent.com/TinyCircuits",
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in (ExcelPlatform.THUMBY, ExcelPlatform.THUMBY_COLOR)

    async def get_results(self, _: ExcelGame) -> List[str]:
        return [
            g.strip()
            for g in (
                await self.get(f"{self.base_url}/{self.THUMBY_SLUG}", json=False)
            ).split("NAME=")
        ] + [
            g.strip()
            for g in (
                await self.get(f"{self.base_url}/{self.THUMBY_COLOR_SLUG}", json=False)
            ).split("NAME=")
        ]

    async def result_to_match(
        self, game: ExcelGame, result: str, is_fallback: bool = False
    ) -> GameMatch | None:
        lines = result.split("\n")
        name = lines[0]
        urls = lines[1:]

        if self.validator.titles_equal_normalized(
            game.title, name
        ) or self.validator.titles_equal_fuzzy(game.title, name):
            return GameMatch(
                name,
                (
                    urls[0]
                    .rsplit("/", maxsplit=1)[0]
                    .replace("raw.githubusercontent.com", "github.com")
                    .replace("/master/", "/blob/master/")
                    .replace("/main/", "/tree/main/")
                    if urls
                    else None
                ),
                name,
                {
                    "name": name,
                    "urls": urls,
                    "description": await self.get(
                        next(
                            filter(lambda url: url.endswith("_description.txt"), urls),
                            "",
                        ),
                        json=False,
                    ),
                },
                self.validator.validate(game, name, [game.platform.value]),
            )

        return None
