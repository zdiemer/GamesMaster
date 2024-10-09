from __future__ import annotations

import datetime
import json
import re
from typing import AsyncGenerator, List

from bs4 import BeautifulSoup

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator

from .HltbResult import HltbResult


class HltbClient(ClientBase):
    __BASE_URL = "https://howlongtobeat.com"
    __GAME_URL = __BASE_URL + "/game"
    __SEARCH_URL = __BASE_URL + "/api/search"
    __PAGE_SIZE = 20

    __version_string: str = None

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(1, DatePart.SECOND))

    async def search(
        self, game: str, page: int = 1, page_size: int = __PAGE_SIZE
    ) -> dict:
        if self.__version_string is None:
            main = await self.get(
                self.__BASE_URL, headers=self.__htlb_headers(), json=False
            )

            soup = BeautifulSoup(main, "html.parser")
            sources = soup.find_all("script")

            build_manifest = next(
                filter(
                    lambda s: s.has_attr("src")
                    and re.search(r"\/_next\/static\/.*\/_buildManifest\.js", s["src"])
                    is not None,
                    sources,
                )
            )

            manifest = await self.get(
                f"{self.__BASE_URL}{build_manifest['src']}",
                headers=self.__htlb_headers(),
                json=False,
            )

            submit_pattern = r"\"\/submit\":\[\"static\/css\/.*\.css\",\"(?P<submit>static\/chunks\/pages\/submit-[^\.]*\.js)\"\]"

            match = re.search(submit_pattern, manifest)

            if match is None:
                raise ValueError

            submit_script = await self.get(
                f"{self.__BASE_URL}/_next/{match.group('submit')}",
                headers=self.__htlb_headers(),
                json=False,
            )

            version_pattern = r"\"\/api\/search\/\"\.concat\(\"(?P<version>[^\"]*)\"\)"

            match = re.search(version_pattern, submit_script)

            if match is None:
                raise ValueError

            self.__version_string = match.group("version")

        return await self.post(
            f"{self.__SEARCH_URL}/{self.__version_string}",
            data=json.dumps(
                {
                    "searchType": "games",
                    "searchTerms": [game],
                    "searchPage": page,
                    "size": page_size,
                    "searchOptions": {
                        "games": {
                            "userId": 0,
                            "platform": "",
                            "sortCategory": "popular",
                            "rangeCategory": "main",
                            "rangeTime": {"min": None, "max": None},
                            "gameplay": {"perspective": "", "flow": "", "genre": ""},
                            "rangeYear": {"min": "", "max": ""},
                            "modifier": "",
                        },
                        "users": {"sortCategory": "postcount"},
                        "lists": {"sortCategory": "follows"},
                        "filter": "",
                        "sort": 0,
                        "randomizer": 0,
                    },
                    "useCache": False,
                }
            ),
            headers=self.__htlb_headers(),
        )

    async def game(self, game_id: int) -> any:
        return await self.get(
            f"{self.__GAME_URL}/{game_id}", headers=self.__htlb_headers(), json=False
        )

    def __htlb_headers(self):
        return {
            "content-type": "application/json",
            "accept": "*/*",
            "User-Agent": self._get_headers(self.__SEARCH_URL)["User-Agent"],
            "referer": self.__BASE_URL,
        }

    async def __search_paginated(self, game: ExcelGame) -> AsyncGenerator[dict, None]:
        page = 1

        results = await self.search(game.title, page=page)

        yield results

        while page < results["pageTotal"]:
            page += 1
            results = await self.search(game.title, page=page)
            yield results

    def should_skip(self, game: ExcelGame) -> bool:
        return game.completed or game.release_date is None

    async def result_to_match(
        self, game: ExcelGame, result: json.Any
    ) -> GameMatch | None:
        if result["comp_main"] == 0:
            return None

        match = self.validator.validate(
            game, result["game_name"], release_years=[result["release_world"]]
        )

        if match.matched:
            html = await self.game(result["game_id"])
            soup = BeautifulSoup(html, "html.parser")

            platform_blocks = soup.find(
                "div",
                {"class": "GameSummary_profile_info__HZFQu GameSummary_medium___r_ia"},
            )

            platforms = list(platform_blocks)[-1].getText().strip().split(", ")
            match.platform_matched = self.validator.verify_platform(
                game.platform.value, platforms
            )

            if not match.date_matched:
                date_blocks = soup.find_all(
                    "div", {"class": "GameSummary_profile_info__HZFQu"}
                )

                release_years = set()

                for date_block in date_blocks:
                    text = date_block.getText().strip()

                    if (
                        text.startswith("NA:")
                        or text.startswith("EU:")
                        or text.startswith("JP:")
                    ):
                        text = (
                            text.replace("NA: ", "")
                            .replace("EU: ", "")
                            .replace("JP: ", "")
                        )

                        # Full Date
                        try:
                            parsed_date = datetime.datetime.strptime(text, "%B %d, %Y")
                            release_years.add(parsed_date.year)
                        except ValueError:
                            pass

                        # Year and Month
                        try:
                            parsed_date = datetime.datetime.strptime(text, "%B %Y")
                            release_years.add(parsed_date.year)
                        except ValueError:
                            pass

                        # Just Year
                        try:
                            parsed_year = int(text)
                            release_years.add(parsed_year)
                        except ValueError:
                            pass

                if any(release_years):
                    match.date_matched = self.validator.verify_release_year(
                        game.release_year, list(release_years)
                    )

            if match.likely_match:
                return GameMatch(
                    result["game_name"],
                    f"{self.__GAME_URL}/{result['game_id']}",
                    result["game_id"],
                    HltbResult(result["comp_main"]),
                    match,
                )

            return None

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        matches: List[GameMatch] = []

        async for results in self.__search_paginated(game):
            for result in results["data"]:
                if any(m.is_guaranteed_match() for m in matches):
                    break

                match = await self.result_to_match(game, result)

                if match is not None:
                    matches.append(match)

            if any(m.is_guaranteed_match() for m in matches):
                break

        return matches
