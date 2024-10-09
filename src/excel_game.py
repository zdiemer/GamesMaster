"""Models for mapping Excel rows to Game objects.

This file contains classes which are meant to wrap the contents
of the Excel file.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import statistics
from enum import Enum
from typing import Any, get_args, List, Literal, Optional

import roman
from unidecode import unidecode


class ExcelRegion(Enum):
    """Release regions for games"""

    ASIA = "AS"
    BRAZIL = "BR"
    GERMANY = "DE"
    EUROPE = "EU"
    FRANCE = "FR"
    JAPAN = "JP"
    KOREA = "KO"
    NORTH_AMERICA = "NA"
    SPAIN = "SP"
    TAIWAN = "TW"
    ITALY = "IT"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class ExcelPlatform(Enum):
    _3DO = "3DO"
    ACORN_ARCHIMEDES = "Acorn Archimedes"
    ACORN_ELECTRON = "Acorn Electron"
    ACTION_MAX = "Action Max"
    AMSTRAD_CPC = "Amstrad CPC"
    ANDROID = "Android"
    APPLE_II = "Apple II"
    ARCADE = "Arcade"
    ATARI_2600 = "Atari 2600"
    ATARI_5200 = "Atari 5200"
    ATARI_7800 = "Atari 7800"
    ATARI_8_BIT = "Atari 8-bit"
    ATARI_JAGUAR = "Atari Jaguar"
    ATARI_JAGUAR_CD = "Atari Jaguar CD"
    ATARI_LYNX = "Atari Lynx"
    ATARI_ST = "Atari ST"
    BBC_MICRO = "BBC Micro"
    BREW = "BREW"
    BROWSER = "Browser"
    BS_X = "BS-X"
    COLECOVISION = "ColecoVision"
    COMMODORE_64 = "Commodore 64"
    COMMODORE_AMIGA = "Commodore Amiga"
    COMMODORE_AMIGA_CD32 = "Commodore Amiga CD32"
    COMMODORE_PLUS_4 = "Commodore Plus/4"
    COMMODORE_VIC_20 = "Commodore VIC-20"
    DEDICATED_CONSOLE = "Dedicated Console"
    DSIWARE = "DSiWare"
    EPOCH_SUPER_CASSETTE_VISION = "Epoch Super Cassette Vision"
    FAMICOM_DISK_SYSTEM = "Famicom Disk System"
    FM_TOWNS = "FM Towns"
    FM_7 = "FM-7"
    GAME_BOY = "Game Boy"
    GAME_BOY_ADVANCE = "Game Boy Advance"
    GAME_BOY_COLOR = "Game Boy Color"
    GAME_COM = "Game.com"
    GAMEPARK_32 = "GamePark 32"
    GIZMONDO = "Gizmondo"
    GOOGLE_STADIA = "Google Stadia"
    INTELLIVISION = "Intellivision"
    IOS = "iOS"
    J2ME = "J2ME"
    MAC_OS = "Mac OS"
    MSX = "MSX"
    MSX_TURBO_R = "MSX Turbo R"
    MSX2 = "MSX2"
    N_GAGE = "N-Gage"
    N_GAGE_2_0 = "N-Gage 2.0"
    NEC_PC_6001 = "NEC PC-6001"
    NEC_PC_8801 = "NEC PC-8801"
    NEC_PC_9801 = "NEC PC-9801"
    NEO_GEO = "Neo-Geo"
    NEO_GEO_CD = "Neo-Geo CD"
    NEO_GEO_POCKET = "Neo-Geo Pocket"
    NEO_GEO_POCKET_COLOR = "Neo-Geo Pocket Color"
    NES = "NES"
    NEW_NINTENDO_3DS = "New Nintendo 3DS"
    NINTENDO_3DS = "Nintendo 3DS"
    NINTENDO_64 = "Nintendo 64"
    NINTENDO_64DD = "Nintendo 64DD"
    NINTENDO_DS = "Nintendo DS"
    NINTENDO_DSI = "Nintendo DSi"
    NINTENDO_GAMECUBE = "Nintendo GameCube"
    NINTENDO_POKEMON_MINI = "Nintendo Pokémon mini"
    NINTENDO_SWITCH = "Nintendo Switch"
    NINTENDO_WII = "Nintendo Wii"
    NINTENDO_WII_U = "Nintendo Wii U"
    OCULUS_QUEST = "Oculus Quest"
    OUYA = "Ouya"
    PC = "PC"
    PC_FX = "PC-FX"
    PDP_10 = "PDP-10"
    PHILIPS_CD_I = "Philips CD-i"
    PIONEER_LASERACTIVE = "Pioneer LaserActive"
    PLAYDATE = "Playdate"
    PLAYSTATION = "PlayStation"
    PLAYSTATION_2 = "PlayStation 2"
    PLAYSTATION_3 = "PlayStation 3"
    PLAYSTATION_4 = "PlayStation 4"
    PLAYSTATION_5 = "PlayStation 5"
    PLAYSTATION_NETWORK = "PlayStation Network"
    PLAYSTATION_PORTABLE = "PlayStation Portable"
    PLAYSTATION_VITA = "PlayStation Vita"
    RISC_PC = "Risc PC"
    SEGA_32X = "Sega 32X"
    SEGA_CD = "Sega CD"
    SEGA_DREAMCAST = "Sega Dreamcast"
    SEGA_GAME_GEAR = "Sega Game Gear"
    SEGA_GENESIS = "Sega Genesis"
    SEGA_MASTER_SYSTEM = "Sega Master System"
    SEGA_SATURN = "Sega Saturn"
    SEGA_SG_1000 = "Sega SG-1000"
    SHARP_X1 = "Sharp X1"
    SHARP_X68000 = "Sharp X68000"
    SNES = "SNES"
    SUPERGRAFX = "SuperGrafx"
    TAPWAVE_ZODIAC = "Tapwave Zodiac"
    TRS_80_COLOR_COMPUTER = "TRS-80 Color Computer"
    TURBOGRAFX_16 = "TurboGrafx-16"
    TURBOGRAFX_CD = "TurboGrafx-CD"
    TVOS = "tvOS"
    VECTREX = "Vectrex"
    VIRTUAL_BOY = "Virtual Boy"
    WATARA_SUPERVISION = "Watara SuperVision"
    WATCHOS = "watchOS"
    WIIWARE = "WiiWare"
    WONDERSWAN = "WonderSwan"
    WONDERSWAN_COLOR = "WonderSwan Color"
    XBOX = "Xbox"
    XBOX_360 = "Xbox 360"
    XBOX_ONE = "Xbox One"
    XBOX_SERIES_X_S = "Xbox Series X|S"
    ZEEBO = "Zeebo"
    ZX_SPECTRUM = "ZX Spectrum"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.__str__()


class ExcelGenre(Enum):
    _3D_PLATFORMER = "3D Platformer"
    _4X = "4X"
    ACTION = "Action"
    ACTION_ADVENTURE = "Action Adventure"
    ACTION_PLATFORMER = "Action Platformer"
    ACTION_RPG = "Action RPG"
    ADVENTURE = "Adventure"
    ADVENTURE_PLATFORMER = "Adventure Platformer"
    ARCADE = "Arcade"
    BEAT_EM_UP = "Beat 'em Up"
    BOARD_GAME = "Board Game"
    CARD_GAME = "Card Game"
    COMPILATION = "Compilation"
    COMPUTER_RPG = "Computer RPG"
    DUNGEON_CRAWLER = "Dungeon Crawler"
    EDUCATIONAL = "Educational"
    EXPERIMENTAL = "Experimental"
    FIGHTING = "Fighting"
    FIRST_PERSON_ACTION = "First-Person Action"
    FIRST_PERSON_PLATFORMER = "First-Person Platformer"
    FIRST_PERSON_PUZZLE = "First-Person Puzzle"
    FIRST_PERSON_SHOOTER = "First-Person Shooter"
    FLIGHT_SIMULATION = "Flight Simulation"
    FMV = "FMV"
    GAME_CREATION = "Game Creation"
    GRAND_STRATEGY = "Grand Strategy"
    HACK_AND_SLASH = "Hack-and-Slash"
    HIDDEN_OBJECT = "Hidden Object"
    METROIDVANIA = "Metroidvania"
    MINIGAME_COLLECTION = "Minigame Collection"
    MMORPG = "MMORPG"
    PINBALL = "Pinball"
    PUZZLE = "Puzzle"
    PUZZLE_ACTION = "Puzzle Action"
    PUZZLE_PLATFORMER = "Puzzle Platformer"
    RACING = "Racing"
    RAIL_SHOOTER = "Rail Shooter"
    REAL_TIME_STRATEGY = "Real-Time Strategy"
    REAL_TIME_TACTICS = "Real-Time Tactics"
    RHYTHM = "Rhythm"
    ROGUELIKE = "Roguelike"
    RUN_AND_GUN = "Run and Gun"
    RUNNER = "Runner"
    SCROLLING_SHOOTER = "Scrolling Shooter"
    SHOOTER = "Shooter"
    SIDE_SCROLLING_PLATFORMER = "Side-Scrolling Platformer"
    SIMULATION = "Simulation"
    SPACE_COMBAT = "Space Combat"
    SPORTS = "Sports"
    STEALTH_ACTION = "Stealth Action"
    STRATEGY = "Strategy"
    STRATEGY_RPG = "Strategy RPG"
    SURVIVAL = "Survival"
    SURVIVAL_HORROR = "Survival Horror"
    TACTICAL_SHOOTER = "Tactical Shooter"
    TEXT_ADVENTURE = "Text Adventure"
    THIRD_PERSON_ACTION = "Third-Person Action"
    THIRD_PERSON_SHOOTER = "Third-Person Shooter"
    TOWER_DEFENSE = "Tower Defense"
    TRIVIA = "Trivia"
    TURN_BASED_RPG = "Turn-Based RPG"
    TURN_BASED_STRATEGY = "Turn-Based Strategy"
    TURN_BASED_TACTICS = "Turn-Based Tactics"
    TWIN_STICK_SHOOTER = "Twin-Stick Shooter"
    VEHICULAR_COMBAT = "Vehicular Combat"
    VISUAL_NOVEL = "Visual Novel"
    WEB_BROWSER = "Web Browser"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.__str__()


class TranslationStatus(Enum):
    NONE = 0
    PARTIAL = 1
    COMPLETE = 2

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class PlayingStatus(Enum):
    STALLED = 0
    PLAYING = 1
    UPCOMING = -1

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class Playability(Enum):
    UNKNOWN = 0
    PLAYABLE = 1
    UNPLAYABLE = -1

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class FuzzyDateType(Enum):
    YEAR_ONLY = 0
    MONTH_AND_YEAR_ONLY = 1

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class ExcelOwnedCondition(Enum):
    COMPLETE = "Complete"
    GAME_ONLY = "Game only"
    GAME_AND_BOX_ONLY = "Game and box only"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class ExcelOwnedFormat(Enum):
    PHYSICAL = "Physical"
    DIGITAL = "Digital"
    BOTH = "Both"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


DigitalPlatformType = Literal[
    "32-bit iOS",
    "Abandonware",
    "Amazon",
    "Battle.net",
    "Desura",
    "DRM Free",
    "Epic Games Store",
    "Freeware",
    "GOG",
    "Green Man Gaming",
    "Humble Bundle",
    "itch.io",
    "Johren",
    "Legacy Games",
    "Mojang",
    "Nintendo 3DS Ambassador Program",
    "Oculus",
    "Origin",
    "Other",
    "Pirated",
    "Playdate",
    "Playdate Catalog",
    "Square Enix",
    "Steam",
    "Super NES Classic Edition",
    "Twitch",
    "uPlay",
    "Virtual Console",
    "Xbox Live Indie Games",
]

SubscriptionServiceType = Literal[
    "Apple Arcade",
    "Games with Gold",
    "Netflix Games",
    "Nintendo Switch Online",
    "OnLive",
    "PlayStation Plus",
    "Stadia Pro",
    "Viveport",
    "Xbox Game Pass",
]

LimitedPrintCompanyType = Literal[
    "Fangamer",
    "Hard Copy Games",
    "iam8bit",
    "Limited Run Games",
    "PixelHeart",
    "Play-Asia Exclusive",
    "Special Reserve Games",
    "Strictly Limited Games",
    "Super Rare Games",
]

PhysicalMediaFormatType = Literal["LaserDisc"]

RequiredAccessoryType = Literal["Adventure Player", "Nintendo Power"]


class ExcelGame:
    """Class representing a game row from the spreadsheet.

    This class holds basic properties of a game from the game
    spreadsheet.

    Attributes:
        id: An integer ID, generated by pandas
        title: The game's title
        platform: The game's release platform
        release_date: The game's release date
        release_region: The game's release region
        publisher: The game's publisher
        developer: The game's developer
        franchise: The franchise this game belongs to
        genre: This game's genre
        notes: Collection notes about this game
        owned_format: The format that this game is owned in (e.g. Physical, Digital)
    """

    id: int
    title: str
    platform: Optional[ExcelPlatform]
    release_date: Optional[datetime.datetime]
    release_region: ExcelRegion
    publisher: str
    developer: str
    franchise: Optional[str]
    genre: ExcelGenre
    notes: str
    owned_format: Optional[ExcelOwnedFormat]
    estimated_playtime: Optional[float]
    completed: bool
    priority: Optional[int]
    metacritic_rating: Optional[float]
    gamefaqs_rating: Optional[float]
    dlc: bool
    owned: bool
    translation: Optional[TranslationStatus]
    vr: bool
    playing_status: Optional[PlayingStatus]
    date_purchased: Optional[datetime.datetime]
    purchase_price: Optional[float]
    playability: Playability
    completion_time: Optional[float]
    fuzzy_date: Optional[FuzzyDateType]
    owned_condition: Optional[ExcelOwnedCondition]
    date_completed: Optional[datetime.datetime]
    wishlisted: bool

    # Completion Metadata

    played_in_vr: bool = False
    collection: Optional[str] = None
    completion_number: Optional[int] = None
    steam_deck: bool = False
    emulated: bool = False
    completion_notes: Optional[str] = None

    # Games on Order

    order_vendor: Optional[str] = None
    order_status: Optional[str] = None
    estimated_release: Optional[datetime.datetime] = None
    order_id: Optional[str] = None
    order_link: Optional[str] = None
    address_on_order: Optional[str] = None
    tracking_number: Optional[str] = None

    # Computed Columns

    hash_id: Optional[str] = None
    release_year: Optional[int] = None
    full_name: Optional[str] = None
    combined_rating: Optional[float] = None
    dollar_per_hour: Optional[float] = None
    normal_title: Optional[str] = None
    collection_hash_id: Optional[str] = None
    game_order_hash_id: Optional[str] = None
    game_platform_hash_id: Optional[str] = None
    sort_parts: Optional[List[Any]] = None

    # Notes Metadata

    digital_platform: Optional[DigitalPlatformType] = None
    subscription_service: Optional[SubscriptionServiceType] = None
    owned_variant_types: Optional[List[str]] = None
    delisted: Optional[bool] = None
    copies_owned: Optional[int] = None
    limited_print_company: Optional[LimitedPrintCompanyType] = None
    physical_media_format: Optional[PhysicalMediaFormatType] = None
    browser_link: Optional[str] = None
    required_accessory: Optional[RequiredAccessoryType] = None
    multi_disc_collection_name: Optional[str] = None
    owned_damaged: Optional[bool] = None

    child_games: List[ExcelGame] = []

    group_metadata: Optional[Any] = None

    def __init__(
        self,
        _id: int = 0,
        title: Optional[str] = None,
        platform: Optional[str] = None,
        release_date: Optional[datetime.datetime] = None,
        release_region: ExcelRegion = ExcelRegion.NORTH_AMERICA,
        publisher: Optional[str] = None,
        developer: Optional[str] = None,
        franchise: Optional[str] = None,
        genre: Optional[str] = None,
        notes: Optional[str] = None,
        owned_format: Optional[ExcelOwnedFormat] = None,
        estimated_playtime: Optional[float] = None,
        completed: bool = False,
        priority: Optional[int] = None,
        metacritic_rating: Optional[float] = None,
        gamefaqs_rating: Optional[float] = None,
        dlc: Optional[bool] = False,
        owned: Optional[bool] = False,
        translation: Optional[TranslationStatus] = None,
        vr: Optional[bool] = None,
        playing_status: Optional[PlayingStatus] = None,
        date_purchased: Optional[datetime.datetime] = None,
        purchase_price: Optional[float] = None,
        rating: Optional[float] = None,
        playability: Playability = Playability.UNKNOWN,
        completion_time: Optional[float] = None,
        fuzzy_date: Optional[FuzzyDateType] = None,
        owned_condition: Optional[ExcelOwnedCondition] = None,
        date_completed: Optional[datetime.datetime] = None,
        wishlisted: Optional[bool] = False,
        group_metadata: Optional[str] = None,
    ):
        self.id = int(_id)
        self.title = str(title) if title is not None else title
        self.platform = ExcelPlatform(platform) if platform is not None else platform
        self.release_date = release_date
        self.release_region = release_region
        self.publisher = str(publisher) if publisher is not None else publisher
        self.developer = str(developer) if developer is not None else developer
        self.franchise = (
            None
            if franchise is None or str(franchise).strip() == ""
            else str(franchise)
        )
        self.genre = ExcelGenre(genre) if genre is not None else genre
        self.notes = str(notes) if notes is not None else notes
        self.owned_format = owned_format
        self.estimated_playtime = (
            None
            if estimated_playtime is None or str(estimated_playtime).strip() == ""
            else float(estimated_playtime)
        )
        self.completed = bool(completed)
        self.priority = (
            None if priority is None or str(priority).strip() == "" else int(priority)
        )
        self.metacritic_rating = (
            None
            if metacritic_rating is None or str(metacritic_rating).strip() == ""
            else float(metacritic_rating)
        )
        self.gamefaqs_rating = (
            None
            if gamefaqs_rating is None or str(gamefaqs_rating).strip() == ""
            else float(gamefaqs_rating)
        )
        self.dlc = dlc is not None and bool(dlc)
        self.owned = owned is not None and bool(owned)
        self.translation = translation
        self.vr = vr is not None and bool(vr)
        self.playing_status = playing_status
        self.date_purchased = date_purchased
        self.purchase_price = (
            None
            if purchase_price is None or str(purchase_price).strip() == ""
            else float(purchase_price)
        )
        self.rating = (
            None if rating is None or str(rating).strip() == "" else float(rating)
        )
        self.playability = playability
        self.completion_time = (
            None
            if completion_time is None or str(completion_time).strip() == ""
            else float(completion_time)
        )
        self.fuzzy_date = fuzzy_date
        self.owned_condition = owned_condition
        self.date_completed = date_completed
        self.wishlisted = wishlisted is not None and bool(wishlisted)
        self.group_metadata = group_metadata

        self.compute_properties()

    def compute_properties(self):
        self.release_year = (
            self.release_date.year if self.release_date is not None else None
        )

        self.hash_id = hashlib.sha256(
            str(
                (
                    self.title,
                    self.platform,
                    self.release_year,
                    self.release_region,
                    self.publisher,
                    self.developer,
                    self.franchise,
                    self.genre,
                )
            ).encode()
        ).hexdigest()

        self.collection_hash_id = hashlib.sha256(
            str(
                (
                    self.collection or self.title,
                    self.platform,
                    self.release_region,
                    self.publisher,
                    self.developer,
                    self.franchise,
                    self.genre,
                )
            ).encode()
        ).hexdigest()

        self.game_order_hash_id = hashlib.sha256(
            str(
                (
                    self.title,
                    self.platform,
                    self.date_purchased,
                    self.purchase_price,
                    self.owned_format,
                )
            ).encode()
        ).hexdigest()

        self.game_platform_hash_id = hashlib.sha256(
            str(
                (
                    self.title,
                    self.platform,
                )
            ).encode()
        ).hexdigest()

        self.full_name = (
            f"{self.title} ({self.platform}) [{self.release_year or 'Unreleased'}]"
        )

        other_ratings = list(
            filter(
                lambda x: x is not None,
                [
                    self.metacritic_rating,
                    self.gamefaqs_rating,
                ],
            )
        )

        ratings = list(
            filter(
                lambda x: x is not None,
                [
                    (
                        self.rating
                        or ((self.priority / 5) if self.priority is not None else None)
                    ),
                    statistics.mean(other_ratings) if any(other_ratings) else None,
                ],
            )
        )

        if any(ratings):
            self.combined_rating = statistics.mean(ratings)

        self.dollar_per_hour = (
            ((self.purchase_price or 0) / self.estimated_playtime)
            if self.estimated_playtime is not None
            else 0
        )

        def try_roman(part: str) -> str:
            try:
                _num = roman.fromRoman("".join(filter(str.isalpha, part)).upper())

                if _num > 20 or _num == 0:
                    return part

                leading = "9" if _num > 9 else ""  # Hack for sorting
                return f"{leading}{_num}"
            except roman.InvalidRomanNumeralError:
                return part

        if self.title is not None:
            self.normal_title = unidecode(
                str.casefold(self.title)
                .removeprefix("the ")
                .removeprefix("a ")
                .removeprefix("an ")
                .replace(" & ", " and ")
                .replace(" the ", " ")
                .replace(" a ", "")
                .replace(" an ", "")
            )

            self.normal_title = "".join(
                filter(lambda l: str.isalnum(l) or str.isspace(l), self.normal_title)
            )

            parts = self.normal_title.split()
            self.normal_title = ""

            for i, w in enumerate(parts):
                final = i == len(parts) - 1

                if not final and w == "i":
                    self.normal_title += w + " "
                    continue

                self.normal_title += try_roman(w)

                if not final:
                    self.normal_title += " "

        if self.notes is not None:
            self.__process_notes()

    def __process_notes(self):
        try:
            assert self.notes in get_args(DigitalPlatformType)
            self.digital_platform = self.notes
            return
        except AssertionError:
            pass

        try:
            assert self.notes in get_args(SubscriptionServiceType)
            self.subscription_service = self.notes
            return
        except AssertionError:
            pass

        if self.notes == "Delisted":
            self.delisted = True
            return

        try:
            assert self.notes in get_args(LimitedPrintCompanyType)
            self.limited_print_company = self.notes
            return
        except AssertionError:
            pass

        if self.notes.startswith("Limited Run Games"):
            self.limited_print_company = "Limited Run Games"
            self.notes = (
                self.notes.replace("Limited Run Games", "").replace(" - ", "").strip()
            )

        try:
            assert self.notes in get_args(PhysicalMediaFormatType)
            self.physical_media_format = self.notes
            return
        except AssertionError:
            pass

        if self.notes == "Link":
            return
            # TODO: Implement browser link parsing

        try:
            assert self.notes in get_args(RequiredAccessoryType)
            self.required_accessory = self.notes
            return
        except AssertionError:
            pass

        if " and " in self.notes:
            copies = self.notes.replace(" copies", "").split(" and ")
            self.copies_owned = len(copies)
            self.owned_variant_types = copies
            return

        if self.notes.endswith("Edition"):
            self.owned_variant_types = [self.notes]
            return

        if (
            self.notes.startswith("Collection with")
            or self.notes.startswith("Dual Pack")
            or self.notes.endswith("Trilogy")
        ):
            self.multi_disc_collection_name = self.notes
            return

        if (
            "broken" in self.notes.casefold()
            or "damage" in self.notes.casefold()
            or "poor" in self.notes.casefold()
        ):
            all_notes = self.notes.split(", ")
            if len(all_notes) > 1:
                self.owned_variant_types = [all_notes[-1]]
            self.owned_damaged = True
            return

        if "two copies" in self.notes.casefold():
            self.copies_owned = 2

            matches: List[str] = re.findall(r"\(.*\)", self.notes)

            if any(matches):
                variants = (
                    matches[0].replace("One ", "").replace("one ", "").split(", ")
                )
                self.owned_variant_types = variants
                return

            all_notes = self.notes.split(", ")
            if len(all_notes) > 1:
                self.owned_variant_types = [all_notes[0]]
            return

        if (
            "Deluxe" in self.notes
            or self.notes == "Steelbook"
            or self.notes.endswith("Hits")
            or "Misprinted" in self.notes
        ):
            self.owned_variant_types = [self.notes]
            return

    def __str__(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True, indent=4, default=str)

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self):
        return hash(
            (
                self.title,
                self.platform,
                self.release_year,
                self.release_region,
                self.publisher,
                self.developer,
                self.franchise,
                self.genre,
            )
        )

    def __eq__(self, other):
        return hash(self) == hash(other)


class ExcelGameBuilder:
    def __init__(self):
        self._eg = ExcelGame()

    def merge(self, g1: ExcelGame, g2: ExcelGame) -> ExcelGame:
        return (
            self.with_title(g1.title or g2.title)
            .with_platform(g1.platform or g2.platform)
            .with_release_date(g1.release_date or g2.release_date)
            .with_release_region(g1.release_region or g2.release_region)
            .with_publisher(g1.publisher or g2.publisher)
            .with_developer(g1.developer or g2.developer)
            .with_franchise(g1.franchise or g2.franchise)
            .with_genre(g1.genre or g2.genre)
            .with_vr(g1.vr or g2.vr)
            .with_dlc(g1.dlc or g2.dlc)
            .with_translation(g1.translation or g2.translation)
            .with_owned(g1.owned or g2.owned)
            .with_owned_condition(g1.owned_condition or g2.owned_condition)
            .with_date_purchased(g1.date_purchased or g2.date_purchased)
            .with_purchase_price(
                g1.purchase_price
                if g1.purchase_price is not None
                else g2.purchase_price
            )
            .with_owned_format(g1.owned_format or g2.owned_format)
            .with_completed(g1.completed or g2.completed)
            .with_date_completed(g1.date_completed or g2.date_completed)
            .with_completion_time(g1.completion_time or g2.completion_time)
            .with_rating(g1.rating or g2.rating)
            .with_metacritic_rating(g1.metacritic_rating or g2.metacritic_rating)
            .with_gamefaqs_rating(g1.gamefaqs_rating or g2.gamefaqs_rating)
            .with_notes(g1.notes or g2.notes)
            .with_priority(g1.priority or g2.priority)
            .with_wishlisted(g1.wishlisted or g2.wishlisted)
            .with_estimated_playtime(g1.estimated_playtime or g2.estimated_playtime)
            .with_playing_status(g1.playing_status or g2.playing_status)
            .with_playability(
                g1.playability
                if g1.playability != Playability.UNKNOWN
                else g2.playability
            )
            .with_order_vendor(g1.order_vendor or g2.order_vendor)
            .with_order_status(g1.order_status or g2.order_status)
            .with_estimated_release(g1.estimated_release or g2.estimated_release)
            .with_order_id(g1.order_id or g2.order_id)
            .with_address_on_order(g1.address_on_order or g2.address_on_order)
            .with_tracking_number(g1.tracking_number or g2.tracking_number)
            .with_played_in_vr(g1.played_in_vr or g2.played_in_vr)
            .with_collection(g1.collection or g2.collection)
            .with_completion_number(g1.completion_number or g2.completion_number)
            .with_steam_deck(g1.steam_deck or g2.steam_deck)
            .with_emulated(g1.emulated or g2.emulated)
            .with_completion_notes(g1.completion_notes or g2.completion_notes)
            .build()
        )

    def with_id(self, _id: int) -> ExcelGameBuilder:
        assert isinstance(_id, int)
        self._eg.id = _id
        return self

    def with_title(self, title: str) -> ExcelGameBuilder:
        assert isinstance(title, str)
        self._eg.title = title
        return self

    def with_platform(
        self, platform: Optional[str | ExcelPlatform]
    ) -> ExcelGameBuilder:
        assert isinstance(platform, str | ExcelPlatform | None)
        val = None
        if platform is not None:
            val = (
                platform
                if isinstance(platform, ExcelPlatform)
                else ExcelPlatform(platform)
            )

        self._eg.platform = val
        return self

    def with_release_date(
        self, release_date: Optional[datetime.datetime]
    ) -> ExcelGameBuilder:
        assert isinstance(release_date, datetime.datetime | None)
        self._eg.release_date = release_date
        return self

    def with_release_region(self, region: ExcelRegion) -> ExcelGameBuilder:
        assert isinstance(region, ExcelRegion)
        self._eg.release_region = region
        return self

    def with_publisher(self, publisher: str) -> ExcelGameBuilder:
        assert isinstance(publisher, str)
        self._eg.publisher = publisher
        return self

    def with_developer(self, developer: str) -> ExcelGameBuilder:
        assert isinstance(developer, str)
        self._eg.developer = developer
        return self

    def with_franchise(self, franchise: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(franchise, str | None)
        self._eg.franchise = franchise
        return self

    def with_genre(self, genre: str | ExcelGenre) -> ExcelGameBuilder:
        assert isinstance(genre, str | ExcelGenre)
        self._eg.genre = genre if isinstance(genre, ExcelGenre) else ExcelGenre(genre)
        return self

    def with_notes(self, notes: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(notes, str | None)
        self._eg.notes = notes
        return self

    def with_owned_format(
        self, owned_format: Optional[str | ExcelOwnedFormat]
    ) -> ExcelGameBuilder:
        assert isinstance(owned_format, str | ExcelOwnedFormat | None)
        self._eg.owned_format = (
            owned_format
            if isinstance(owned_format, ExcelOwnedFormat | None)
            else ExcelOwnedFormat(owned_format)
        )
        return self

    def with_estimated_playtime(
        self, estimated_playtime: Optional[float]
    ) -> ExcelGameBuilder:
        assert isinstance(estimated_playtime, float | None)
        self._eg.estimated_playtime = estimated_playtime
        return self

    def with_completed(self, completed: bool) -> ExcelGameBuilder:
        assert isinstance(completed, bool)
        self._eg.completed = completed
        return self

    def with_priority(self, priority: Optional[int]) -> ExcelGameBuilder:
        assert isinstance(priority, int | None)
        self._eg.priority = priority
        return self

    def with_metacritic_rating(
        self, metacritic_rating: Optional[float]
    ) -> ExcelGameBuilder:
        assert isinstance(metacritic_rating, float | None)
        self._eg.metacritic_rating = metacritic_rating
        return self

    def with_gamefaqs_rating(
        self, gamefaqs_rating: Optional[float]
    ) -> ExcelGameBuilder:
        assert isinstance(gamefaqs_rating, float | None)
        self._eg.gamefaqs_rating = gamefaqs_rating
        return self

    def with_dlc(self, dlc: Optional[bool]) -> ExcelGameBuilder:
        assert isinstance(dlc, bool | None)
        self._eg.dlc = dlc is not None and dlc
        return self

    def with_owned(self, owned: Optional[bool]) -> ExcelGameBuilder:
        assert isinstance(owned, bool | None)
        self._eg.owned = owned is not None and owned
        return self

    def with_translation(
        self, translation: Optional[TranslationStatus]
    ) -> ExcelGameBuilder:
        assert isinstance(translation, TranslationStatus | None)
        self._eg.translation = translation
        return self

    def with_vr(self, vr: Optional[bool]) -> ExcelGameBuilder:
        assert isinstance(vr, bool | None)
        self._eg.vr = vr is not None and vr
        return self

    def with_playing_status(
        self, playing_status: Optional[PlayingStatus]
    ) -> ExcelGameBuilder:
        assert isinstance(playing_status, PlayingStatus | None)
        self._eg.playing_status = playing_status
        return self

    def with_date_purchased(
        self, date_purchased: Optional[datetime.datetime]
    ) -> ExcelGameBuilder:
        assert isinstance(date_purchased, datetime.datetime | None)
        self._eg.date_purchased = date_purchased
        return self

    def with_purchase_price(self, purchase_price: Optional[float]) -> ExcelGameBuilder:
        assert isinstance(purchase_price, float | None)
        self._eg.purchase_price = purchase_price
        return self

    def with_rating(self, rating: Optional[float]) -> ExcelGameBuilder:
        assert isinstance(rating, float | None)
        self._eg.rating = rating
        return self

    def with_playability(self, playability: Optional[Playability]) -> ExcelGameBuilder:
        assert isinstance(playability, Playability | None)
        self._eg.playability = playability
        return self

    def with_completion_time(
        self, completion_time: Optional[float]
    ) -> ExcelGameBuilder:
        assert isinstance(completion_time, float | None)
        self._eg.completion_time = completion_time
        return self

    def with_fuzzy_date(self, fuzzy_date: Optional[FuzzyDateType]) -> ExcelGameBuilder:
        assert isinstance(fuzzy_date, FuzzyDateType | None)
        self._eg.fuzzy_date = fuzzy_date
        return self

    def with_owned_condition(
        self, owned_condition: Optional[str | ExcelOwnedCondition]
    ) -> ExcelGameBuilder:
        assert isinstance(owned_condition, str | ExcelOwnedCondition | None)
        self._eg.owned_condition = (
            owned_condition
            if isinstance(owned_condition, ExcelOwnedCondition | None)
            else ExcelGameBuilder.__convert_owned_condition(owned_condition)
        )
        return self

    @staticmethod
    def __convert_owned_condition(owned_condition: str) -> ExcelOwnedCondition:
        try:
            return ExcelOwnedCondition(owned_condition)
        except ValueError:
            if "Complete" in owned_condition:
                return ExcelOwnedCondition.COMPLETE

            if "only" in owned_condition:
                return ExcelOwnedCondition.GAME_ONLY

            return ExcelOwnedCondition.GAME_AND_BOX_ONLY

    def with_date_completed(
        self, date_completed: Optional[datetime.datetime]
    ) -> ExcelGameBuilder:
        assert isinstance(date_completed, datetime.datetime | None)
        self._eg.date_completed = date_completed
        return self

    def with_wishlisted(self, wishlisted: Optional[bool]) -> ExcelGameBuilder:
        assert isinstance(wishlisted, bool | None)
        self._eg.wishlisted = wishlisted is not None and wishlisted
        return self

    def with_played_in_vr(self, played_in_vr: Optional[bool]) -> ExcelGameBuilder:
        assert isinstance(played_in_vr, bool | None)
        self._eg.played_in_vr = played_in_vr is not None and played_in_vr
        return self

    def with_collection(self, collection: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(collection, str | None)
        self._eg.collection = collection
        return self

    def with_completion_number(
        self, completion_number: Optional[int]
    ) -> ExcelGameBuilder:
        assert isinstance(completion_number, int | None)
        self._eg.completion_number = completion_number
        return self

    def with_steam_deck(self, steam_deck: Optional[bool]) -> ExcelGameBuilder:
        assert isinstance(steam_deck, bool | None)
        self._eg.steam_deck = steam_deck is not None and steam_deck
        return self

    def with_emulated(self, emulated: Optional[bool]) -> ExcelGameBuilder:
        assert isinstance(emulated, bool | None)
        self._eg.emulated = emulated is not None and emulated
        return self

    def with_completion_notes(
        self, completion_notes: Optional[str]
    ) -> ExcelGameBuilder:
        assert isinstance(completion_notes, str | None)
        self._eg.completion_notes = completion_notes
        return self

    def with_order_vendor(self, vendor: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(vendor, str | None)
        self._eg.order_vendor = vendor
        return self

    def with_order_status(self, order_status: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(order_status, str | None)
        self._eg.order_status = order_status
        return self

    def with_estimated_release(
        self, estimated_release: Optional[datetime.datetime]
    ) -> ExcelGameBuilder:
        assert isinstance(estimated_release, datetime.datetime | None)
        self._eg.estimated_release = estimated_release
        return self

    def with_order_id(self, order_id: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(order_id, str | None)
        self._eg.order_id = order_id
        return self

    def with_order_link(self, order_link: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(order_link, str | None)
        self._eg.order_link = order_link
        return self

    def with_tracking_number(self, tracking_number: Optional[str]) -> ExcelGameBuilder:
        assert isinstance(tracking_number, str | None)
        self._eg.tracking_number = tracking_number
        return self

    def with_address_on_order(
        self, address_on_order: Optional[str]
    ) -> ExcelGameBuilder:
        assert isinstance(address_on_order, str | None)
        self._eg.address_on_order = address_on_order
        return self

    def build(self) -> ExcelGame:
        self._eg.compute_properties()
        return self._eg
