from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

from bs4 import BeautifulSoup

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class VideoGamesMuseumClient(ClientBase):
    __BASE_VG_MUSEUM_URL = "https://www.video-games-museum.com"

    supported_platforms: Dict[ExcelPlatform, str] = {
        ExcelPlatform.ARCADE: "Arcade",
        ExcelPlatform.SEGA_32X: "140",
        ExcelPlatform._3DO: "58",
        ExcelPlatform.ACTION_MAX: "101",
        ExcelPlatform.COMMODORE_AMIGA_CD32: "50",
        ExcelPlatform.ARCADIA_2001: "77",
        ExcelPlatform.ATARI_2600: "76",
        ExcelPlatform.ATARI_5200: "75",
        ExcelPlatform.ATARI_7800: "13",
        ExcelPlatform.GP2X_CAANOO: "9",
        ExcelPlatform.COLECOVISION: "15",
        ExcelPlatform.SEGA_DREAMCAST: "68",
        ExcelPlatform.FAMICOM_DISK_SYSTEM: "16",
        ExcelPlatform.GAMATE: "116",
        ExcelPlatform.GAME_BOY: "17",
        ExcelPlatform.GAME_BOY_COLOR: "143",
        ExcelPlatform.SEGA_GAME_GEAR: "19",
        ExcelPlatform.TIMETOP_GAMEKING: "157",
        ExcelPlatform.TIMETOP_GAMEKING_III: "157",
        ExcelPlatform.HARTUNG_GAME_MASTER: "118",
        ExcelPlatform.GAMEPARK_32: "20",
        ExcelPlatform.GAME_COM: "103",
        ExcelPlatform.GAME_BOY_ADVANCE: "18",
        ExcelPlatform.NINTENDO_GAMECUBE: "62",
        ExcelPlatform.GIZMONDO: "107",
        ExcelPlatform.GP2X: "6",
        ExcelPlatform.HYPERSCAN: "125",
        ExcelPlatform.INTELLIVISION: "21",
        ExcelPlatform.ATARI_JAGUAR: "52",
        ExcelPlatform.ATARI_JAGUAR_CD: "159",
        ExcelPlatform.ATARI_LYNX: "22",
        ExcelPlatform.SEGA_MASTER_SYSTEM: "23",
        ExcelPlatform.SEGA_CD: "24",
        ExcelPlatform.MEGA_DUCK: "117",
        ExcelPlatform.SEGA_GENESIS: "25",
        ExcelPlatform.MICROVISION: "119",
        ExcelPlatform.N_GAGE: "108",
        ExcelPlatform.NEO_GEO: "26",
        ExcelPlatform.NEO_GEO_CD: "60",
        ExcelPlatform.NEO_GEO_POCKET: "27",
        ExcelPlatform.NEO_GEO_POCKET_COLOR: "28",
        ExcelPlatform.NES: "28",
        ExcelPlatform.NINTENDO_3DS: "115",
        ExcelPlatform.NINTENDO_64: "29",
        ExcelPlatform.NINTENDO_DS: "81",
        ExcelPlatform.NINTENDO_DSI: "134",
        ExcelPlatform.DSIWARE: "134",
        ExcelPlatform.NUON: "136",
        ExcelPlatform.MAGNAVOX_ODYSSEY_2: "55",
        ExcelPlatform.TURBOGRAFX_16: "30",
        ExcelPlatform.TURBOGRAFX_CD: "45",
        ExcelPlatform.PC_FX: "83",
        ExcelPlatform.PHILIPS_CD_I: "88",
        ExcelPlatform.SEGA_PICO: "104",
        ExcelPlatform.BANDAI_PIPPIN: "111",
        ExcelPlatform.PLAYSTATION: "31",
        ExcelPlatform.PLAYSTATION_2: "80",
        ExcelPlatform.PLAYSTATION_3: "121",
        ExcelPlatform.PLAYSTATION_4: "114",
        ExcelPlatform.NINTENDO_POKEMON_MINI: "8",
        ExcelPlatform.PLAYSTATION_VITA: "102",
        ExcelPlatform.PLAYSTATION_PORTABLE: "89",
        ExcelPlatform.EPOCH_SUPER_CASSETTE_VISION: "110",
        ExcelPlatform.SEGA_SATURN: "51",
        ExcelPlatform.SEGA_SG_1000: "141",
        ExcelPlatform.SUPER_ACAN: "100",
        ExcelPlatform.SNES: "33",
        ExcelPlatform.BS_X: "33",
        ExcelPlatform.NINTENDO_SWITCH: "129",
        ExcelPlatform.VECTREX: "73",
        ExcelPlatform.VIRTUAL_BOY: "35",
        ExcelPlatform.NINTENDO_WII: "93",
        ExcelPlatform.WIIWARE: "93",
        ExcelPlatform.NINTENDO_WII_U: "106",
        ExcelPlatform.WONDERSWAN: "36",
        ExcelPlatform.WONDERSWAN_COLOR: "36",
        ExcelPlatform.XBOX: "59",
        ExcelPlatform.XBOX_360: "109",
        ExcelPlatform.TAPWAVE_ZODIAC: "105",
        ExcelPlatform.COMMODORE_AMIGA: "82",
        ExcelPlatform.AMSTRAD_CPC: "38",
        ExcelPlatform.APPLE_II: "37",
        ExcelPlatform.APPLE_IIGS: "133",
        ExcelPlatform.MATTEL_AQUARIUS: "139",
        ExcelPlatform.ACORN_ARCHIMEDES: "153",
        ExcelPlatform.ATARI_ST: "54",
        ExcelPlatform.ACORN_ATOM: "155",
        ExcelPlatform.COMMODORE_PET: "67",
        ExcelPlatform.COMMODORE_VIC_20: "161",
        ExcelPlatform.EXIDY_SORCERER: "64",
        ExcelPlatform.FM_TOWNS: "90",
        ExcelPlatform.FM_7: "130",
        ExcelPlatform.MSX: "49",
        ExcelPlatform.MSX_TURBO_R: "72",
        ExcelPlatform.MSX2: "46",
        ExcelPlatform.ORIC: "97",
        ExcelPlatform.MAINFRAME: "44",
        ExcelPlatform.SHARP_X1: "65",
        ExcelPlatform.SHARP_X68000: "63",
        ExcelPlatform.DEDICATED_CONSOLE: "92",
        ExcelPlatform.J2ME: "91",
        ExcelPlatform.DOJA: "91",
        ExcelPlatform.MOPHUN: "91",
        ExcelPlatform.EXEN: "91",
    }

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, spoof_headers=True)

    async def search(self, game: ExcelGame, page: int = 0) -> AsyncGenerator[Any]:
        return await self.get(
            f"{self.__BASE_VG_MUSEUM_URL}/en/search/{game.title.replace('/', '').replace(':', ' - ').replace('%', '')}/{self.supported_platforms[game.platform]}/all/{page}",
            params={"systeme_affichage": "liste"},
            json=False,
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in self.supported_platforms

    async def get_results_paginated(
        self, game: ExcelPlatform
    ) -> AsyncGenerator[List[Any]]:
        page = 0
        html = await self.search(game, page)
        soup = BeautifulSoup(html, "html.parser")
        _next = soup.find("li", {"class": "next"})
        table = soup.find("table", {"id": "simple-example-table"})

        if table is None:
            yield []
        else:
            yield table.find_all("tr", {"class": None})

        while (
            _next is not None
            and _next.has_attr("class")
            and not any("disabled" in c for c in _next["class"])
        ):
            table = soup.find("table", {"id": "simple-example-table"})
            yield table.find_all("tr", {"class": None})

            page += 1

            html = await self.search(game, page)
            soup = BeautifulSoup(html, "html.parser")
            _next = soup.find("li", {"class": "next"})

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        title, _, year, genre = result.find_all("td")

        if year.text.strip() == "????":
            year = None
        else:
            year = datetime.strptime(year.text.strip(), "%Y").year

        match = self.validator.validate(
            game, title.text.strip(), [game.platform.value], [year]
        )

        match_data = {
            "title": title.text.strip(),
            "year": year,
            "genre": genre.text.strip(),
            "url": f"{self.__BASE_VG_MUSEUM_URL}{title.a['href']}",
        }

        match_data["boxarts_url"] = f"{match_data['url']}/boxarts"
        match_data["credits_url"] = f"{match_data['url']}/credits"
        match_data["reviews_url"] = f"{match_data['url']}/reviews"
        match_data["faqs_url"] = f"{match_data['url']}/faqs"
        match_data["cheats_url"] = f"{match_data['url']}/cheats"
        match_data["buy_url"] = f"{match_data['url']}/buy"

        if match.likely_match:
            html = await self.get(
                match_data["url"],
                json=False,
            )

            soup = BeautifulSoup(html, "html.parser")

            alternate_titles = soup.find("div", {"id": "titres_alternatifs"})
            if alternate_titles is not None:
                match_data["alternate_titles"] = [
                    title.text.strip() for title in alternate_titles.find_all("li")
                ]

            developer = soup.find("div", {"itemprop": "author"})
            if developer is not None:
                match_data["developer"] = developer.text.strip()

            num_players = soup.find("div", {"itemprop": "numberOfPlayers"})
            if num_players is not None:
                match_data["num_players"] = num_players.text.strip()

            franchise = soup.find("a", {"class": "lien_noir"})
            if franchise is not None:
                match_data["franchise"] = franchise.text.strip()
                match_data["franchise_url"] = (
                    f"{self.__BASE_VG_MUSEUM_URL}{franchise['href']}"
                )

            metadata = soup.find("div", {"class": "jeu_infos"})
            if metadata is not None:
                meta_children = metadata.find_all("div") or []
                for meta in meta_children:
                    meta_text = meta.text.strip()

                    if "Wikipedia :" in meta_text:
                        match_data["wikipedia"] = meta.a["href"]
                    elif "Youtube :" in meta_text:
                        match_data["youtube"] = meta.a["href"]
                    elif "Manuals :" in meta_text:
                        match_data["manuals"] = meta.a["href"]

            return GameMatch(
                match_data["title"],
                match_data["url"],
                match_data["url"].rsplit("/", maxsplit=1)[-1],
                match_data,
                match,
            )

        return None
