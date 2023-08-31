from __future__ import annotations

import aiohttp
import re
from typing import List, Literal

from bs4 import BeautifulSoup

from excel_game import ExcelGame, ExcelRegion as Region
from match_validator import MatchValidator


class MetacriticGame:
    title: str
    platform: str
    score: int
    url: str
    release_year: int

    def __init__(
        self, title: str, platform: str, score: int, url: str, release_year: int
    ):
        self.title = title
        self.platform = platform
        self.score = score
        self.url = url
        self.release_year = release_year


class MetacriticClient:
    __BASE_METACRITIC_URL = "https://www.metacritic.com"
    __METACRITIC_HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    }

    def __init__(self):
        pass

    @staticmethod
    def create() -> MetacriticClient:
        return MetacriticClient()

    async def _search(self, term: str):
        payload = {"search_term": term, "search_filter": "game"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.__BASE_METACRITIC_URL}/search",
                headers=self.__METACRITIC_HEADERS,
                data=payload,
            ) as res:
                return await res.text()

    async def match_game(self, game: ExcelGame) -> List[MetacriticGame]:
        if game.release_region != Region.NORTH_AMERICA:
            return []

        text = await self._search(game.title)
        soup = BeautifulSoup(text, "html.parser")
        results = soup.find_all("div", {"class": "main_stats"})
        matches = []
        validator = MatchValidator()

        for r in results:
            title = r.h3.a.text.strip()
            platform = r.p.span.text.strip()
            score = r.span.text.strip()
            url = r.h3.a["href"]

            if score == "tbd":
                continue

            year_match = re.search(r"Game, (?P<year>[0-9]{4})", r.p.getText())

            if year_match is None:
                continue

            year = int(year_match.group("year"))

            match = validator.validate(game, title, [platform], [year])
            if match.matched:
                matches.append(
                    (
                        MetacriticGame(
                            title,
                            platform,
                            int(score),
                            f"{self.__BASE_METACRITIC_URL}{url}",
                            year,
                        ),
                        match,
                    ),
                )

        return matches
