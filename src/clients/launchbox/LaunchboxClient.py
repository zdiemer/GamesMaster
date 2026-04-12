from __future__ import annotations

import urllib.parse
from datetime import datetime
from typing import Any, AsyncGenerator, List

from bs4 import BeautifulSoup

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class LaunchboxClient(ClientBase):
    supported_platforms: List[ExcelPlatform] = [
        ExcelPlatform._3DO,
        ExcelPlatform.ACORN_ARCHIMEDES,
        ExcelPlatform.ACORN_ATOM,
        ExcelPlatform.ACORN_ELECTRON,
        ExcelPlatform.AMSTRAD_CPC,
        ExcelPlatform.ANDROID,
        ExcelPlatform.APPLE_II,
        ExcelPlatform.APPLE_IIGS,
        ExcelPlatform.IOS,
        ExcelPlatform.MAC_OS,
        ExcelPlatform.ARCADE,
        ExcelPlatform.ATARI_2600,
        ExcelPlatform.ATARI_5200,
        ExcelPlatform.ATARI_7800,
        ExcelPlatform.ATARI_8_BIT,
        ExcelPlatform.ATARI_JAGUAR,
        ExcelPlatform.ATARI_JAGUAR_CD,
        ExcelPlatform.ATARI_LYNX,
        ExcelPlatform.ATARI_ST,
        ExcelPlatform.BBC_MICRO,
        ExcelPlatform.CASIO_LOOPY,
        ExcelPlatform.COLECO_ADAM,
        ExcelPlatform.COLECOVISION,
        ExcelPlatform.COMMODORE_64,
        ExcelPlatform.COMMODORE_AMIGA,
        ExcelPlatform.COMMODORE_AMIGA_CD32,
        ExcelPlatform.COMMODORE_PET,
        ExcelPlatform.COMMODORE_PLUS_4,
        ExcelPlatform.COMMODORE_VIC_20,
        ExcelPlatform.DRAGON_32_64,
        ExcelPlatform.ARCADIA_2001,
        ExcelPlatform.EPOCH_SUPER_CASSETTE_VISION,
        ExcelPlatform.EXIDY_SORCERER,
        ExcelPlatform.FM_TOWNS,
        ExcelPlatform.FM_7,
        ExcelPlatform.SUPER_ACAN,
        ExcelPlatform.GAMEPARK_32,
        ExcelPlatform.VECTREX,
        ExcelPlatform.HARTUNG_GAME_MASTER,
        ExcelPlatform.MAGNAVOX_ODYSSEY_2,
        ExcelPlatform.MATTEL_AQUARIUS,
        ExcelPlatform.HYPERSCAN,
        ExcelPlatform.MEGA_DUCK,
        ExcelPlatform.MSX,
        ExcelPlatform.MSX2,
        ExcelPlatform.MSX_TURBO_R,
        ExcelPlatform.XBOX,
        ExcelPlatform.XBOX_360,
        ExcelPlatform.XBOX_ONE,
        ExcelPlatform.XBOX_SERIES_X_S,
        ExcelPlatform.PC,
        ExcelPlatform.NEC_PC_8801,
        ExcelPlatform.NEC_PC_9801,
        ExcelPlatform.PC_FX,
        ExcelPlatform.TURBOGRAFX_16,
        ExcelPlatform.TURBOGRAFX_CD,
        ExcelPlatform.NINTENDO_3DS,
        ExcelPlatform.NINTENDO_64,
        ExcelPlatform.NINTENDO_64DD,
        ExcelPlatform.NINTENDO_DS,
        ExcelPlatform.NES,
        ExcelPlatform.FAMICOM_DISK_SYSTEM,
        ExcelPlatform.DEDICATED_CONSOLE,
        ExcelPlatform.GAME_BOY,
        ExcelPlatform.GAME_BOY_ADVANCE,
        ExcelPlatform.GAME_BOY_COLOR,
        ExcelPlatform.NINTENDO_GAMECUBE,
        ExcelPlatform.NINTENDO_POKEMON_MINI,
        ExcelPlatform.BS_X,
        ExcelPlatform.NINTENDO_SWITCH,
        ExcelPlatform.NINTENDO_SWITCH_2,
        ExcelPlatform.VIRTUAL_BOY,
        ExcelPlatform.NINTENDO_WII,
        ExcelPlatform.WIIWARE,
        ExcelPlatform.NINTENDO_WII_U,
        ExcelPlatform.N_GAGE,
        ExcelPlatform.NUON,
        ExcelPlatform.ORIC,
        ExcelPlatform.OUYA,
        ExcelPlatform.SUPERGRAFX,
        ExcelPlatform.SEGA_32X,
        ExcelPlatform.SEGA_CD,
        ExcelPlatform.SEGA_DREAMCAST,
        ExcelPlatform.SEGA_GAME_GEAR,
        ExcelPlatform.SEGA_GENESIS,
        ExcelPlatform.SEGA_MASTER_SYSTEM,
        ExcelPlatform.SEGA_PICO,
        ExcelPlatform.SEGA_SATURN,
        ExcelPlatform.SEGA_SG_1000,
        ExcelPlatform.SHARP_X1,
        ExcelPlatform.SHARP_X68000,
        ExcelPlatform.ZX_SPECTRUM,
        ExcelPlatform.NEO_GEO,
        ExcelPlatform.NEO_GEO_CD,
        ExcelPlatform.NEO_GEO_POCKET,
        ExcelPlatform.NEO_GEO_POCKET_COLOR,
        ExcelPlatform.PLAYSTATION,
        ExcelPlatform.PLAYSTATION_2,
        ExcelPlatform.PLAYSTATION_3,
        ExcelPlatform.PLAYSTATION_4,
        ExcelPlatform.PLAYSTATION_5,
        ExcelPlatform.PLAYSTATION_VITA,
        ExcelPlatform.PLAYSTATION_PORTABLE,
        ExcelPlatform.SNES,
        ExcelPlatform.TRS_80_COLOR_COMPUTER,
        ExcelPlatform.TAPWAVE_ZODIAC,
        ExcelPlatform.TI_99_4A,
        ExcelPlatform.GAME_COM,
        ExcelPlatform.WATARA_SUPERVISION,
        ExcelPlatform.BROWSER,
        ExcelPlatform.WONDERSWAN,
        ExcelPlatform.WONDERSWAN_COLOR,
        ExcelPlatform.ACTION_MAX,
    ]

    api_url: str = "https://api.gamesdb.launchbox-app.com/api"

    def __init__(self, validator: MatchValidator = None, config: Config = None):
        super().__init__(
            validator or MatchValidator(),
            config or Config.create(),
            spoof_headers=True,
            base_url="https://gamesdb.launchbox-app.com",
            limit=RateLimit(45, DatePart.MINUTE),
            immediately_stop_statuses=[429],
        )

    async def search(self, title: str, page: int = 1) -> Any:
        return await self.get(
            f"{self.base_url}/games/results/{urllib.parse.quote(title.replace('/', '').replace(':', ''))}|{page}",
            json=False,
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in self.supported_platforms

    async def get_results_paginated(self, game: ExcelGame) -> AsyncGenerator[List[Any]]:
        max_pages = 3
        page = 1
        while page <= max_pages:
            html = await self.search(game.normal_title, page)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")

            if soup.find("h1", {"class": "empty-games-list"}):
                break

            yield soup.find_all("div", {"class": "games-grid-card"})
            page += 1

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        card_content = result.find("div", {"class": "cardContent"})

        if not card_content:
            return None

        card_title = card_content.find("div", {"class": "cardTitle"})

        name = card_title.h3.get_text(strip=True)
        platform = card_title.p.get_text(strip=True)

        release_date_str = card_content.find(
            "div", {"class": "releaseDate"}
        ).h5.get_text(strip=True)

        release_date = None
        if release_date_str:
            try:
                release_date = datetime.strptime(release_date_str, "%Y")
            except ValueError:
                pass

            try:
                release_date = datetime.strptime(release_date_str, "%B %d, %Y")
            except ValueError:
                pass

        match = self.validator.validate(
            game, name, [platform], [release_date.year if release_date else None]
        )

        if match.likely_match or is_fallback:
            url = f"{self.api_url}{result.find('a', {'class': 'list-item link-no-underline'})['href']}"

            game_details = await self.get(url)

            match = self.validator.validate(
                game,
                [
                    game_details["name"],
                    *[alt["name"] for alt in game_details["gameAlternateNames"]],
                ],
                [game_details["platform"]["name"]],
                [
                    self.try_parse_date_year(game_details["releaseDate"]),
                    game_details["releaseYear"],
                ],
                [pub["name"] for pub in game_details["gamePublishers"]],
                [dev["name"] for dev in game_details["gameDevelopers"]],
            )

            if match.likely_match:
                return GameMatch(
                    game_details["name"],
                    url.replace("api.", "").replace("/api/", "/"),
                    game_details["gameKey"],
                    game_details,
                    match,
                )

        return None
