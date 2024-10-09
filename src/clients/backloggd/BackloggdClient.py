from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterator

from bs4 import BeautifulSoup

from clients import ClientBase, DatePart, RateLimit
from config import Config
from match_validator import MatchValidator


class BackloggdClient(ClientBase):
    __BASE_BACKLOGGD_URL = "https://www.backloggd.com"

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(30, DatePart.MINUTE))

    async def popular(self, page: int = 1) -> Dict[str, Any]:
        return await self.get(
            f"{self.__BASE_BACKLOGGD_URL}/games/lib/popular",
            params={"page": page},
            json=False,
        )

    def get_popular_games(self) -> Iterator[str]:
        page = 1

        while page <= 5291:
            popular_doc = asyncio.run(self.popular(page))
            soup = BeautifulSoup(popular_doc, "html.parser")

            games = soup.find_all("div", {"class": "game-text-centered"})

            for g in games:
                yield g.text.strip()
            page += 1
