from __future__ import annotations

import datetime
import json
import re
from typing import AsyncGenerator, List

from bs4 import BeautifulSoup

from clients import ClientBase, DatePart, RateLimit, ResponseNotOkError
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator

from .HltbResult import HltbResult


class HltbClient(ClientBase):
    __BASE_URL = "https://howlongtobeat.com"
    __GAME_URL = __BASE_URL + "/game"
    __SEARCH_URL = __BASE_URL + "/api/locate"
    __PAGE_SIZE = 20

    __version_string: str = None

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(1, DatePart.SECOND))

    async def __update_version_string(self):
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

        version_pattern = r"\"\/api\/locate\/\"\.concat\(\"(?P<version>[^\"]*)\"\)\.concat\(\"(?P<version2>[^\"]*)\"\)"

        match = re.search(version_pattern, submit_script)

        if match is None:
            raise ValueError

        self.__version_string = match.group("version") + match.group("version2")

    async def search(
        self, game: str, page: int = 1, page_size: int = __PAGE_SIZE, modifier: str = ""
    ) -> dict:
        if self.__version_string is None:
            await self.__update_version_string()

        try:
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
                                "gameplay": {
                                    "perspective": "",
                                    "flow": "",
                                    "genre": "",
                                    "difficulty": "",
                                },
                                "rangeYear": {"min": "", "max": ""},
                                "modifier": modifier,
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
        except ResponseNotOkError:
            old_version = self.__version_string
            await self.__update_version_string()
            if old_version != self.__version_string:
                return await self.search(game, page, page_size, modifier)

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

        results = await self.search(
            game.title, page=page, modifier="hide_dlc" if not game.dlc else "only_dlc"
        )

        yield results

        while page < results["pageTotal"]:
            page += 1
            results = await self.search(
                game.title,
                page=page,
                modifier="hide_dlc" if not game.dlc else "only_dlc",
            )
            yield results

    def should_skip(self, game: ExcelGame) -> bool:
        return game.release_date is None

    async def result_to_match(
        self, game: ExcelGame, result: json.Any, is_fallback: bool = False
    ) -> GameMatch | None:
        if result.get("comp_main", 0) == 0:
            return None

        match = self.validator.validate(
            game,
            [result["game_name"], *result["game_alias"].split(", ")],
            platforms=result["profile_platform"].split(", "),
            release_years=[result["release_world"]],
        )

        if match.likely_match:
            return GameMatch(
                result["game_name"],
                f"{self.__GAME_URL}/{result['game_id']}",
                result["game_id"],
                HltbResult(
                    result["comp_main"],
                    result["comp_plus"],
                    result["comp_100"],
                    result["comp_all"],
                    result["comp_main_count"],
                    result["comp_plus_count"],
                    result["comp_100_count"],
                    result["comp_all_count"],
                ),
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
