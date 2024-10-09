import json
from typing import Any, List, Literal

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class ArcadeDatabaseClient(ClientBase):
    BASE_URL: str = "http://adb.arcadeitalia.net"
    DEFAULT_URL: str = BASE_URL + "/default.php"
    SERVICE_SCRAPER_URL: str = BASE_URL + "/service_scraper.php"

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(4, DatePart.SECOND))

    async def default(self, title: str) -> Any:
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
        game_name: str,
        use_parent: bool = False,
        resize: Literal["0", "100h", "200h", "300h", "100w", "200w", "300w"] = "0",
        lang: Literal["en", "it"] = "en",
    ) -> Any:
        return await self.get(
            self.SERVICE_SCRAPER_URL,
            params={
                "ajax": "query_mame",
                "game_name": game_name,
                "use_parent": int(use_parent),
                "resize": resize,
                "lang": lang,
            },
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform != ExcelPlatform.ARCADE

    async def get_results(self, game: ExcelGame) -> List[Any]:
        mame_names = json.loads(str(await self.default(game.title)))

        if not any(mame_names):
            return []

        results = await self.query_mame(game_name=";".join(m["id"] for m in mame_names))

        return results.get("result") or []

    async def result_to_match(self, game: ExcelGame, result: Any) -> GameMatch | None:
        match = self.validator.validate(
            game, result["title"], [game.platform.value], [result["year"]]
        )

        if match.likely_match:
            return GameMatch(
                result["title"], result["url"], result["game_name"], result, match
            )

        return None
