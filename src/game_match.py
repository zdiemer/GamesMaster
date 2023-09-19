"""Classes for holding match info about game rows to external sources."""

from enum import Enum
from typing import Any, Optional

from match_validator import ValidationInfo


class DataSource(Enum):
    """External data sources to be used for matching."""

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
    """Class for information about a match for a game ID.

    This class contains information about a potential match against
    a row corresponding to id.

    Attributes:
        id: The ID for a row in the spreadsheet
        title: The matched title
        url: A URL for the match result
        source: The DataSource corresponding to this match
        match_info: Any additional external match info
        validation_info: Information on how this game matched
    """

    id: Optional[int]
    title: str
    url: Optional[str]
    source: DataSource
    match_info: Optional[Any]
    validation_info: Optional[ValidationInfo]

    def __init__(
        self,
        title: str,
        url: Optional[str] = None,
        id: Optional[int] = None,
        match_info: Optional[Any] = None,
        validation_info: Optional[ValidationInfo] = None,
    ):
        self.title = title
        self.url = url
        self.id = id
        self.match_info = match_info
        self.validation_info = validation_info

    def __str__(self) -> str:
        return str(
            {
                "id": self.id,
                "title": self.title,
                "url": self.url,
                "source": self.source,
                "match_info": self.match_info,
                "validation_info": self.validation_info,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()
