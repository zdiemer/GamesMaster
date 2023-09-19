from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup

from clients.ClientBase import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator, ValidationInfo


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


class GameFaqsClient(ClientBase):
    __BASE_GAMEFAQS_URL = "https://gamefaqs.gamespot.com"
    __PLATFORM_TO_URL_PART = {
        "3do": "3do",
        "amstrad cpc": "cpc",
        "android": "android",
        "apple ii": "appleii",
        "arcade": "arcade",
        "atari 2600": "atari2600",
        "atari 7800": "atari7800",
        "atari 8-bit": "atari8bit",
        "atari jaguar": "jaguar",
        "atari lynx": "lynx",
        "atari st": "ast",
        "bbc micro": "bbc",
        "bs-x": "snes",
        "browser": "webonly",
        "colecovision": "colecovision",
        "commodore 64": "c64",
        "commodore amiga": "amiga",
        "commodore amiga cd32": "cd32",
        "commodore vic-20": "vic20",
        "dsiware": "ds",
        "dedicated console": "dedicated",
        "epoch super cassette vision": "scv",
        "fm towns": "fmtowns",
        "fm-7": "fm7",
        "famicom disk system": "famicomds",
        "game boy": "gameboy",
        "game boy advance": "gba",
        "game boy color": "gbc",
        "game.com": "game.com",
        "gamepark 32": "gp32",
        "google stadia": "stadia",
        "intellivision": "intellivision",
        "j2me": "mobile",
        "msx": "msx",
        "msx2": "msx",
        "mac os": "mac",
        "n-gage": "ngage",
        "n-gage 2.0": "ngage",
        "nec pc-8801": "pc88",
        "nec pc-9801": "pc98",
        "nes": "nes",
        "neo-geo": "neo",
        "neo-geo cd": "neogeocd",
        "neo-geo pocket": "ngpocket",
        "neo-geo pocket color": "ngpc",
        "new nintendo 3ds": "3ds",
        "nintendo 3ds": "3ds",
        "nintendo 64": "n64",
        "nintendo 64dd": "n64dd",
        "nintendo ds": "ds",
        "nintendo dsi": "ds",
        "nintendo gamecube": "gamecube",
        "nintendo pokémon mini": "pokemon-mini",
        "nintendo switch": "switch",
        "nintendo wii": "wii",
        "nintendo wii u": "wiiu",
        "oculus quest": "oculusquest",
        "ouya": "ouya",
        "pc": "pc",
        "pc-fx": "pcfx",
        "pdp-10": "pc",
        "philips cd-i": "cdi",
        "pioneer laseractive": "laser",
        "playstation": "ps",
        "playstation 2": "ps2",
        "playstation 3": "ps3",
        "playstation 4": "ps4",
        "playstation 5": "ps5",
        "playstation portable": "psp",
        "playstation vita": "vita",
        "playdate": "playdate",
        "snes": "snes",
        "sega 32x": "sega32x",
        "sega cd": "segacd",
        "sega dreamcast": "dreamcast",
        "sega game gear": "gamegear",
        "sega genesis": "genesis",
        "sega master system": "sms",
        "sega sg-1000": "sg1000",
        "sega saturn": "saturn",
        "sharp x1": "x1",
        "sharp x68000": "x68000",
        "turbografx-16": "tg16",
        "turbografx-cd": "turbocd",
        "vectrex": "vectrex",
        "virtual boy": "virtualboy",
        "watara supervision": "svision",
        "wiiware": "wii",
        "wonderswan": "wonderswan",
        "wonderswan color": "wsc",
        "xbox": "xbox",
        "xbox 360": "xbox360",
        "xbox one": "xboxone",
        "xbox series x|s": "xbox-series-x",
        "zx spectrum": "sinclair",
        "zeebo": "zeebo",
        "ios": "iphone",
    }

    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config, RateLimit(2, DatePart.MINUTE), spoof_headers=True)

    async def _make_request(
        self, route: str, params: Dict = None, as_json: bool = True
    ):
        url = f"{self.__BASE_GAMEFAQS_URL}/{route}"
        return await self.get(url, params=params, json=as_json)

    async def home_game_search(self, term: str):
        return await self._make_request("ajax/home_game_search", {"term": term})

    async def game_page(self, url: str):
        return await self._make_request(url, as_json=False)

    async def release_data_page(self, url: str):
        return await self._make_request(f"{url}/data", as_json=False)

    async def get_gamefaqs_game(self, match: Dict, platform: str) -> GameFaqsGame:
        url = match["board_url"].replace(
            "boards", self.__PLATFORM_TO_URL_PART[platform.lower()]
        )[1:]

        html_doc = await self.game_page(url)

        soup = BeautifulSoup(html_doc, "html.parser")
        game_info = soup.find("div", {"class": "pod_gameinfo"})
        infos = game_info.find_all("div", {"class": "content"})

        gf_game = GameFaqsGame()
        gf_game.id = int(match["game_id"])
        gf_game.url = f"{self.__BASE_GAMEFAQS_URL}{url}"
        gf_game.title = soup.find("h1", {"class": "page-title"}).text.strip()

        for i in infos:
            label = i.b.text.strip()
            if label == "Platform:":
                gf_game.platform = GameFaqsPlatform(i.a.text.strip())
            elif label == "Genre:":
                genre_parts = [GameFaqsGenre(g.text.strip()) for g in i.find_all("a")]
                idx = len(genre_parts) - 1
                while idx > 0:
                    genre_parts[idx].parent_genre = genre_parts[idx - 1]
                    idx -= 1
                gf_game.genre = genre_parts[-1]
            elif label == "Franchises:":
                gf_game.franchises = [
                    GameFaqsFranchise(f.text.strip()) for f in i.find_all("a")
                ]
            elif label in ["Developer:", "Developer/Publisher:"]:
                gf_game.developer = GameFaqsCompany(i.a.text.strip())

        rating_child = soup.find(id="gs_rate_avg")
        if rating_child is not None:
            empty_title = "Average: 0 stars from  users"
            rating_elem = rating_child.parent
            if rating_elem["title"] != empty_title:
                results = re.search(
                    r"(?P<rating>[0-9]+(\.[0-9]+)*) stars* from (?P<count>[0-9]+) users",
                    rating_elem["title"],
                )
                gf_game.user_rating = float(results.group("rating"))
                gf_game.user_rating_count = int(results.group("count"))

        difficulty_child = soup.find(id="gs_difficulty_avg")
        if difficulty_child is not None:
            difficulty_elem = difficulty_child.parent
            empty_title = "Average: 0 hearts from  users"
            if difficulty_elem["title"] != empty_title:
                results = re.search(
                    r"(?P<rating>[0-9]+(\.[0-9]+)*) hearts* from (?P<count>[0-9]+) users",
                    difficulty_elem["title"],
                )
                gf_game.user_difficulty = float(results.group("rating"))
                gf_game.user_difficulty_count = int(results.group("count"))

        length_child = soup.find(id="gs_length_avg_hint")
        if length_child is not None:
            length_elem = length_child.parent
            empty_title = "Average: 0 hours from  users"
            if length_elem["title"] != empty_title:
                results = re.search(
                    r"(?P<rating>[0-9]+(\.[0-9]+)*) hours* from (?P<count>[0-9]+) users",
                    length_elem["title"],
                )
                gf_game.user_length_hours = float(results.group("rating"))
                gf_game.user_length_hours_count = int(results.group("count"))

        html_doc = await self.release_data_page(url)
        soup = BeautifulSoup(html_doc, "html.parser")
        release_elems = soup.find("table", {"class": "rdates"}).tbody.find_all("tr")

        releases: List[GameFaqsRelease] = []

        for i in range(0, len(release_elems), 2):
            release = GameFaqsRelease()
            if i + 1 > len(release_elems) - 1:
                break
            release.title = release_elems[i].find("td", {"class": "bold"}).text.strip()
            for idx, td in enumerate(release_elems[i + 1].find_all("td")):
                value = td.text.strip()
                if value == "&nbsp;":
                    continue
                if idx == 0:
                    release.release_region = GameFaqsRegion(value)
                elif idx == 1:
                    release.publisher = GameFaqsCompany(td.a.text.strip())
                elif idx == 2:
                    release.product_id = value
                elif idx == 3:
                    release.distribution_or_barcode = value
                elif idx == 4:
                    if len(value) == 4:
                        release.release_year = int(value)
                    elif "/" in value:
                        date: datetime = datetime.strptime(value, "%m/%d/%y")
                        release.release_day = date.day
                        release.release_month = date.month
                        release.release_year = date.year
                    elif value == "Canceled":
                        release.status = GameFaqsReleaseStatus.CANCELED
                    elif value == "TBA":
                        release.status = GameFaqsReleaseStatus.UNRELEASED
                    else:
                        date: datetime = datetime.strptime(value, "%B %Y")
                        release.release_month = date.month
                        release.release_year = date.year
                elif idx == 5:
                    release.age_rating = value

            releases.append(release)

        gf_game.releases = releases

        return gf_game

    async def match_game(
        self, game: ExcelGame
    ) -> List[Tuple[GameMatch, ValidationInfo]]:
        results = await self.home_game_search(game.title)
        matches: List[Tuple[GameMatch, ValidationInfo]] = []
        validator = MatchValidator()

        for r in results:
            if r.get("footer"):
                continue
            if r.get("game_name") and r.get("plats"):
                match = validator.validate(game, r["game_name"], r["plats"].split(", "))
                if match.matched:
                    gf_game = await self.get_gamefaqs_game(r, game.platform)
                    if validator.verify_release_year(
                        game.release_date.year,
                        [
                            rel.release_year
                            for rel in filter(
                                # Filter unreleased games
                                lambda _rel: _rel.status
                                == GameFaqsReleaseStatus.RELEASED,
                                gf_game.releases,
                            )
                        ],
                    ):
                        matches.append(
                            (
                                GameMatch(
                                    gf_game.title, gf_game.url, gf_game.id, gf_game
                                ),
                                match,
                            )
                        )

        return matches
