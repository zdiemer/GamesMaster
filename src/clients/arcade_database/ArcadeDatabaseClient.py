import json
from typing import Any, Dict, List, Literal

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator

from .arcade_database_types import QueryMameResponse


class ArcadeDatabaseClient(ClientBase):
    BASE_URL: str = "http://adb.arcadeitalia.net"
    DEFAULT_URL: str = BASE_URL + "/default.php"
    SERVICE_SCRAPER_URL: str = BASE_URL + "/service_scraper.php"

    def __init__(self, validator: MatchValidator = None, config: Config = None):
        validator = validator or MatchValidator()
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(4, DatePart.SECOND))

    async def default(self, title: str) -> Dict[str, Any]:
        return await self.get(
            self.DEFAULT_URL,
            params={
                "ajax": "input",
                "oper": "autocomplete",
                "id": "ricerca_mame_text",
                "form": "fast_search",
                "term": title,
            },
            json=False,
        )

    async def query_mame(
        self,
        game_name: str | List[str],
        use_parent: bool = False,
        resize: Literal["0", "100h", "200h", "300h", "100w", "200w", "300w"] = "0",
        lang: Literal["en", "it"] = "en",
    ) -> List[QueryMameResponse]:
        response = await self.get(
            self.SERVICE_SCRAPER_URL,
            params={
                "ajax": "query_mame",
                "game_name": (
                    game_name if isinstance(game_name, str) else ";".join(game_name)
                ),
                "use_parent": int(use_parent),
                "resize": resize,
                "lang": lang,
            },
        )

        return [QueryMameResponse.from_json(r) for r in response["result"]]

    async def download_status(self) -> Any:
        return await self.get(
            self.SERVICE_SCRAPER_URL, params={"ajax": "download_status"}
        )

    async def query_mame_like(self) -> Any:
        pass

    def should_skip(self, game: ExcelGame) -> bool:
        return game.mame_romset is None

    async def get_results(self, game: ExcelGame) -> List[Any]:
        return await self.query_mame(game_name=game.mame_romset)

    async def result_to_match(
        self, game: ExcelGame, result: QueryMameResponse, is_fallback: bool = False
    ) -> GameMatch | None:
        match = self.validator.validate(
            game, result.title, [game.platform.value], [result.year]
        )

        if not match.likely_match:
            match.exact = match.matched = match.platform_matched = (
                self.validator.titles_equal_normalized(
                    game.mame_romset, result.game_name
                )
            )

            match.date_matched = self.validator.verify_release_year(
                game.release_year, [result.year]
            )

        if match.likely_match:
            return GameMatch(result.title, result.url, result.game_name, result, match)

        return None

    async def _manual_match_impl(self, game: ExcelGame) -> GameMatch | None:
        mame_name = input(f"Input the MAME name for {game.full_name}: ").lower().strip()

        results = await self.query_mame(game_name=mame_name)

        if not any(results):
            return None

        result = results[0]

        return GameMatch(result.title, result.url, result.game_name, result)
