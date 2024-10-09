"""Implements functionality for validating whether a result matches.

This file implements functionality for matching game rows to external sources.
It has a suite of validation functions for matching titles, platforms, and
release years.
"""

import html
import unicodedata
import re
from typing import Dict, List, Optional

import edit_distance
import roman

from excel_game import ExcelGame
from constants import PLATFORM_NAMES


class ValidationInfo:
    """Information about a validation.

    ValidationInfo contains information on whether this match
    matched in the first place and whether it was an exact match.

    Attributes:
        matched: Whether this represents a match
        exact: Whether this represents an exact match
        platform_matched: Whether this represents a platform match
        date_matched: Whether this represents a date match
    """

    matched: bool
    exact: bool
    platform_matched: bool
    date_matched: bool
    publisher_matched: bool
    developer_matched: bool
    franchise_matched: bool

    def __init__(
        self,
        matched: bool,
        exact: bool = False,
        platform_matched: bool = False,
        date_matched: bool = False,
        publisher_matched: bool = False,
        developer_matched: bool = False,
        franchise_matched: bool = False,
    ):
        self.matched = matched
        self.exact = exact
        self.platform_matched = platform_matched
        self.date_matched = date_matched
        self.publisher_matched = publisher_matched
        self.developer_matched = developer_matched
        self.franchise_matched = franchise_matched

    @property
    def likely_match(self):
        """Returns whether this is a likely match (i.e. title and platform)"""
        return self.matched and self.platform_matched

    @property
    def full_match(self):
        """Returns whether this is a full match, but not necessarily exact

        This method checks whether all properties have matched, but doesn't
        guarantee that this is an exact title match.
        """
        return self.matched and self.platform_matched and self.date_matched

    @property
    def components_matched(self):
        """Returns whether additional components not required for full match matched

        This method checks whether all components have matched, regardless of
        whether they were required for validating a full match.
        """
        return (
            self.publisher_matched and self.developer_matched and self.franchise_matched
        )

    @property
    def match_score(self):
        """Returns a score for this match

        This method checks whether all components have matched, regardless of
        whether they were required for validating a full match.
        """
        return (
            int(self.matched) * 5
            + int(self.exact) * 5
            + int(self.platform_matched)
            + int(self.date_matched)
            + int(self.publisher_matched)
            + int(self.developer_matched)
            + int(self.franchise_matched)
        )

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


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
        t_1 = str(t_1)
        t_2 = str(t_2)
        t1_fuzzy = re.sub(self.__THE_REGEX, "", t_1.split(":", maxsplit=1)[0])
        t2_fuzzy = re.sub(self.__THE_REGEX, "", t_2.split(":", maxsplit=1)[0])

        return (
            self.titles_equal_normalized(t1_fuzzy, t2_fuzzy)
            or (
                edit_distance.SequenceMatcher(
                    a=self.normalize(t_1), b=self.normalize(t_2)
                ).distance()
                <= 2
                and len(t_1) > 1
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

    def romanize(self, string: str) -> str:
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

    def roman_numeralize(self, string: str, _max: int = 20) -> str:
        """Converts Roman numeral parts to real numbers.

        This method takes in a string and converts any of its whitespace
        split parts into real numbers instead of Roman numerals.

        Args:
            string: The string to Roman numeralize

        Returns:
            A Roman numeralized string
        """

        def try_roman_numeralize(_str: str) -> str:
            try:
                _filter_str = "".join(filter(str.isalnum, _str))
                _num = roman.fromRoman(_filter_str.upper())
                if _num > _max:
                    return _str
                return str(_num)
            except roman.InvalidRomanNumeralError:
                return _str

        return " ".join([try_roman_numeralize(_str) for _str in string.split()])

    def normalize(self, string: str) -> str:
        """Normalizes a string with many normalization methods.

        This method transforms a string in a number of ways to do a
        normalized comparison. It strips trademark and copyright symbols,
        Romanizes the string, unescapes HTML, removes trailing dates (e.g. (2004)),
        lowercases the string, replaces ampersand with "and," normalizes Unicode,
        strips non-alphanumeric characters, and converts Roman numerals to real numbers.

        Args:
            string: The string to normalize

        Returns:
            A normalized string
        """
        string = str(string)
        if string in self.__cached_normalization:
            return self.__cached_normalization[string]
        normalized = "".join(
            filter(
                str.isalnum,
                unicodedata.normalize(
                    "NFKD",
                    re.sub(
                        r"( \([A-Za-z0-9]{4}\))",
                        "",
                        html.unescape(
                            self.roman_numeralize(
                                self.romanize(
                                    string.replace("™", "")
                                    .replace("®", "")
                                    .replace("©", "")
                                )
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
        platforms: List[str] = None,
        release_years: List[int] = None,
        publishers: List[str] = None,
        developers: List[str] = None,
        franchises: List[str] = None,
    ) -> ValidationInfo:
        """Validates a potential matches characteristics against a row.

        This method takes in some values to compare against an ExcelGame.

        Args:
            game: The ExcelGame to validate a match for
            title: The title to check
            platforms: A list of platforms to verify
            release_years: A list of release years to verify
        """
        normal_equal = self.titles_equal_normalized(game.title, title)

        fuzzy_equal = normal_equal or self.titles_equal_fuzzy(game.title, title)

        if not fuzzy_equal:
            return ValidationInfo(matched=False)

        platform_equal = (
            platforms is not None
            and any(platforms)
            and self.verify_platform(game.platform.value, platforms)
        )

        year_equal = (
            release_years is not None
            and any(release_years)
            and self.verify_release_year(game.release_year, release_years)
        )

        return ValidationInfo(
            matched=normal_equal or self.titles_equal_fuzzy(game.title, title),
            exact=normal_equal,
            platform_matched=platform_equal,
            date_matched=year_equal,
            developer_matched=self.verify_component(game.developer, developers),
            publisher_matched=self.verify_component(game.publisher, publishers),
            franchise_matched=self.verify_franchise(game.franchise, franchises),
        )

    def verify_platform(self, platform: str, platforms: List[str]) -> bool:
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

    def verify_release_year(self, release_year: int, release_years: List[int]) -> bool:
        """Verifies whether a release year is within a list of release years.

        This methods ensures that a given release year matches any release years.

        Args:
            release_year: The release year to check
            release_years The release years to check against

        Returns:
            Boolean indicating whether release year was contained in release years
        """
        return release_year in release_years

    def verify_component(self, component: str, components: List[str]) -> bool:
        """Verifies whether a component's normalized form equals any in components.

        This methods ensures that a given component matches any components.

        Args:
            component: The company to check
            components: The components to check against

        Returns:
            Boolean indicating whether normalized component was contained in components
        """
        if components is None or not any(components):
            return False

        normalized_component = self.normalize(component)

        return any(normalized_component == self.normalize(c) for c in components)

    def verify_franchise(
        self, franchise: Optional[str], franchises: Optional[List[str]]
    ) -> bool:
        if not any(franchises or []) and not franchise:
            return True

        return self.verify_component(franchise, franchises)

    def check_platform_alias_is_mapped(self, platform: str) -> bool:
        platform = platform.lower()
        return platform in PLATFORM_NAMES or any(
            platform in p for p in PLATFORM_NAMES.values()
        )
