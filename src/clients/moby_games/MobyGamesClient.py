import asyncio
import html
import json
import re
from typing import Any, Dict, List, Literal

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator
from .moby_games_types import *  # pylint: disable=unused-wildcard-import,wildcard-import


class MobyGamesClient(ClientBase):
    __BASE_MOBYGAMES_SEARCH_URL = "https://api.mobygames.com/v1"
    __api_key: str
    enable_remote: bool

    PLATFORM_TO_MOBY_NAME = {
        ExcelPlatform._3DO: "3DO",
        ExcelPlatform.ACORN_ATOM: "atom",
        ExcelPlatform.ACORN_ARCHIMEDES: "acorn 32-bit",
        ExcelPlatform.RISC_PC: "acorn 32-bit",
        ExcelPlatform.COMMODORE_AMIGA_CD32: "amiga cd32",
        ExcelPlatform.COMMODORE_AMIGA: "amiga",
        ExcelPlatform.AMSTRAD_CPC: "amstrad cpc",
        ExcelPlatform.AMSTRAD_PCW: "amstrad pcw",
        ExcelPlatform.ANDROID: "android",
        ExcelPlatform.APPLE_II: "apple ii",
        ExcelPlatform.APPLE_IIGS: "apple iigs",
        ExcelPlatform.ARCADE: "arcade",
        ExcelPlatform.ARCADIA_2001: "arcadia 2001",
        ExcelPlatform.ARDUBOY: "arduboy",
        ExcelPlatform.ATARI_8_BIT: "atari 8-bit",
        ExcelPlatform.ATARI_2600: "atari 2600",
        ExcelPlatform.ATARI_5200: "atari 5200",
        ExcelPlatform.ATARI_7800: "atari 7800",
        ExcelPlatform.ATARI_ST: "atari st",
        ExcelPlatform.BBC_MICRO: "bbc micro",
        ExcelPlatform.DVD_PLAYER: ["blu-ray disc player", "dvd player"],
        ExcelPlatform.BREW: "brew",
        ExcelPlatform.BROWSER: "browser",
        ExcelPlatform.CASIO_LOOPY: "casio loopy",
        ExcelPlatform.PHILIPS_CD_I: "cd-i",
        ExcelPlatform.COLECO_ADAM: "coleco adam",
        ExcelPlatform.COLECOVISION: "colecovision",
        ExcelPlatform.COMMODORE_PLUS_4: "commodore 16, plus/4",
        ExcelPlatform.COMMODORE_64: "commodore 64",
        ExcelPlatform.COMMODORE_PET: "commodore pet/cbm",
        ExcelPlatform.DEDICATED_CONSOLE: ["dedicated console", "dedicated handheld"],
        ExcelPlatform.DOJA: "doja",
        ExcelPlatform.PC: [
            "dos",
            "windows 3.x",
            "windows 16-bit",
            "windows apps",
            "windows",
        ],
        ExcelPlatform.DRAGON_32_64: "dragon 32/64",
        ExcelPlatform.SEGA_DREAMCAST: "dreamcast",
        ExcelPlatform.ACORN_ELECTRON: "electron",
        ExcelPlatform.EPOCH_SUPER_CASSETTE_VISION: "epoch super cassette vision",
        ExcelPlatform.EVERCADE: "evercade",
        ExcelPlatform.EXEN: "exen",
        ExcelPlatform.EXIDY_SORCERER: "exidy sorcerer",
        ExcelPlatform.AMAZON_FIRE_TV: "fire os",
        ExcelPlatform.FM_TOWNS: "fm towns",
        ExcelPlatform.FM_7: "fm-7",
        ExcelPlatform.GALAKSIJA: "galaksija",
        ExcelPlatform.E_READER: "game boy advance",
        ExcelPlatform.GAME_BOY_ADVANCE: "game boy advance",
        ExcelPlatform.GAME_BOY_COLOR: "game boy color",
        ExcelPlatform.GAME_BOY: "game boy",
        ExcelPlatform.GAME_COM: "game.com",
        ExcelPlatform.SEGA_GAME_GEAR: "game gear",
        ExcelPlatform.NINTENDO_GAMECUBE: "gamecube",
        ExcelPlatform.SEGA_GENESIS: "genesis",
        ExcelPlatform.GIZMONDO: "gizmondo",
        ExcelPlatform.GP2X: "gp2x",
        ExcelPlatform.GP2X_WIZ: "gp2x wiz",
        ExcelPlatform.GAMEPARK_32: "gp32",
        ExcelPlatform.HYPERSCAN: "hyperscan",
        ExcelPlatform.INTELLIVISION: "intellivision",
        ExcelPlatform.IOS: ["ipad", "iphone"],
        ExcelPlatform.IPOD: "ipod classic",
        ExcelPlatform.J2ME: "j2me",
        ExcelPlatform.ATARI_JAGUAR: "jaguar",
        ExcelPlatform.ATARI_JAGUAR_CD: "jaguar",
        ExcelPlatform.PIONEER_LASERACTIVE: "laseractive",
        ExcelPlatform.ATARI_LYNX: "lynx",
        ExcelPlatform.MAC_OS: "macintosh",
        ExcelPlatform.MAINFRAME: "mainframe",
        ExcelPlatform.MATTEL_AQUARIUS: "mattel aquarius",
        ExcelPlatform.MICROVISION: "microvision",
        ExcelPlatform.MOPHUN: "mophun",
        ExcelPlatform.MSX: "msx",
        ExcelPlatform.MSX2: "msx",
        ExcelPlatform.MSX_TURBO_R: "msx",
        ExcelPlatform.N_GAGE: "n-gage",
        ExcelPlatform.N_GAGE_2_0: "n-gage (service)",
        ExcelPlatform.NEO_GEO_CD: "neo geo cd",
        ExcelPlatform.NEO_GEO_POCKET_COLOR: "neo geo pocket color",
        ExcelPlatform.NEO_GEO_POCKET: "neo geo pocket",
        ExcelPlatform.NES: "nes",
        ExcelPlatform.NEW_NINTENDO_3DS: "new nintendo 3ds",
        ExcelPlatform.NINTENDO_3DS: "nintendo 3ds",
        ExcelPlatform.NINTENDO_64: "nintendo 64",
        ExcelPlatform.NINTENDO_DS: "nintendo ds",
        ExcelPlatform.NINTENDO_DSI: "nintendo dsi",
        ExcelPlatform.DSIWARE: "nintendo dsi",
        ExcelPlatform.NINTENDO_SWITCH: "nintendo switch",
        ExcelPlatform.NUON: "nuon",
        ExcelPlatform.MAGNAVOX_ODYSSEY_2: "odyssey 2",
        ExcelPlatform.ORIC: "oric",
        ExcelPlatform.OS_2: "os/2",
        ExcelPlatform.OUYA: "ouya",
        ExcelPlatform.PALM_OS: "palm os",
        ExcelPlatform.NEC_PC_6001: "pc-6001",
        ExcelPlatform.NEC_PC_8801: "pc-88",
        ExcelPlatform.NEC_PC_9801: "pc-98",
        ExcelPlatform.PC_FX: "pc-fx",
        ExcelPlatform.BANDAI_PIPPIN: "pippin",
        ExcelPlatform.PLAYDATE: "playdate",
        ExcelPlatform.PLAYDIA: "playdia",
        ExcelPlatform.PLAYSTATION_2: "playstation 2",
        ExcelPlatform.PLAYSTATION_3: "playstation 3",
        ExcelPlatform.PLAYSTATION_4: "playstation 4",
        ExcelPlatform.PLAYSTATION_5: "playstation 5",
        ExcelPlatform.PLAYSTATION: "playstation",
        ExcelPlatform.NINTENDO_POKEMON_MINI: "pok mon mini",
        ExcelPlatform.PLAYSTATION_VITA: "ps vita",
        ExcelPlatform.PLAYSTATION_PORTABLE: "psp",
        ExcelPlatform.OCULUS_QUEST: "quest",
        ExcelPlatform.SEGA_32X: "sega 32x",
        ExcelPlatform.SEGA_CD: "sega cd",
        ExcelPlatform.SEGA_MASTER_SYSTEM: "sega master system",
        ExcelPlatform.SEGA_PICO: "sega pico",
        ExcelPlatform.SEGA_SATURN: "sega saturn",
        ExcelPlatform.SEGA_SG_1000: "sg-1000",
        ExcelPlatform.SHARP_X1: "sharp x1",
        ExcelPlatform.SHARP_X68000: "sharp x68000",
        ExcelPlatform.SNES: "snes",
        ExcelPlatform.BS_X: "snes",
        ExcelPlatform.GOOGLE_STADIA: "stadia",
        ExcelPlatform.SUPER_ACAN: "super a'can",
        ExcelPlatform.SUPERGRAFX: "supergrafx",
        ExcelPlatform.WATARA_SUPERVISION: "supervision",
        ExcelPlatform.SYMBIAN: "symbian",
        ExcelPlatform.TI_99_4A: "ti-99/4a",
        ExcelPlatform.TRS_80_COLOR_COMPUTER: "trs-80 coco",
        ExcelPlatform.TURBOGRAFX_CD: "turbografx cd",
        ExcelPlatform.TURBOGRAFX_16: "turbografx-16",
        ExcelPlatform.TVOS: "tvos",
        ExcelPlatform.VECTREX: "vectrex",
        ExcelPlatform.COMMODORE_VIC_20: "vic-20",
        ExcelPlatform.VIRTUAL_BOY: "virtual boy",
        ExcelPlatform.WATCHOS: "watchos",
        ExcelPlatform.NINTENDO_WII_U: "wii u",
        ExcelPlatform.NINTENDO_WII: "wii",
        ExcelPlatform.WINDOWS_MOBILE: "windows mobile",
        ExcelPlatform.WINDOWS_PHONE: "windows phone",
        ExcelPlatform.WONDERSWAN_COLOR: "wonderswan color",
        ExcelPlatform.WONDERSWAN: "wonderswan",
        ExcelPlatform.XBOX_360: "xbox 360",
        ExcelPlatform.XBOX_ONE: "xbox one",
        ExcelPlatform.XBOX_SERIES_X_S: "xbox series",
        ExcelPlatform.XBOX: "xbox",
        ExcelPlatform.ZEEBO: "zeebo",
        ExcelPlatform.TAPWAVE_ZODIAC: "zodiac",
        ExcelPlatform.ZX_SPECTRUM: "zx spectrum",
    }

    platform_cache: Dict[str, Any] = {}

    def __init__(
        self,
        validator: MatchValidator,
        config: Config = None,
        rate_limit: RateLimit = None,
        enable_remote: bool = False,
    ):
        config = config or Config.create()
        self.enable_remote = enable_remote

        if not self.enable_remote:
            rate_limit = RateLimit(60, DatePart.SECOND)

        super().__init__(validator, config, rate_limit or RateLimit(360, DatePart.HOUR))
        self.__api_key = self._config.moby_games_api_key

    async def _make_request(self, route: str, params: Dict = None) -> any:
        params = params or {}

        if params.get("api_key") is None:
            params["api_key"] = self.__api_key

        url = f"{self.__BASE_MOBYGAMES_SEARCH_URL}/{route}"

        return await self.get(url, params=params)

    async def genres(self) -> List[Genre]:
        res = await self._make_request("genres")
        return [
            Genre(
                GenreCategory(genre["genre_category"], genre["genre_category_id"]),
                genre["genre_id"],
                genre["genre_name"],
                genre["genre_description"],
            )
            for genre in res["genres"]
        ]

    async def groups(self, limit: int = 100, offset: int = 0) -> List[Group]:
        if limit > 100:
            raise ValueError("limit has a maximum of 100")
        res = await self._make_request("groups", {"limit": limit, "offset": offset})
        return [
            Group(group["group_description"], group["group_id"], group["group_name"])
            for group in res["groups"]
        ]

    async def platforms(self) -> List[Platform]:
        res = await self._make_request("platforms")
        return [
            Platform(platform["platform_id"], platform["platform_name"])
            for platform in res["platforms"]
        ]

    async def game_platforms(self, game_id: int, platform_id: int = None):
        platform_string = f"/{platform_id}" if platform_id is not None else ""
        return await self._make_request(f"games/{game_id}/platforms{platform_string}")

    def json_to_game_local(self, game: Any) -> Game:
        return Game(
            (
                [
                    AlternateTitle(alt["description"], alt["title"])
                    for alt in game["alternate_titles"]
                ]
                if game.get("alternate_titles") is not None
                else []
            ),
            game["description"],
            game["id"],
            [
                Genre(
                    GenreCategory(genre["name"], genre["id"]),
                    genre["id"],
                    genre["name"],
                    genre["description"],
                )
                for genre in game["genres"]
            ],
            game["moby_score"],
            game["moby_url"],
            game["num_votes"],
            game["official_url"],
            [
                GamePlatform(
                    Platform(platform[0]["id"], platform[0]["name"]),
                    platform[1],
                )
                for platform in game["platforms"]
            ],
            (
                Cover(
                    game["sample_cover"]["height"],
                    game["sample_cover"]["image_url"],
                    game["sample_cover"]["platforms"],
                    game["sample_cover"]["thumbnail_image_url"],
                    game["sample_cover"]["width"],
                )
                if game.get("sample_cover") is not None
                else None
            ),
            [
                Screenshot(
                    screenshot["caption"],
                    screenshot["height"],
                    screenshot["image_url"],
                    screenshot["thumbnail_image_url"],
                    screenshot["width"],
                )
                for screenshot in game["sample_screenshots"]
            ],
            html.unescape(game["title"]),
        )

    def json_to_game(self, game: Any) -> Game:
        return Game(
            (
                [
                    AlternateTitle(alt["description"], alt["title"])
                    for alt in game["alternate_titles"]
                ]
                if game.get("alternate_titles") is not None
                else []
            ),
            game["description"],
            game["game_id"],
            [
                Genre(
                    GenreCategory(genre["genre_category"], genre["genre_category_id"]),
                    genre["genre_id"],
                    genre["genre_name"],
                )
                for genre in game["genres"]
            ],
            game["moby_score"],
            game["moby_url"],
            game["num_votes"],
            game["official_url"],
            [
                GamePlatform(
                    Platform(platform["platform_id"], platform["platform_name"]),
                    platform["first_release_date"],
                )
                for platform in game["platforms"]
            ],
            (
                Cover(
                    game["sample_cover"]["height"],
                    game["sample_cover"]["image"],
                    game["sample_cover"]["platforms"],
                    game["sample_cover"]["thumbnail_image"],
                    game["sample_cover"]["width"],
                )
                if game.get("sample_cover") is not None
                else None
            ),
            [
                Screenshot(
                    screenshot["caption"],
                    screenshot["height"],
                    screenshot["image"],
                    screenshot["thumbnail_image"],
                    screenshot["width"],
                )
                for screenshot in game["sample_screenshots"]
            ],
            html.unescape(game["title"]),
        )

    async def games(
        self,
        game_ids: List[int] = None,
        limit: int = 100,
        offset: int = 0,
        platform_ids: List[int] = None,
        genre_ids: List[int] = None,
        group_ids: List[int] = None,
        title: str = "",
        return_format: Literal["id", "brief", "normal"] = "normal",
    ) -> List[Game]:
        res: Dict[str, Any] = await self._make_request(
            "games",
            {
                "id": game_ids or [],
                "limit": limit,
                "offset": offset,
                "platform": platform_ids or [],
                "genre": genre_ids or [],
                "group": group_ids or [],
                "title": title,
                "format": return_format,
            },
        )

        return [self.json_to_game(game) for game in res.get("games") or []]

    @staticmethod
    def platform_to_file_name(platform: str) -> str:
        clean_name = re.sub(r"[^A-Za-z0-9-_]", "_", platform).lower()
        return f"exclusives\\{clean_name}.json"

    def get_games_from_file(self, game: ExcelGame, file_name: str) -> List[Game]:
        exclusive_games: List[Game] = []

        if file_name in self.platform_cache:
            exclusive_games = self.platform_cache[file_name]
        else:
            with open(
                file_name,
                mode="r",
                encoding="utf-8",
            ) as file:
                exclusive_games = [
                    self.json_to_game_local(game) for game in json.load(file)
                ]

                self.platform_cache[file_name] = exclusive_games = list(
                    filter(
                        lambda g: not any(
                            genre.name.lower()
                            in ("add-on", "compilation", "special edition")
                            or genre.category.name.lower()
                            in ("add-on", "special edition")
                            for genre in g.genres
                        ),
                        exclusive_games,
                    )
                )

        return list(
            filter(
                lambda g: self.validator.validate(
                    game,
                    [g.title, *g.alternate_titles],
                    [p.platform.name for p in g.platforms],
                    [int(p.first_release_date[0:4]) for p in g.platforms],
                ),
                exclusive_games,
            )
        )

    async def get_results(self, game: ExcelGame) -> List[Any]:
        if self.enable_remote:
            return await self.games(title=game.title)

        await asyncio.sleep(0.5)
        exclusives_folder = "D:\\Code\\GamePicker"
        moby_name = self.PLATFORM_TO_MOBY_NAME.get(game.platform)
        games: List[Game] = []

        if moby_name is None or game.platform == ExcelPlatform.PC:
            return games

        if isinstance(moby_name, str):
            file_name = f"{exclusives_folder}\\{self.platform_to_file_name(moby_name)}"
            return self.get_games_from_file(game, file_name)

        for name in moby_name:
            file_name = f"{exclusives_folder}\\{self.platform_to_file_name(name)}"
            games.extend(self.get_games_from_file(game, file_name))

        return games

    async def __get_years(self, game_id: int, platform_id: int) -> List[int]:
        game_platforms = await self.game_platforms(game_id, platform_id)

        years = []

        for plat in game_platforms.get("releases") or []:
            if plat.get("release_date") is not None:
                years.append(int(plat["release_date"][0:4]))

        return years

    async def result_to_match(
        self, game: ExcelGame, result: Game, is_fallback: bool = False
    ) -> GameMatch | None:
        if result.platforms is None:
            return None

        platform_names = [p.platform.name for p in result.platforms]
        platform_years = []
        pid = 0

        for plat in result.platforms:
            if self.validator.verify_platform(game.platform, [plat.platform.name]):
                pid = plat.platform.id
                r_date_parts = plat.first_release_date.split("-")
                platform_years.append(int(r_date_parts[0]))

        match = self.validator.validate(
            game, result.title, platform_names, platform_years
        )

        if match.likely_match:
            if not match.date_matched and self.enable_remote:
                match.date_matched = self.validator.verify_release_year(
                    game.release_year, await self.__get_years(result.id, pid)
                )

            return GameMatch(result.title, result.moby_url, result.id, result, match)

        if result.alternate_titles is not None:
            for alt in result.alternate_titles:
                match = self.validator.validate(
                    game, alt.title, platform_names, platform_years
                )

                if match.likely_match:
                    if not match.date_matched and self.enable_remote:
                        match.date_matched = self.validator.verify_release_year(
                            game.release_year, await self.__get_years(result.id, pid)
                        )

                    return GameMatch(
                        result.title, result.moby_url, result.id, result, match
                    )

        return None
