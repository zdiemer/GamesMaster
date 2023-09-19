from __future__ import annotations

from enum import Enum
from typing import List


class GameFaqsPlatform:
    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsGenre:
    name: str
    parent_genre: GameFaqsGenre

    def __init__(self, name: str, parent_genre: GameFaqsGenre = None):
        self.name = name
        self.parent_genre = parent_genre

    def __str__(self) -> str:
        return str({"name": self.name, "parent_genre": self.parent_genre})

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsCompany:
    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsRegion(Enum):
    JP = "JP"
    US = "US"
    EU = "EU"
    AU = "AU"
    KO = "KO"
    AS = "AS"
    SA = "SA"


class GameFaqsReleaseStatus(Enum):
    RELEASED = 1
    CANCELED = 2
    UNRELEASED = 3


class GameFaqsRelease:
    release_day: int = None
    release_month: int = None
    release_year: int = None
    release_region: GameFaqsRegion = None
    publisher: GameFaqsCompany = None
    product_id: str = None
    distribution_or_barcode: str = None
    age_rating: str = None
    title: str = None
    status: GameFaqsReleaseStatus = GameFaqsReleaseStatus.RELEASED

    def __str__(self) -> str:
        return str(
            {
                "release_day": self.release_day,
                "release_month": self.release_month,
                "release_year": self.release_year,
                "release_region": self.release_region.value,
                "publisher": self.publisher,
                "product_id": self.product_id,
                "distribution_or_barcode": self.distribution_or_barcode,
                "age_rating": self.age_rating,
                "title": self.title,
                "status": self.status.name.title(),
            }
        )

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsFranchise:
    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsGame:
    id: int = None
    title: str = None
    url: str = None
    platform: GameFaqsPlatform = None
    genre: GameFaqsGenre = None
    releases: List[GameFaqsRelease] = None
    developer: GameFaqsCompany = None
    franchises: List[GameFaqsFranchise] = None
    user_rating: float = None
    user_rating_count: int = None
    user_difficulty: float = None
    user_difficulty_count: int = None
    user_length_hours: float = None
    user_length_hours_count: int = None

    def __str__(self) -> str:
        return str(
            {
                "id": self.id,
                "title": self.title,
                "url": self.url,
                "platform": self.platform,
                "releases": self.releases,
                "developer": self.developer,
                "franchises": self.franchises,
                "user_rating": self.user_rating,
                "user_rating_count": self.user_rating_count,
                "user_difficulty": self.user_difficulty,
                "user_difficulty_count": self.user_difficulty_count,
                "user_length_hours": self.user_length_hours,
                "user_length_hours_count": self.user_length_hours_count,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()
