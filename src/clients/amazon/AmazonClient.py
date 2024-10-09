import datetime
import json
import re
from typing import Any, AsyncGenerator, Callable, Dict, Iterator, List, Optional, Tuple

from bs4 import BeautifulSoup, ResultSet

from excel_game import ExcelPlatform
from excel_loader import ExcelLoader
from clients import ClientBase, DatePart, RateLimit
from config import Config
from match_validator import MatchValidator


class AmazonResult:
    title: str
    platform: ExcelPlatform
    release_date: datetime.datetime
    price: float
    url: str
    id: str

    def __init__(
        self,
        title: str,
        platform: ExcelPlatform,
        release_date: datetime.datetime,
        price: float,
        url: str,
        _id: str,
    ):
        self.title = title
        self.platform = platform
        self.release_date = release_date
        self.price = price
        self.url = url
        self.id = _id

    def __str__(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True, indent=4, default=str)

    def __repr__(self) -> str:
        return self.__str__()


class AmazonClient(ClientBase):
    __BASE_AMAZON_URL: str = "https://www.amazon.com"
    __VIDEO_GAMES_URL: str = __BASE_AMAZON_URL + "/s"

    __VALID_PLATFORMS_MAPPING: Dict[str, ExcelPlatform] = {
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
        "xbox seris x/s": ExcelPlatform.XBOX_SERIES_X_S,
        "xbox series x/xbox one": ExcelPlatform.XBOX_SERIES_X_S,
    }

    __EXCLUDE_CONDITIONS: List[Callable[[AmazonResult], bool]] = [
        lambda ar: "Controller" in ar.title
    ]

    upcoming_games: Dict[ExcelPlatform, List[AmazonResult]]

    def __init__(self, validator: MatchValidator, config: Config = None):
        self.upcoming_games = {}
        config = config or Config.create()
        super().__init__(
            validator, config, RateLimit(60, DatePart.MINUTE), spoof_headers=True
        )

    async def search(
        self, query: str = "", page: int = 1, prime_only: bool = False
    ) -> Any:
        return await self.get(
            self.__VIDEO_GAMES_URL,
            params={
                "k": query,
                "i": "videogames",
                "s": "date-desc-rank",
                "page": page,
                "rh": "n:468642,p_85:2470955011" if prime_only else "",
            },
            json=False,
        )

    async def get_search_results(self, page: int = 1) -> ResultSet[Any]:
        html = await self.search(page=page)
        soup = BeautifulSoup(html, "html.parser")
        return soup.find_all("div", {"data-component-type": "s-search-result"})

    def is_unreleased_result(self, result: Any) -> bool:
        release_date = self.get_release_date_from_result(result)

        if release_date is None or datetime.datetime.now() > release_date:
            return False

        return True

    def get_unreleased_from_results(self, results: ResultSet[Any]) -> Iterator[Any]:
        return filter(self.is_unreleased_result, results)

    async def search_paginated(self) -> AsyncGenerator[ResultSet[Any], None]:
        page = 1
        pages_without_unreleased = 0
        results = await self.get_search_results(page)

        yield results

        while results is not None and pages_without_unreleased < 5:
            if not any(self.get_unreleased_from_results(results)):
                pages_without_unreleased += 1
            else:
                pages_without_unreleased = 0

            page += 1
            print(f"Requesting page {page}")
            results = await self.get_search_results(page)
            yield results

    def get_platform_from_result(self, result: Any) -> Optional[str]:
        price_recipe = result.find("div", {"data-cy": "price-recipe"})

        if price_recipe is None:
            return None

        platform_spacer = price_recipe.find("div", {"class": "a-spacing-mini"})

        if platform_spacer is None:
            return None

        return platform_spacer.getText().strip()

    def verify_platform(self, platform: str) -> bool:
        return platform.casefold().strip() in self.__VALID_PLATFORMS_MAPPING

    def get_platform(self, platform: str) -> ExcelPlatform:
        return self.__VALID_PLATFORMS_MAPPING[platform.casefold().strip()]

    def try_get_platform(self, platform: str) -> Optional[ExcelPlatform]:
        if not self.verify_platform(platform):
            print(f"{platform} not considered a valid platform.")
            return None
        return self.get_platform(platform)

    def try_add_upcoming_game(
        self, platform: ExcelPlatform, game: AmazonResult
    ) -> None:
        for exclusion in self.__EXCLUDE_CONDITIONS:
            if exclusion(game):
                return

        self.add_upcoming_game(platform, game)

    def add_upcoming_game(self, platform: ExcelPlatform, game: AmazonResult) -> None:
        if platform in self.upcoming_games:
            self.upcoming_games[platform].append(game)
        else:
            self.upcoming_games[platform] = [game]

    def get_title_from_result(self, result: Any) -> str:
        return result.find("div", {"data-cy": "title-recipe"}).h2.getText().strip()

    def get_release_date_from_result(self, result: Any) -> Optional[datetime.datetime]:
        will_be_released_span = result.find(
            "span",
            {
                "aria-label": lambda l: l is not None
                and "This item will be released" in l
            },
        )

        if will_be_released_span is not None:
            will_be_released_text = will_be_released_span.getText().strip()

            try:
                return datetime.datetime.strptime(
                    will_be_released_text, "This item will be released on %B %d, %Y."
                )
            except ValueError:
                print(f"Failed to parse {will_be_released_text}")
                return None

        title_recipe = result.find("div", {"data-cy": "title-recipe"})

        if title_recipe is None:
            return None

        release_span = title_recipe.find(
            "span", {"class": "a-size-base a-color-secondary a-text-normal"}
        )

        if release_span is None:
            return None

        release_text = release_span.getText().strip()

        try:
            return datetime.datetime.strptime(release_text, "%b %d, %Y")
        except ValueError:
            print(f"Failed to parse {release_text}")
            return None

    def split_title(
        self, title: str, separator: str, platform: Optional[ExcelPlatform]
    ) -> Tuple[str, Optional[ExcelPlatform]]:
        parts = title.split(separator)

        if len(parts) == 1:
            return (title, platform)

        if platform is None:
            platform = self.try_get_platform(parts[-1])

        return (parts[0], platform)

    def clean_title_with_platform(
        self, title: str
    ) -> Tuple[str, Optional[ExcelPlatform]]:
        paren_re = r"\((?P<platform>[^\)]*)\)"
        platform: Optional[ExcelPlatform] = None

        re_match = re.search(paren_re, title)

        if re_match is not None:
            platform = self.try_get_platform(re_match.group("platform"))

        title = re.sub(paren_re, "", title).strip()

        title, platform = self.split_title(title, " - ", platform)

        # EM DASH used sometimes
        title, platform = self.split_title(title, " – ", platform)

        return (title, platform)

    def get_price_from_result(self, result: Any) -> Optional[float]:
        price_recipe = result.find("div", {"data-cy": "price-recipe"})

        if price_recipe is None:
            return None

        whole = price_recipe.find("span", {"class": "a-price-whole"})
        fraction = price_recipe.find("span", {"class": "a-price-fraction"})

        if whole is None and fraction is None:
            return None

        leading = 0

        if whole is not None:
            leading = int(whole.getText().strip().replace(".", ""))

        decimal = 0

        if fraction is not None:
            decimal = int(fraction.getText().strip()) / 100

        return leading + decimal

    def get_url_from_result(self, result: Any) -> Optional[str]:
        title_recipe = result.find("div", {"data-cy": "title-recipe"})

        a_block = title_recipe.find("a", {"class": "a-link-normal"})

        if a_block is None or not a_block.has_attr("href"):
            return None

        return f"{self.__BASE_AMAZON_URL}{a_block['href']}"

    def get_id_from_result(self, result: Any) -> Optional[str]:
        if not result.has_attr("data-asin"):
            return None

        return result["data-asin"]

    async def get_upcoming_games(self) -> Dict[ExcelPlatform, List[AmazonResult]]:
        async for results in self.search_paginated():
            unreleased = self.get_unreleased_from_results(results)

            for ur in unreleased:
                title = self.get_title_from_result(ur)
                platform = self.get_platform_from_result(ur)

                title, title_platform = self.clean_title_with_platform(title)

                if platform is None and title_platform is None:
                    print(f"Skipped {title} <> {platform}")
                    continue

                platform_enum = title_platform or self.try_get_platform(platform)

                if platform_enum is None:
                    print(f"Skipped {title} <> {platform}")
                    continue

                release_date = self.get_release_date_from_result(ur)
                price = self.get_price_from_result(ur)
                url = self.get_url_from_result(ur)
                _id = self.get_id_from_result(ur)

                self.try_add_upcoming_game(
                    platform_enum,
                    AmazonResult(title, platform_enum, release_date, price, url, _id),
                )

        return self.upcoming_games

    async def get_unordered_games(self) -> Dict[ExcelPlatform, List[AmazonResult]]:
        loader = ExcelLoader()
        upcoming_games = await self.get_upcoming_games()

        for game in loader.games_on_order:
            if game.platform is None:
                continue
            if game.platform not in upcoming_games:
                continue

            to_remove: Optional[AmazonResult] = None

            for upcoming_game in upcoming_games[game.platform]:
                if self.validator.titles_equal_normalized(
                    game.title, upcoming_game.title
                ):
                    to_remove = upcoming_game
                    break
                if self.validator.titles_equal_fuzzy(game.title, upcoming_game.title):
                    should_remove = input(
                        f"Does {game.full_name} match {upcoming_game.title} ({upcoming_game.url})? (y/n)"
                    )

                    if should_remove.lower().strip() == "y":
                        to_remove = upcoming_game
                        break

            if to_remove is not None:
                upcoming_games[game.platform].remove(to_remove)

        return upcoming_games
