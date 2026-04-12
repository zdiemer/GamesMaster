from __future__ import annotations

import re
import unidecode
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

from bs4 import BeautifulSoup

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class UniversalVideoGamesListClient(ClientBase):
    supported_platforms: List[ExcelPlatform] = [
        ExcelPlatform._3DO,
        ExcelPlatform.ACORN_ELECTRON,
        ExcelPlatform.ACTION_MAX,
        ExcelPlatform.COMMODORE_AMIGA,
        ExcelPlatform.COMMODORE_AMIGA_CD32,
        ExcelPlatform.AMSTRAD_CPC,
        ExcelPlatform.AMSTRAD_PCW,
        ExcelPlatform.ANDROID,
        ExcelPlatform.APPLE_II,
        ExcelPlatform.APPLE_IIGS,
        ExcelPlatform.APPLE_III,
        ExcelPlatform.BANDAI_PIPPIN,
        ExcelPlatform.ARCADE,
        ExcelPlatform.ACORN_ARCHIMEDES,
        ExcelPlatform.ARDUBOY,
        ExcelPlatform.ATARI_2600,
        ExcelPlatform.ATARI_8_BIT,
        ExcelPlatform.ATARI_5200,
        ExcelPlatform.ATARI_7800,
        ExcelPlatform.ATARI_JAGUAR,
        ExcelPlatform.ATARI_LYNX,
        ExcelPlatform.ATARI_ST,
        ExcelPlatform.ACORN_ATOM,
        ExcelPlatform.BBC_MICRO,
        ExcelPlatform.CASIO_LOOPY,
        ExcelPlatform.PHILIPS_CD_I,
        ExcelPlatform.COLECO_ADAM,
        ExcelPlatform.COLECOVISION,
        ExcelPlatform.COMMODORE_PLUS_4,
        ExcelPlatform.COMMODORE_64,
        ExcelPlatform.COMMODORE_PET,
        ExcelPlatform.DRAGON_32_64,
        ExcelPlatform.SEGA_DREAMCAST,
        ExcelPlatform.DVD_PLAYER,
        ExcelPlatform.ARCADIA_2001,
        ExcelPlatform.EXIDY_SORCERER,
        ExcelPlatform.FAMICOM_DISK_SYSTEM,
        ExcelPlatform.BROWSER,
        ExcelPlatform.FM_TOWNS,
        ExcelPlatform.GAMATE,
        ExcelPlatform.DEDICATED_CONSOLE,
        ExcelPlatform.GAME_BOY,
        ExcelPlatform.GAME_BOY_ADVANCE,
        ExcelPlatform.GAME_BOY_COLOR,
        ExcelPlatform.SEGA_GAME_GEAR,
        ExcelPlatform.NINTENDO_GAMECUBE,
        ExcelPlatform.TIMETOP_GAMEKING,
        ExcelPlatform.GAMEPARK_32,
        ExcelPlatform.GIZMONDO,
        ExcelPlatform.GP2X,
        ExcelPlatform.HARTUNG_GAME_MASTER,
        ExcelPlatform.HYPERSCAN,
        ExcelPlatform.INTELLIVISION,
        ExcelPlatform.IOS,
        ExcelPlatform.PIONEER_LASERACTIVE,
        ExcelPlatform.MAC_OS,
        ExcelPlatform.MAGNAVOX_ODYSSEY_2,
        ExcelPlatform.MAINFRAME,
        ExcelPlatform.SEGA_MASTER_SYSTEM,
        ExcelPlatform.MATTEL_AQUARIUS,
        ExcelPlatform.SEGA_GENESIS,
        ExcelPlatform.FM_7,
        ExcelPlatform.MICROVISION,
        ExcelPlatform.J2ME,
        ExcelPlatform.PC,
        ExcelPlatform.MSX,
        ExcelPlatform.MSX2,
        ExcelPlatform.MSX_TURBO_R,
        ExcelPlatform.N_GAGE,
        ExcelPlatform.NEC_PC_6001,
        ExcelPlatform.NEC_PC_8801,
        ExcelPlatform.NEC_PC_9801,
        ExcelPlatform.SUPERGRAFX,
        ExcelPlatform.NEO_GEO_POCKET,
        ExcelPlatform.NEO_GEO_POCKET_COLOR,
        ExcelPlatform.NEO_GEO,
        ExcelPlatform.NINTENDO_3DS,
        ExcelPlatform.NINTENDO_64,
        ExcelPlatform.NINTENDO_DS,
        ExcelPlatform.NES,
        ExcelPlatform.NINTENDO_SWITCH,
        ExcelPlatform.NINTENDO_SWITCH_2,
        ExcelPlatform.ORIC,
        ExcelPlatform.PLAYDATE,
        ExcelPlatform.PLAYDIA,
        ExcelPlatform.PLAYSTATION,
        ExcelPlatform.PLAYSTATION_2,
        ExcelPlatform.PLAYSTATION_3,
        ExcelPlatform.PLAYSTATION_4,
        ExcelPlatform.PLAYSTATION_5,
        ExcelPlatform.PLAYSTATION_PORTABLE,
        ExcelPlatform.PLAYSTATION_VITA,
        ExcelPlatform.SEGA_SATURN,
        ExcelPlatform.SEGA_32X,
        ExcelPlatform.SEGA_PICO,
        ExcelPlatform.SEGA_SG_1000,
        ExcelPlatform.SEGA_CD,
        ExcelPlatform.SHARP_X1,
        ExcelPlatform.GOOGLE_STADIA,
        ExcelPlatform.SUPER_ACAN,
        ExcelPlatform.EPOCH_SUPER_CASSETTE_VISION,
        ExcelPlatform.SNES,
        ExcelPlatform.TRS_80_COLOR_COMPUTER,
        ExcelPlatform.TI_99_4A,
        ExcelPlatform.GAME_COM,
        ExcelPlatform.R_ZONE,
        ExcelPlatform.VECTREX,
        ExcelPlatform.COMMODORE_VIC_20,
        ExcelPlatform.VIRTUAL_BOY,
        ExcelPlatform.WATARA_SUPERVISION,
        ExcelPlatform.NINTENDO_WII,
        ExcelPlatform.NINTENDO_WII_U,
        ExcelPlatform.WONDERSWAN,
        ExcelPlatform.WONDERSWAN_COLOR,
        ExcelPlatform.SHARP_X68000,
        ExcelPlatform.XBOX,
        ExcelPlatform.XBOX_360,
        ExcelPlatform.XBOX_ONE,
        ExcelPlatform.XBOX_SERIES_X_S,
        ExcelPlatform.ZEEBO,
        ExcelPlatform.ZX_SPECTRUM,
    ]

    def __init__(self, validator: MatchValidator = None, config: Config = None):
        super().__init__(
            validator or MatchValidator(),
            config or Config.create(),
            spoof_headers=True,
            base_url="https://www.uvlist.net",
            immediately_stop_statuses=[403],
        )

    async def search(self, title: str) -> Any:
        return await self.get(
            f"{self.base_url}/globalsearch/", params={"t": title}, json=False
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in self.supported_platforms

    async def get_results(self, game: ExcelGame) -> List[Any]:
        html = await self.search(game.title)
        soup = BeautifulSoup(html, "html.parser")

        games_by_title = soup(string=re.compile(r"Games by title"))

        if not games_by_title or not any(games_by_title):
            return []

        return (
            games_by_title[0]
            .parent.find_next_sibling("div", {"class": "card-body"})
            .find_all("tr")
        )

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        name_elem, year_elem, platform_elem, publisher_elem = result.find_all("td")

        name = name_elem.a.get_text(strip=True)
        url = f"{self.base_url}{name_elem.a['href']}"
        aliases = (
            [a.strip() for a in name_elem.find("small").get_text(strip=True).split(";")]
            if name_elem.find("small")
            else []
        )

        year = None

        if year_elem:
            try:
                year = datetime.strptime(
                    result.find("td", {"class": "text-end"}).get_text(strip=True), "%Y"
                ).year
            except ValueError:
                pass

        platform = platform_elem.get_text(strip=True)
        publisher = publisher_elem.get_text(strip=True) if publisher_elem else None
        if publisher == "?":
            publisher = None

        game_id = int(url.rsplit("/", maxsplit=1)[-1].split("-")[1])

        match = self.validator.validate(game, [name, *aliases], [platform], [year])

        match_info = {
            "name": name,
            "url": url,
            "aliases": aliases,
            "release_year": year,
            "platform": platform,
            "publisher": publisher,
            "game_id": game_id,
        }

        if match.likely_match:
            return GameMatch(
                name,
                url,
                game_id,
                match_info,
                match,
            )

        return None
