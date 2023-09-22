from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal

from bs4 import BeautifulSoup

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelRegion
from game_match import GameMatch
from match_validator import MatchValidator


class Category(Enum):
    FULLY_PLAYABLE = 1
    UNFINISHED = 2
    ADDENDUM = 4


class Platform(Enum):
    _3DO = 46
    ARCADE = 26
    ATARI_2600 = 37
    ATARI_5200 = 42
    ATARI_7800 = 43
    ATARI_JAGUAR = 28
    ATARI_LYNX = 52
    COLECOVISION = 53
    DREAMCAST = 14
    FAMILY_COMPUTER_DISK_SYSTEM = 7
    GAME_BOY = 8
    GAME_BOY_ADVANCE = 10
    MSX = 19
    MULTI_PLATFORM = 25
    NEO_GEO_CD = 15
    NEO_GEO_POCKET_COLOR = 16
    NINTENDO_3DS = 51
    NINTENDO_64 = 27
    NINTENDO_DS = 23
    NINTENDO_ENTERTAINMENT_SYSTEM = 1
    NINTENDO_GAMECUBE = 33
    NOT_APPLICABLE = 24
    PC = 20
    PC_ENGINE_SUPERGRAFX = 45
    PC_6X01 = 35
    PC_8X01 = 2
    PC_98 = 3
    PC_FX = 6
    PHILIPS_CD_I = 50
    PLAYSTATION = 17
    PLAYSTATION_2 = 18
    PLAYSTATION_3 = 47
    PLAYSTATION_PORTABLE = 44
    PLAYSTATION_VITA = 54
    POKEMON_MINI = 41
    SEGA_32X = 31
    SEGA_CD = 29
    SEGA_GAME_GEAR = 12
    SEGA_GENESIS = 11
    SEGA_MASTER_SYSTEM = 22
    SEGA_SATURN = 13
    SG_1000_SC_3000 = 34
    SUPER_NINTENDO = 9
    TURBOGRAFX_16 = 4
    TURBOGRAFX_CD = 5
    VIRTUAL_BOY = 32
    WII = 36
    WII_U = 49
    WONDERSWAN = 21
    X68000 = 30
    XBOX = 38
    XBOX_360 = 48


class Language(Enum):
    ENGLISH = 12


class OrderBy(Enum):
    ASCENDING = 0
    DESCENDING = 1


