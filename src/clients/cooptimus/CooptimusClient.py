from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from clients import ClientBase, DatePart, RateLimit
from config import Config
from match_validator import MatchValidator

from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch


class CooptimusClient(ClientBase):
    __BASE_COOPTIMUS_URL = "https://api.co-optimus.com/games.php"

    __COOPTIMUS_PLATFORM_MAPPING: Dict[ExcelPlatform, int] = {
        ExcelPlatform.NINTENDO_SWITCH: 28,
        ExcelPlatform.NINTENDO_WII_U: 20,
        ExcelPlatform.PC: 4,
        ExcelPlatform.PLAYSTATION_2: 6,
        ExcelPlatform.PLAYSTATION_3: 2,
        ExcelPlatform.PLAYSTATION_4: 22,
        ExcelPlatform.PLAYSTATION_5: 30,
        ExcelPlatform.NINTENDO_WII: 3,
        ExcelPlatform.WIIWARE: 14,
        ExcelPlatform.XBOX: 5,
        ExcelPlatform.XBOX_360: 1,
        ExcelPlatform.XBOX_ONE: 24,
        ExcelPlatform.XBOX_SERIES_X_S: 31,
    }

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(1, DatePart.SECOND))

    async def search(self, name: str, system: int) -> Dict[str, Any]:
        return await self.get(
            f"{self.__BASE_COOPTIMUS_URL}",
            params={"search": str(True).lower(), "name": name, "system": system},
            json=False,
            retry_errors=[UnicodeDecodeError],
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in self.__COOPTIMUS_PLATFORM_MAPPING

    async def get_results(self, game: ExcelGame) -> List[Any]:
        html = await self.search(
            game.title, self.__COOPTIMUS_PLATFORM_MAPPING[game.platform]
        )

        soup = BeautifulSoup(html, "html.parser")
        return soup.find_all("game")

    async def result_to_match(
        self, game: ExcelGame, result: Any
    ) -> Optional[GameMatch]:
        title = result.title.getText().strip()
        release_years = None

        try:
            release_date = datetime.datetime.strptime(
                result.releasedate.getText().strip(), "%Y-%m-%d"
            )
            release_years = [release_date.year]
        except ValueError:
            release_date = None

        publisher = result.publisher.getText().strip()

        match = self.validator.validate(
            game, title, [game.platform.value], release_years, [publisher]
        )

        _id = int(result.id.getText().strip())
        url = result.url.getText().strip()

        if match.likely_match:
            return GameMatch(
                title,
                url,
                _id,
                {
                    "id": _id,
                    "title": title,
                    "genre": result.genre.getText().strip(),
                    "publisher": publisher,
                    "esrb": result.esrb.getText().strip(),
                    "release_date": release_date,
                    "local": int(result.local.getText().strip()),
                    "online": int(result.online.getText().strip()),
                    "lan": int(result.lan.getText().strip()),
                    "split_screen": bool(int(result.splitscreen.getText().strip())),
                    "drop_in_drop_out": bool(
                        int(result.dropindropout.getText().strip())
                    ),
                    "campaign": bool(int(result.campaign.getText().strip())),
                    "modes": bool(int(result.modes.getText().strip())),
                    "features": result.featurelist.getText().strip().split(", "),
                    "coop_experience": result.coopexp.getText().strip(),
                    "description": result.background.getText().strip(),
                    "url": url,
                    "art": result.art.getText().strip(),
                    "thumbnail": result.thumbnail.getText().strip(),
                },
                match,
            )

        return None
