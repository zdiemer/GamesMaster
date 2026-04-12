import asyncio
import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, ResultSet

from excel_game import ExcelPlatform
from clients import ShoppingClientBase, BaseResult
from match_validator import MatchValidator


class AmazonResult(BaseResult):
    def __init__(
        self,
        title: str,
        platform: ExcelPlatform,
        release_date: datetime.datetime,
        price: float,
        url: str,
        _id: str,
    ):
        super().__init__(_id, platform, price, release_date, title, url)


class AmazonClient(ShoppingClientBase):
    __BASE_AMAZON_URL: str = "https://www.amazon.com"
    __VIDEO_GAMES_URL: str = __BASE_AMAZON_URL + "/s"
    pages_without_unreleased_threshold: int

    upcoming_games: Dict[ExcelPlatform, List[AmazonResult]]

    def __init__(
        self,
        silent: bool = False,
        pages_without_unreleased_threshold: int = 5,
        max_pages: int = 400,
    ):
        self.pages_without_unreleased_threshold = pages_without_unreleased_threshold
        super().__init__(
            silent=silent,
            max_pages=max_pages,
            use_vpn=True,
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

    def is_unreleased_result(self, result: Any) -> bool:
        release_date = self.get_release_date_from_result(result)

        if release_date is None or datetime.datetime.now() > release_date:
            return False

        return True

    async def get_search_results(self, page: int = 1) -> ResultSet[Any]:
        html = await self.search(page=page)
        soup = BeautifulSoup(html, "html.parser")
        return soup.find_all("div", {"data-component-type": "s-search-result"})

    async def search_paginated(self) -> AsyncGenerator[ResultSet[Any], None]:
        page = 1
        pages_without_unreleased = 0
        results = await self.get_search_results(page)

        yield results

        while (
            results is not None
            and pages_without_unreleased < self.pages_without_unreleased_threshold
            and page < self.max_pages
        ):
            if not any(self.get_unreleased_from_results(results)):
                pages_without_unreleased += 1
            else:
                pages_without_unreleased = 0

            page += 1
            if not self.silent:
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
                if not self.silent:
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
            if not self.silent:
                print(f"Failed to parse {release_text}")
            return None

    def get_price_from_result(self, result: Any) -> Optional[float]:
        price_recipe = result.find("div", {"data-cy": "price-recipe"})

        if price_recipe is None:
            return None

        whole = price_recipe.find("span", {"class": "a-price-whole"})
        fraction = price_recipe.find("span", {"class": "a-price-fraction"})

        if whole is None and fraction is None:
            return None

        leading = 0.0

        if whole is not None:
            leading = float(whole.getText().strip().replace(".", ""))

        decimal = 0.0

        if fraction is not None:
            decimal = float(fraction.getText().strip()) / 100

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
                    if not self.silent:
                        print(
                            f"Skipped {title} <> {platform} due to no platform or title platform"
                        )
                    continue

                platform_enum = title_platform or self.try_get_platform(platform)

                if platform_enum is None:
                    if not self.silent:
                        print(f"Skipped {title} <> {platform} due to unmapped enum")
                    continue

                release_date = self.get_release_date_from_result(ur)
                price = self.get_price_from_result(ur)
                url = self.get_url_from_result(ur)
                _id = self.get_id_from_result(ur)

                if not isinstance(price, float | None):
                    print(type(price))

                self.try_add_upcoming_game(
                    platform_enum,
                    AmazonResult(
                        title,
                        platform_enum,
                        release_date,
                        price or 0.0,
                        urljoin(url, urlparse(url).path),
                        _id,
                    ),
                )

        return self.upcoming_games


if __name__ == "__main__":
    client = AmazonClient(MatchValidator())

    unordered_games = asyncio.run(client.get_unordered_games())
