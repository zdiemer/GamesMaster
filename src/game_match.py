"""Classes for holding match info about game rows to external sources."""

from enum import Enum
from typing import Any, List, Optional

from excel_game import ExcelGame
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
    VG_CHARTZ = 10
    GAMEYE = 11

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
        match_info: Any additional external match info
        validation_info: Information on how this game matched
    """

    id: Optional[int]
    title: str
    url: Optional[str]
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
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()

    def is_guaranteed_match(self):
        return self.validation_info.exact and self.validation_info.full_match


class GameMatchResult:
    game: Optional[ExcelGame]
    matches: Optional[List[GameMatch]]
    error: Optional[str]

    def __init__(
        self,
        game: Optional[ExcelGame] = None,
        matches: Optional[List[GameMatch]] = None,
        error: Optional[str] = None,
    ):
        self.game = game
        self.matches = matches or []
        self.error = error

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class GameMatchResultSet:
    successes: List[GameMatchResult]
    errors: List[GameMatchResult]
    skipped: List[GameMatchResult]
    offset: int
    batch_size: int

    def __init__(self, offset: int, batch_size: int):
        self.successes = []
        self.errors = []
        self.skipped = []
        self.offset = offset
        self.batch_size = batch_size

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()
