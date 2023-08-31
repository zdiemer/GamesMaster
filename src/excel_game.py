from enum import Enum
import pandas as pd


class ExcelRegion(Enum):
    ASIA = "AS"
    GERMANY = "DE"
    EUROPE = "EU"
    FRANCE = "FR"
    JAPAN = "JP"
    KOREA = "KO"
    NORTH_AMERICA = "NA"


class ExcelGame:
    title: str
    platform: str
    release_date: pd.DatetimeIndex
    release_region: ExcelRegion
    publisher: str
    developer: str
    franchise: str
    genre: str
    notes: str

    def __init__(
        self,
        title: str,
        platform: str,
        release_date: pd.DatetimeIndex,
        release_region: ExcelRegion,
        publisher: str,
        developer: str,
        franchise: str,
        genre: str,
        notes: str,
    ):
        self.title = title
        self.platform = platform
        self.release_date = release_date
        self.release_region = release_region
        self.publisher = publisher
        self.developer = developer
        self.franchise = franchise
        self.genre = genre
        self.notes = notes
