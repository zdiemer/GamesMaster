"""Classes for holding match info about game rows to external sources."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

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
    GAME_JOLT = 12
    COOPTIMUS = 13
    ARCADE_DATABASE = 14

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
        game_id: Optional[int] = None,
        match_info: Optional[Any] = None,
        validation_info: Optional[ValidationInfo] = None,
    ):
        self.title = title
        self.url = url
        self.id = game_id
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
    offset: int
    batch_size: int

    _successes: Dict[int, GameMatchResult]
    _errors: Dict[int, GameMatchResult]
    _skipped: Dict[int, GameMatchResult]
    _index: int

    def __init__(self, offset: int, batch_size: int):
        self.offset = offset
        self.batch_size = batch_size
        self._successes = {}
        self._errors = {}
        self._skipped = {}
        self._index = 0

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()

    def __len__(self):
        return len(self.successes) + len(self.errors)

    @property
    def successes(self) -> List[GameMatchResult]:
        return list(self._successes.values())

    @property
    def errors(self) -> List[GameMatchResult]:
        return list(self._errors.values())

    @property
    def skipped(self) -> List[GameMatchResult]:
        return list(self._skipped.values())

    def append(
        self,
        gmr: GameMatchResult,
        match_type: Literal["success", "error", "skipped"] = "success",
    ):
        if match_type == "success":
            self._successes[self._index] = gmr
        if match_type == "error":
            self._errors[self._index] = gmr
        if match_type == "skipped":
            self._skipped[self._index] = gmr

        self._index += 1

    def extend(
        self,
        gmrs: List[GameMatchResult],
        match_type: Literal["success", "error", "skipped"] = "success",
    ):
        for gmr in gmrs:
            self.append(gmr, match_type)

    def __getitem__(self, key: int) -> GameMatchResult:
        if key in self._successes:
            return self._successes[key]
        if key in self._errors:
            return self._errors[key]
        if key in self._skipped:
            return self._skipped[key]

        raise KeyError
