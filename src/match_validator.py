"""Implements functionality for validating whether a result matches.

This file implements functionality for matching game rows to external sources.
It has a suite of validation functions for matching titles, platforms, and
release years.
"""

import html
import re
import unicodedata
from typing import Dict, List, NamedTuple

import edit_distance

from excel_game import ExcelGame
from constants import PLATFORM_NAMES


class ValidationInfo(NamedTuple):
    """Information about a validation.

    ValidationInfo contains information on whether this match
    matched in the first place and whether it was an exact match.

    Attributes:
        matched: Whether this represents a match
        exact: Whether this represents an exact match
    """

    matched: bool
    exact: bool


class MatchValidator:
    """The MatchValidator class implements functionality for matching games and rows.

    This class contains a number of functions for matching. It's able to handle exact
    normalized matches, fuzzy matching, platform matching, and release year matching.

    Attributes:
        __cached_normalization: A dictionary of non-normalized strings to normalized strings
        __THE_REGEX: A regex for removing leading "The" from game titles
    """

    __cached_normalization: Dict[str, str]
    __THE_REGEX = r"The "

    def __init__(self):
        self.__cached_normalization = {}

    def titles_equal_normalized(self, t_1: str, t_2: str) -> bool:
        """Checks whether the normalized titles are equal.

        This method normalizes each title and then compares the strings.

        Args:
            t_1: First string to compare
            t_2: Second string to compare

        Returns:
            Boolean indicating whether the two equal
        """
        if t_1 is None or t_2 is None:
            return False
        return self.normalize(t_1) == self.normalize(t_2)

    def titles_equal_fuzzy(self, t_1: str, t_2: str) -> bool:
        """Checks whether the normalized titles are fuzzy equal.

        This method normalizes each title and does some additional
        fuzzy comparison.

        Args:
            t_1: First string to compare
            t_2: Second string to compare

        Returns:
            Boolean indicating whether the two are fuzzy equal
        """
        t1_fuzzy = re.sub(self.__THE_REGEX, "", t_1.split(":")[0])
        t2_fuzzy = re.sub(self.__THE_REGEX, "", t_2.split(":")[0])

        return (
            self.titles_equal_normalized(t1_fuzzy, t2_fuzzy)
            or (
                edit_distance.SequenceMatcher(
                    a=self.normalize(t_1), b=self.normalize(t_2)
                ).distance()
                <= 2
                and not str.isdigit(t_1[-1])
                and not str.isdigit(t_2[-1])
            )
            or self.pokemon_special_case(t_1, t_2)
        )

    def pokemon_special_case(self, t_1: str, t_2: str) -> bool:
        """Special case handling for Pokemon games.

        Given my spreadsheet handles Pokemon version names without the
        suffix "version," this special casing helps to ensure there are
        matches against many sources.

        Args:
            t_1: First string to compare
            t_2: Second string to compare

        Returns:
            Boolean indicating whether the two are equal under Pokemon logic
        """
        if t_1.startswith("Pokémon") and not t_1.endswith("version"):
            return self.titles_equal_normalized(f"{t_1}version", t_2)
        return False

    @staticmethod
    def romanize(string: str) -> str:
        """Romanizes a string by replacing certain special characters with Latin.

        This method takes certain commonly occuring characters found in Japanese
        game titles and replaces them with a Latin string.

        Args:
            string: The string to Romanize

        Returns:
            A Romanized string
        """
        return (
            string.replace("ō", "o")
            .replace("ū", "u")
            .replace("Ō", "O")
            .replace("Ū", "U")
        )

    def normalize(self, string: str) -> str:
        """Normalizes a string with many normalization methods.

        This method transforms a string in a number of ways to do a
        normalized comparison. It strips trademark and copyright symbols,
        Romanizes the string, unescapes HTML, removes trailing dates (e.g. (2004)),
        lowercases the string, replaces ampersand with "and," normalizes Unicode, and
        strips non-alphanumeric characters.

        Args:
            string: The string to normalize

        Returns:
            A normalized string
        """
        if string in self.__cached_normalization:
            return self.__cached_normalization[string]
        normalized = "".join(
            filter(
                str.isalnum,
                unicodedata.normalize(
                    "NFKD",
                    re.sub(
                        r"( \([0-9]{4}\))",
                        "",
                        html.unescape(
                            MatchValidator.romanize(
                                string.replace("™", "")
                                .replace("®", "")
                                .replace("©", "")
                            )
                        )
                        .casefold()
                        .replace("&", "and"),
                    ),
                ).strip(),
            )
        )

        self.__cached_normalization[string] = normalized
        return normalized

    def validate(
        self,
        game: ExcelGame,
        title: str,
        platforms: List[str],
        release_years: List[int] = [],
    ) -> ValidationInfo:
        """Validates a potential matches characteristics against a row.

        This method takes in some values to compare against an ExcelGame.

        Args:
            game: The ExcelGame to validate a match for
            title: The title to check
            platforms: A list of platforms to verify
            release_years: A list of release years to verify
        """
        platform_equal = MatchValidator.verify_platform(game.platform, platforms)

        if not platform_equal:
            return ValidationInfo(False, False)

        year_equal = not any(release_years) or MatchValidator.verify_release_year(
            game.release_year, release_years
        )

        if not year_equal:
            return ValidationInfo(False, False)

        normal_equal = self.titles_equal_normalized(game.title, title)

        if normal_equal:
            return ValidationInfo(True, True)

        return ValidationInfo(self.titles_equal_fuzzy(game.title, title), False)

    @staticmethod
    def verify_platform(platform: str, platforms: List[str]) -> bool:
        """Verifies whether a list of platforms contains a given platform.

        This method ensures that a given platform matches any platforms exactly
        or matches with any of their aliases.

        Args:
            platform: The platform to check
            platforms: The platforms to check against

        Returns:
            Boolean indicating whether platform was found in platforms
        """
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
        """Verifies whether a release year is within a list of release years.

        This methods ensures that a given release year matches any release years.

        Args:
            release_year: The release year to check
            release_years The release years to check against

        Returns:
            Boolean indicating whether release year was contained in release years
        """
        return release_year in release_years
