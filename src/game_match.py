from enum import Enum
from typing import Any, Optional


class DataSource(Enum):
    GAME_FAQS = 1
    GIANT_BOMB = 2
    IGDB = 3
    METACRITIC = 4
    MOBY_GAMES = 5
    ROM_HACKING = 6
    STEAM = 7
    HLTB = 8
    PRICE_CHARTING = 9

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameMatch:
    id: Optional[int]
    title: str
    url: Optional[str]
    source: DataSource
    match_info: Optional[Any]

    def __init__(
        self,
        title: str,
        url: Optional[str] = None,
        id: Optional[int] = None,
        match_info: Optional[Any] = None,
    ):
        self.title = title
        self.url = url
        self.id = id
        self.match_info = match_info

    def __str__(self) -> str:
        return str(
            {
                "id": self.id,
                "title": self.title,
                "url": self.url,
                "source": self.source,
                "match_info": self.match_info,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()
