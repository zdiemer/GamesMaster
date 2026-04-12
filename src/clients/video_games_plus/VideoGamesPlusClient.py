import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any, Tuple

from bs4 import BeautifulSoup, ResultSet

from excel_game import ExcelGame, ExcelPlatform
from excel_loader import ExcelLoader
from clients import ShoppingClientBase, BaseResult
from config import Config
from match_validator import MatchValidator


class VideoGamesPlusClient(ShoppingClientBase):
    __BASE_VIDEO_GAMES_PLUS_URL = "https://www.videogamesplus.ca"
    __PRE_ORDERS_URL = f"{__BASE_VIDEO_GAMES_PLUS_URL}/collections/pre-orders-1"

    async def get_preorders(self) -> AsyncGenerator[ResultSet[Any], None]:
        page = 1
        while True:
            res = await self.get(
                self.__PRE_ORDERS_URL,
                params={"page": page},
                json=False,
            )
            soup = BeautifulSoup(res, "html.parser")
            preorders = soup.find_all("div", class_="product-card__content")
            if not preorders:
                break
            yield preorders
            page += 1

    async def get_upcoming_games(self) -> Dict[ExcelPlatform, List[BaseResult]]:
        return await super().get_upcoming_games()
