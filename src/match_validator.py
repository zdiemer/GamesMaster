import html
import re
import unicodedata
from typing import Dict, List, NamedTuple

import edit_distance

from excel_game import ExcelGame as ExcelGame
from constants import PLATFORM_NAMES


class ValidationInfo(NamedTuple):
    matched: bool
    exact: bool


class MatchValidator:
    __cached_normalization: Dict[str, str]

    def __init__(self):
        self.__cached_normalization = {}

    def titles_equal_normalized(self, t1: str, t2: str) -> bool:
        if t1 is None or t2 is None:
            return False
        return self.normalize(t1) == self.normalize(t2)

    def titles_equal_fuzzy(self, t1: str, t2: str) -> bool:
        return (
            self.titles_equal_normalized(t1.split(":")[0], t2.split(":")[0])
            or edit_distance.SequenceMatcher(
                a=self.normalize(t1), b=self.normalize(t2)
            ).distance()
            <= 2
        )

    @staticmethod
    def romanize(s: str) -> str:
        return s.replace("ō", "o").replace("ū", "u").replace("Ō", "O").replace("Ū", "U")

    def normalize(self, s: str) -> str:
        if s in self.__cached_normalization:
            return self.__cached_normalization[s]
        normalized = "".join(
            filter(
                str.isalnum,
                unicodedata.normalize(
                    "NFKD",
                    re.sub(
                        r"( \([0-9]{4}\))",
                        "",
                        html.unescape(MatchValidator.romanize(s))
                        .casefold()
                        .replace("&", "and"),
                    ),
                ).strip(),
            )
        )

        self.__cached_normalization[s] = normalized
        return normalized

    def validate(
        self,
        game: ExcelGame,
        title: str,
        platforms: List[str],
        release_years: List[int] = [],
    ) -> ValidationInfo:
        platform_equal = MatchValidator.verify_platform(game.platform, platforms)

        if not platform_equal:
            return ValidationInfo(False, False)

        year_equal = not any(release_years) or MatchValidator.verify_release_year(
            game.release_date.year, release_years
        )

        if not year_equal:
            return ValidationInfo(False, False)

        normal_equal = self.titles_equal_normalized(game.title, title)

        if normal_equal:
            return ValidationInfo(True, True)

        return ValidationInfo(self.titles_equal_fuzzy(game.title, title), False)

    @staticmethod
    def verify_platform(platform: str, platforms: List[str]) -> bool:
        if platforms is None or not any(platforms):
            return False
        return any(
            filter(
                lambda p: p.lower() == platform.lower()
                or p.lower() in PLATFORM_NAMES[platform.lower()],
                platforms,
            )
        )

    @staticmethod
    def verify_release_year(release_year: int, release_years: List[int]) -> bool:
        return release_year in release_years