class RomHackingClient(ClientBase):
    __BASE_ROM_HACKING_URL = "https://www.romhacking.net"

    __PLATFORM_ID_MAPPINGS = {
        "3do": Platform._3DO,
        "arcade": Platform.ARCADE,
        "atari 2600": Platform.ATARI_2600,
        "atari 7800": Platform.ATARI_7800,
        "atari jaguar": Platform.ATARI_JAGUAR,
        "atari lynx": Platform.ATARI_LYNX,
        "colecovision": Platform.COLECOVISION,
        "sega dreamcast": Platform.DREAMCAST,
        "famicom disk system": Platform.FAMILY_COMPUTER_DISK_SYSTEM,
        "game boy": Platform.GAME_BOY,
        "game boy color": Platform.GAME_BOY,
        "game boy advance": Platform.GAME_BOY_ADVANCE,
        "msx": Platform.MSX,
        "msx2": Platform.MSX,
        "neo-geo cd": Platform.NEO_GEO_CD,
        "neo-geo pocket color": Platform.NEO_GEO_POCKET_COLOR,
        "nintendo 3ds": Platform.NINTENDO_3DS,
        "nintendo 64": Platform.NINTENDO_64,
        "nintendo ds": Platform.NINTENDO_DS,
        "nes": Platform.NINTENDO_ENTERTAINMENT_SYSTEM,
        "nintendo gamecube": Platform.NINTENDO_GAMECUBE,
        "pc": Platform.PC,
        "nec pc-8801": Platform.PC_8X01,
        "nec pc-9801": Platform.PC_98,
        "pc-fx": Platform.PC_FX,
        "philips cd-i": Platform.PHILIPS_CD_I,
        "playstation": Platform.PLAYSTATION,
        "playstation 2": Platform.PLAYSTATION_2,
        "playstation 3": Platform.PLAYSTATION_3,
        "playstation portable": Platform.PLAYSTATION_PORTABLE,
        "playstation vita": Platform.PLAYSTATION_VITA,
        "nintendo pokémon mini": Platform.POKEMON_MINI,
        "sega 32x": Platform.SEGA_32X,
        "sega cd": Platform.SEGA_CD,
        "sega game gear": Platform.SEGA_GAME_GEAR,
        "sega genesis": Platform.SEGA_GENESIS,
        "sega master system": Platform.SEGA_MASTER_SYSTEM,
        "sega saturn": Platform.SEGA_SATURN,
        "sega sg-1000": Platform.SG_1000_SC_3000,
        "snes": Platform.SUPER_NINTENDO,
        "turbografx-16": Platform.TURBOGRAFX_16,
        "turbografx-cd": Platform.TURBOGRAFX_CD,
        "virtual boy": Platform.VIRTUAL_BOY,
        "nintendo wii": Platform.WII,
        "wiiware": Platform.WII,
        "nintendo wii u": Platform.WII_U,
        "wonderswan": Platform.WONDERSWAN,
        "wonderswan color": Platform.WONDERSWAN,
        "sharp x68000": Platform.X68000,
        "xbox": Platform.XBOX,
        "xbox 360": Platform.XBOX_360,
    }

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config)

    async def _make_request(self, route: str, params: Dict) -> str:
        return await self.get(
            f"{self.__BASE_ROM_HACKING_URL}/{route}", params=params, json=False
        )

    async def translations(
        self,
        title: str,
        platform: Platform,
        category: Category = None,
        results_per_page: Literal[10, 20, 30, 50, 100, 200] = 200,
        language: Language = Language.ENGLISH,
        sort_by: Literal["", "Title", "Date", "Downloads", "Added"] = "",
        order_by: OrderBy = OrderBy.DESCENDING,
    ) -> str:
        params = {
            "page": "translations",
            "title": title,
            "platform": platform.value,
            "perpage": results_per_page,
            "status": category.value if category is not None else "",
            "languageid": language.value,
            "order": sort_by,
            "dir": order_by.value,
            "transsearch": "Go",
        }

        return await self._make_request("", params)

    def should_skip(self, game: ExcelGame) -> bool:
        return (
            game.release_region in (ExcelRegion.NORTH_AMERICA, ExcelRegion.EUROPE)
            or not game.platform.lower() in self.__PLATFORM_ID_MAPPINGS
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        text = await self.translations(
            game.title, self.__PLATFORM_ID_MAPPINGS[game.platform.lower()]
        )

        soup = BeautifulSoup(text, "html.parser")
        results = soup.find_all("tr", {"class": "even", "class": "odd"})
        matches: List[GameMatch] = []

        for res in results:
            title = res.find("td", {"class": "col_1"})
            name = title.a.text.strip()
            url = title.a["href"]
            released_by = res.find("td", {"class": "col_2"})
            released_by_name = released_by.a.text.strip()
            released_by_url = released_by.a["href"]
            genre = res.find("td", {"class": "col_3"}).text.strip()
            category = Category[
                res.find("td", {"class": "col_5"})
                .text.strip()
                .replace(" ", "_")
                .upper()
            ]
            version = res.find("td", {"class": "col_6"}).text.strip()
            translation_release = datetime.strptime(
                res.find("td", {"class": "col_7"}).text.strip(), "%d %b %Y"
            )

            rh_info = {
                "name": name,
                "url": f"{self.__BASE_ROM_HACKING_URL}{url}",
                "released_by_name": released_by_name,
                "released_by_url": f"{self.__BASE_ROM_HACKING_URL}{released_by_url}",
                "genre": genre,
                "category": category,
                "version": version,
                "translation_release": translation_release,
            }

            match = self.validator.validate(game, name, [game.platform])

            if match.likely_match:
                matches.append(
                    GameMatch(
                        rh_info["name"],
                        rh_info["url"],
                        match_info=rh_info,
                        validation_info=match,
                    )
                )

        return matches
