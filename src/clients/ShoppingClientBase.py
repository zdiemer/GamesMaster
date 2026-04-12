import datetime
import json
import re

from typing import (
    Optional,
    List,
    Dict,
    Any,
    Generic,
    TypeVar,
    Callable,
    Iterator,
    Tuple,
)

from bs4 import ResultSet

from clients import ClientBase, DatePart, RateLimit
from config import Config
from match_validator import MatchValidator

from excel_game import ExcelPlatform
from excel_loader import ExcelLoader


class BaseResult:
    id: str
    platform: ExcelPlatform
    price: float
    release_date: datetime.datetime
    title: str
    url: str

    def __init__(
        self,
        id: str,
        platform: ExcelPlatform,
        price: float,
        release_date: datetime.datetime,
        title: str,
        url: str,
    ):
        self.id = id
        self.platform = platform
        self.price = price
        self.release_date = release_date
        self.title = title
        self.url = url

    def __str__(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True, indent=4, default=str)

    def __repr__(self) -> str:
        return self.__str__()


ResultT = TypeVar("ResultT", bound=BaseResult)


class ShoppingClientBase(ClientBase, Generic[ResultT]):
    silent: bool
    max_pages: int

    _VALID_PLATFORMS_MAPPING: Dict[str, ExcelPlatform] = {
        "nintendo switch": ExcelPlatform.NINTENDO_SWITCH,
        "nsw": ExcelPlatform.NINTENDO_SWITCH,
        "steam pc [online game code]": ExcelPlatform.PC,
        "steam online game code": ExcelPlatform.PC,
        "pc [online game code]": ExcelPlatform.PC,
        "pc online game code": ExcelPlatform.PC,
        "playstation 4": ExcelPlatform.PLAYSTATION_4,
        "ps4": ExcelPlatform.PLAYSTATION_4,
        "playstation 5": ExcelPlatform.PLAYSTATION_5,
        "ps5": ExcelPlatform.PLAYSTATION_5,
        "xbox": ExcelPlatform.XBOX_SERIES_X_S,
        "xbox series x": ExcelPlatform.XBOX_SERIES_X_S,
        "xbox series x|s [digital code]": ExcelPlatform.XBOX_SERIES_X_S,
        "xbox series x|s digital code": ExcelPlatform.XBOX_SERIES_X_S,
        "xbox series x/s": ExcelPlatform.XBOX_SERIES_X_S,
        "xbox series x/xbox one": ExcelPlatform.XBOX_SERIES_X_S,
        "windows": ExcelPlatform.PC,
        "ea app [online game code]": ExcelPlatform.PC,
        "ea app online game code": ExcelPlatform.PC,
        "psvr2": ExcelPlatform.PLAYSTATION_5,
        "playstation": ExcelPlatform.PLAYSTATION_5,
        "xbox one": ExcelPlatform.XBOX_ONE,
        "play station 5": ExcelPlatform.PLAYSTATION_5,
        "pc": ExcelPlatform.PC,
        "PlayStation PS4": ExcelPlatform.PLAYSTATION_4,
        "xbox 360": ExcelPlatform.XBOX_360,
        "xbox [digital code]": ExcelPlatform.XBOX_SERIES_X_S,
        "xsx": ExcelPlatform.XBOX_SERIES_X_S,
        "windows 10": ExcelPlatform.PC,
        "ea app pc [online game code]": ExcelPlatform.PC,
        "steam game code": ExcelPlatform.PC,
        "evercade": ExcelPlatform.EVERCADE,
        "xbox one [digital code]": ExcelPlatform.XBOX_ONE,
        "pc steam [online game code]": ExcelPlatform.PC,
        "nintendo switch 2": ExcelPlatform.NINTENDO_SWITCH_2,
        "ns2": ExcelPlatform.NINTENDO_SWITCH_2,
        "nsw2": ExcelPlatform.NINTENDO_SWITCH_2,
        "switch 2": ExcelPlatform.NINTENDO_SWITCH_2,
    }

    _EXCLUDE_CONDITIONS: List[Callable[[ResultT], bool]] = [
        lambda ar: "Controller" in ar.title
        or "Carry Case" in ar.title
        or "Travel Case" in ar.title
        or "Gamepad" in ar.title
        or "Console" in ar.title
        or "HORI" in ar.title
        or "Turtle Beach" in ar.title
        or "Joystick" in ar.title
        or "Keyboard" in ar.title
        or "Racing Wheel" in ar.title
    ]

    upcoming_games: Dict[ExcelPlatform, List[ResultT]]

    def __init__(
        self,
        validator: MatchValidator = None,
        config: Config = None,
        silent: bool = False,
        max_pages: int = 400,
        use_vpn: bool = True,
    ):
        validator = validator or MatchValidator()
        self.upcoming_games = {}
        self.silent = silent
        self.max_pages = max_pages
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            RateLimit(4, DatePart.SECOND),
            spoof_headers=True,
            use_vpn=use_vpn,
            cycle_vpn_stasues=[503],
            vpn_regions=[
                "us-alabama",
                "us-alaska",
                "us-arkansas",
                "us-atlanta",
                "us-baltimore",
                "us-california",
                "us-chicago",
                "us-connecticut",
                "us-denver",
                "us-east",
                "us-east-streaming-optimized",
                "us-florida",
                "us-honolulu",
                "us-houston",
                "us-idaho",
                "us-indiana",
                "us-iowa",
                "us-kansas",
                "us-kentucky",
                "us-las-vegas",
                "us-louisiana",
                "us-maine",
                "us-massachusetts",
                "us-michigan",
                "us-minnesota",
                "us-mississippi",
                "us-missouri",
                "us-montana",
                "us-nebraska",
                "us-new-hampshire",
                "us-new-mexico",
                "us-new-york",
                "us-north-carolina",
                "us-north-dakota",
                "us-ohio",
                "us-oklahoma",
                "us-oregon",
                "us-pennsylvania",
                "us-rhode-island",
                "us-salt-lake-city",
                "us-seattle",
                "us-silicon-valley",
                "us-south-carolina",
                "us-south-dakota",
                "us-tennessee",
                "us-texas",
                "us-vermont",
                "us-virginia",
                "us-washington-dc",
                "us-west",
                "us-west-streaming-optimized",
                "us-west-virginia",
                "us-wilmington",
                "us-wisconsin",
                "us-wyoming",
            ],
        )

    def get_id_from_result(self, result: Any) -> Optional[str]:
        raise NotImplementedError

    def get_platform_from_result(self, result: Any) -> Optional[str]:
        raise NotImplementedError

    def get_price_from_result(self, result: Any) -> Optional[float]:
        raise NotImplementedError

    def get_release_date_from_result(self, result: Any) -> Optional[datetime.datetime]:
        raise NotImplementedError

    def get_title_from_result(self, result: Any) -> str:
        raise NotImplementedError

    async def get_upcoming_games(self) -> Dict[ExcelPlatform, List[ResultT]]:
        raise NotImplementedError

    def get_url_from_result(self, result: Any) -> Optional[str]:
        raise NotImplementedError

    def is_unreleased_result(self, result: Any) -> bool:
        raise NotImplementedError

    def add_upcoming_game(self, platform: ExcelPlatform, game: ResultT) -> None:
        if platform in self.upcoming_games:
            for p_game in self.upcoming_games[platform]:
                if p_game.id == game.id:
                    return

            self.upcoming_games[platform].append(game)
        else:
            self.upcoming_games[platform] = [game]

    def clean_title_with_platform(
        self, title: str
    ) -> Tuple[str, Optional[ExcelPlatform]]:
        paren_re = r"\((?P<platform>[^\)]*)\)"
        platform: Optional[ExcelPlatform] = None

        if title.startswith("Blaze Evercade") or title.startswith("Evercade"):
            return (
                title.replace("Blaze Evercade", "").replace("Evercade", "").strip(),
                ExcelPlatform.EVERCADE,
            )

        re_match = re.search(paren_re, title)

        if re_match is not None:
            platform = self.try_get_platform(re_match.group("platform"))

        title = re.sub(paren_re, "", title).strip()

        title, platform = self.split_title(title, " - ", platform)

        # EM DASH used sometimes
        title, platform = self.split_title(title, " – ", platform)

        return (title, platform)

    def get_platform(self, platform: str) -> ExcelPlatform:
        return self._VALID_PLATFORMS_MAPPING[platform.casefold().strip()]

    async def get_unordered_games(self) -> Dict[ExcelPlatform, List[ResultT]]:
        loader = ExcelLoader()
        upcoming_games = await self.get_upcoming_games()

        for game in loader.games_on_order:
            if game.platform is None:
                continue
            if game.platform not in upcoming_games:
                continue

            to_remove: Optional[ResultT] = None

            for upcoming_game in upcoming_games[game.platform]:
                if self.validator.titles_equal_normalized(
                    game.title, upcoming_game.title
                ):
                    to_remove = upcoming_game
                    break
                if self.validator.titles_equal_fuzzy(game.title, upcoming_game.title):
                    should_remove = input(
                        f"Does {game.full_name} match {upcoming_game.title} ({upcoming_game.url})? (y/n): "
                    )

                    if should_remove.lower().strip() == "y":
                        to_remove = upcoming_game
                        break

            if to_remove is not None:
                upcoming_games[game.platform].remove(to_remove)

        return upcoming_games

    def get_unreleased_from_results(
        self, results: ResultSet[Any] | List[Any]
    ) -> Iterator[Any]:
        return filter(self.is_unreleased_result, results)

    def split_title(
        self, title: str, separator: str = " ", platform: Optional[ExcelPlatform] = None
    ) -> Tuple[str, Optional[ExcelPlatform]]:
        parts = title.split(separator)

        if len(parts) == 1:
            return (title, platform)

        if platform is None:
            platform = self.try_get_platform(parts[-1])

        return (" ".join(parts[:-1]), platform)

    def try_add_upcoming_game(self, platform: ExcelPlatform, game: ResultT) -> None:
        for exclusion in self._EXCLUDE_CONDITIONS:
            if exclusion(game):
                return

        self.add_upcoming_game(platform, game)

    def try_get_platform(self, platform: str) -> Optional[ExcelPlatform]:
        if not self.verify_platform(platform):
            if not self.silent:
                print(f"{platform} not considered a valid platform.")
            return None
        return self.get_platform(platform)

    def verify_platform(self, platform: str) -> bool:
        return platform.casefold().strip() in self._VALID_PLATFORMS_MAPPING
