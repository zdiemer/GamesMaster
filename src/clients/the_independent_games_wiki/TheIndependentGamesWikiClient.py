from typing import Any, List

from bs4 import BeautifulSoup

from clients import ClientBase
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator


class TheIndependentGamesWikiClient(ClientBase):
    def __init__(self, validator: MatchValidator = None, config: Config = None):
        validator = validator or MatchValidator()
        config = config or Config.create()
        super().__init__(validator, config, base_url="https://tig.fandom.com")

    async def search(self, title: str) -> List[Any]:
        return await self.get(
            f"{self.base_url}/wikia.php",
            params={
                "controller": "UnifiedSearchSuggestions",
                "method": "getSuggestions",
                "query": title,
                "format": "json",
                "scope": "internal",
            },
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.digital_platform != "Freeware"

    async def get_results(self, game: ExcelGame) -> List[Any]:
        search_results = await self.search(game.title)

        if not search_results or not search_results.get("suggestions"):
            return []

        return search_results["suggestions"]

    async def result_to_match(
        self, game: ExcelGame, result: str, is_fallback: bool = False
    ) -> GameMatch | None:
        if not self.validator.titles_equal_normalized(
            game.title, result
        ) or not self.validator.titles_equal_fuzzy(game.title, result):
            return None

        url = f"{self.base_url}/wiki/{result.replace(' ', '_')}"

        html = await self.get(
            url,
            json=False,
        )

        soup = BeautifulSoup(html, "html.parser")

        match_info = {
            "name": result,
            "url": url,
        }

        page_content = soup.find("div", {"class": "page-content"})

        if not page_content:
            return None

        infobox = page_content.find("table", {"class": "infobox"})

        if infobox:
            match_info["wiki_content"] = "\n".join(
                sibling.get_text(strip=True, separator="\n")
                for sibling in infobox.find_next_siblings()
            )

            for row in infobox.find_all("tr"):
                if row.th:
                    continue
                if row.img:
                    match_info["image_url"] = row.img.get("src")
                    continue

                label, value = row.find_all("td", limit=2)

                label = label.get_text(strip=True)
                value = value.get_text(strip=True)

                match_info[label] = value

                if "release" in label.lower():
                    match_info["release_date"] = self.try_parse_date(value)

        match = self.validator.validate(
            game,
            result,
            [game.platform.value],
            [
                (
                    match_info["release_date"].year
                    if match_info.get("release_date")
                    else None
                )
            ],
        )

        if match.likely_match:
            return GameMatch(result, url, result, match_info, match)

        return None
