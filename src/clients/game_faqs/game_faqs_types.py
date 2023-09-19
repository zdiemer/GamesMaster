from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional


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


class GameFaqsGuide:
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
        return str(
            {
                "title": self.title,
                "url": self.url,
                "author_name": self.author_name,
                "author_url": self.author_url,
                "version": self.version,
                "updated_date": self.updated_date,
                "full_text": self.full_text,
                "platform": self.platform,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()


class GameFaqsGame:
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
                "guides": self.guides,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()
