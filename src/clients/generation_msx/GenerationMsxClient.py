from __future__ import annotations

from typing import Any, AsyncGenerator, List

from bs4 import BeautifulSoup

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class GenerationMsxClient(ClientBase):
    __BASE_GENERATION_MSX_URL = "https://www.generation-msx.nl"

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, spoof_headers=True)

    async def search(self, game: ExcelGame, page: int = 1) -> AsyncGenerator[Any]:
        return await self.get(
            f"{self.__BASE_GENERATION_MSX_URL}/software/result",
            params={"q": game.title, "p": page, "ki[]": "game"},
            json=False,
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in (
            ExcelPlatform.MSX,
            ExcelPlatform.MSX2,
            ExcelPlatform.MSX_TURBO_R,
            ExcelPlatform.LASERDISC,
        )

    async def get_results_paginated(
        self, game: ExcelPlatform
    ) -> AsyncGenerator[List[Any]]:
        page = 1
        html = await self.search(game, page)
        soup = BeautifulSoup(html, "html.parser")
        _next = soup.find("li", {"class": "next"})
        table = soup.find("table", {"class": "table table-striped"})

        if table is None:
            yield []
        else:
            yield table.tbody.find_all("tr")

        while _next is not None:
            page += 1
            html = await self.search(game, page)
            soup = BeautifulSoup(html, "html.parser")
            _next = soup.find("li", {"class": "next"})
            table = soup.find("table", {"class": "table table-striped"})
            yield table.tbody.find_all("tr")

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        title_elem, developers_elem, publishers_elem, year_elem = result.find_all("td")

        try:
            year = int(year_elem.text.strip())
        except ValueError:
            year = None

        match_data = {
            "title": title_elem.a.text.strip(),
            "developers": [
                {
                    "name": de.text.strip(),
                    "url": f"{self.__BASE_GENERATION_MSX_URL}{de['href']}",
                }
                for de in developers_elem.find_all("a")
            ],
            "publishers": [
                {
                    "name": pe.text.strip(),
                    "url": f"{self.__BASE_GENERATION_MSX_URL}{pe['href']}",
                }
                for pe in publishers_elem.find_all("a")
            ],
            "year": year,
            "platforms": [
                el["alt"]
                for el in title_elem.find_all("img", {"class": "msx-icon"})
                if el["alt"] not in ("MSX-Music", "SCC")
            ],
            "url": f"{self.__BASE_GENERATION_MSX_URL}{title_elem.a['href']}",
        }

        match = self.validator.validate(
            game,
            match_data["title"],
            match_data["platforms"],
            [match_data["year"]],
            match_data["publishers"],
            match_data["developers"],
        )

        if match.likely_match:
            return GameMatch(
                match_data["title"],
                match_data["url"],
                match_data["url"].rsplit("/", maxsplit=1)[-1],
                match_data,
                match,
            )

        return None
