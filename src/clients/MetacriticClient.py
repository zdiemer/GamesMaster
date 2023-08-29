from __future__ import annotations

import aiohttp
from typing import List, Literal

from bs4 import BeautifulSoup

from excel_game import ExcelGame as ExcelGame, ExcelRegion as Region
from helpers import validate

class MetacriticGame:
    title: str
    platform: str
    score: int | Literal['tbd']
    url: str

    def __init__(self, title: str, platform: str, score: int | Literal['tbd'], url: str):
        self.title = title
        self.platform = platform
        self.score = score

class MetacriticClient:
    __BASE_METACRITIC_URL = 'https://www.metacritic.com'
    __METACRITIC_HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }

    def __init__(self):
        pass

    @staticmethod
    def create() -> MetacriticClient:
        return MetacriticClient()
    
    async def _search(self, term: str):
        payload = {
            'search_term': term,
            'search_filter': 'game'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f'{self.__BASE_METACRITIC_URL}/search',
                    headers=self.__METACRITIC_HEADERS,
                    data=payload) as res:
                return await res.text()

    async def match_game(self, game: ExcelGame) -> List[MetacriticGame]:
        if game.release_region != Region.NORTH_AMERICA:
            return []

        text = await self._search(game.title)
        soup = BeautifulSoup(text, 'html.parser')
        results = soup.find_all('div', {'class': 'main_stats'})
        matches = []

        for r in results:
            title = r.h3.a.text.strip()
            platform = r.p.span.text.strip()
            score = r.span.text.strip()
            url = r.h3.a['href']
            if validate(game, title, [platform]):
                matches.append(
                    MetacriticGame(
                        title,
                        platform,
                        int(score) if score != 'tbd' else score,
                        f'{self.__BASE_METACRITIC_URL}{url}'))

        return matches