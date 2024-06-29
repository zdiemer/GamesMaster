"""Models for mapping GameFAQs data to classes.

This file contains classes that wrap data fetched from
GameFAQs. These classes comprise different game related
concepts, e.g. platforms, genres, etc.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional


class GameFaqsPlatform:
    """Class representing a platform on GameFAQs.

    This class represents a platform as they exist on GameFAQs.

    Attributes:
        name: The name of the platform
    """

    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsGenre:
    """Class representing a genre on GameFAQs.

    This class represents a genre as they exist on GameFAQs.

    Attributes:
        name: The name of the genre
        parent_genre: The parent of this genre, if it's a child
    """

    name: str
    parent_genre: Optional[GameFaqsGenre]

    def __init__(self, name: str, parent_genre: GameFaqsGenre = None):
        self.name = name
        self.parent_genre = parent_genre

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsCompany:
    """Class representing a company on GameFAQs.

    This class represents a company as they exist on GameFAQs.

    Attributes:
        name: The name of the company
    """

    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsRegion(Enum):
    """Release regions for games on GameFAQs"""

    JP = "JP"
    US = "US"
    EU = "EU"
    AU = "AU"
    KO = "KO"
    AS = "AS"
    SA = "SA"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsReleaseStatus(Enum):
    """Release statuses for games on GameFAQs"""

    RELEASED = 1
    CANCELED = 2
    UNRELEASED = 3

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsRelease:
    """Class representing a game release on GameFAQs.

    This class represents a game release as they exist on GameFAQs.
    One game can have many releases.

    Attributes:
        release_day: The day of the month this game was released
        release_month: The month this game was released
        release_year: The year this game was released
        release_region: The region this release maps to
        publisher: A company which published this release
        product_id: Generally a product ID specific to the console manufacturer
        distribution_or_barcode: Either a distribution platform (e.g. Wii U eShop) or a UPC
        age_rating: If applicable, the rating this received from the region's ratings board
        title: The title for this particular release. May differ from the game's title
        status: The status for this release
    """

    release_day: Optional[int] = None
    release_month: Optional[int] = None
    release_year: Optional[int] = None
    release_region: Optional[GameFaqsRegion] = None
    publisher: Optional[GameFaqsCompany] = None
    product_id: Optional[str] = None
    distribution_or_barcode: Optional[str] = None
    age_rating: Optional[str] = None
    title: Optional[str] = None
    status: GameFaqsReleaseStatus = GameFaqsReleaseStatus.RELEASED

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsFranchise:
    """Class representing a game franchise on GameFAQs.

    This class represents a game franchise as they exist on GameFAQs.

    Attributes:
        name: The name of the game franchise
    """

    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsGuide:
    """Class representing a guide for a game on GameFAQs.

    This class represents a GameFAQs guide. It holds all of the information
    about the guide along with full text if it is a plaintext guide.

    Attributes:
        title: The title for this guide
        url: A link to this guide
        author_name: The username of the person who authored this guide
        author_url: A link to the author's profile
        version: The version for this guide, e.g. 1.0
        updated_date: The most recent update date for this guide
        full_text: The full text for this guide, if applicable
        highest_rated: Whether this is a "Highest Rated" guide
        most_recommended: Whether this is a "Most Recommended" guide
        html: Whether this is an HTML guide
        platform: The platform this guide maps to
        faq_of_the_month_winner: Whether this guide won "FAQ of the Month"
        faq_of_the_month_month: The month this guide won
        faq_of_the_month_year: The year this guide won
        incomplete: Whether the guide is incomplete
    """

    title: Optional[str] = None
    url: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    version: Optional[str] = None
    updated_date: Optional[datetime] = None
    full_text: Optional[str] = None
    highest_rated: bool = False
    most_recommended: bool = False
    html: bool = False
    platform: Optional[GameFaqsPlatform] = None
    faq_of_the_month_winner: bool = False
    faq_of_the_month_month: Optional[str] = None
    faq_of_the_month_year: Optional[int] = None
    incomplete: bool = False

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsGame:
    """Class representing a game on GameFAQs.

    This class represents a game as they exist on GameFAQs.

    Attributes:
        id: GameFAQs's internal ID for this game
        title: The title of this game
        url: A link to this game
        platform: The platform this game maps to
        genre: Genres for this game
        releases: Releases for this game
        developer: The company that developed this game
        franchises: Franchises this game belongs to
        user_rating: User rating for this game
        user_rating_count: The number of user ratings this guide received
        user_difficulty: The difficulty for this game, rated by users
        user_difficulty_count: The number of users who rated this game's difficulty
        user_length_hours: The length in hours for this game, rated by users
        user_length_hours_count: The number of users who rated this game's length
        guides: Any guides that exist for this game
        aliases: Other names this game is known by
    """

    id: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[GameFaqsPlatform] = None
    genre: Optional[GameFaqsGenre] = None
    releases: Optional[List[GameFaqsRelease]] = None
    developer: Optional[GameFaqsCompany] = None
    franchises: Optional[List[GameFaqsFranchise]] = None
    user_rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    user_difficulty: Optional[float] = None
    user_difficulty_count: Optional[int] = None
    user_length_hours: Optional[float] = None
    user_length_hours_count: Optional[int] = None
    guides: Optional[List[GameFaqsGuide]] = None
    aliases: Optional[List[str]] = None

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()
