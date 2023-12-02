from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Literal, Optional

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelRegion
from game_match import GameMatch
from match_validator import MatchValidator


class GameyeClient(ClientBase):
    __BASE_GAMEYE_URL = "https://www.gameye.app/api"
    __EDITION_REGEX = r"( [\[\(](?P<edition>.*)[\]\)]$)"

    __REGION_COUNTRY_MAPPINGS: Dict[ExcelRegion, List[int]] = {
        ExcelRegion.ASIA: [3, 9, 20, 22, 23],
        ExcelRegion.BRAZIL: [4],
        ExcelRegion.GERMANY: [5],
        ExcelRegion.EUROPE: [5, 6, 14, 15, 16, 17, 19, 21, 24],
        ExcelRegion.FRANCE: [14],
        ExcelRegion.JAPAN: [3],
        ExcelRegion.KOREA: [20],
        ExcelRegion.NORTH_AMERICA: [1, 2],
    }

    __platforms: Dict[str, Any] = None
    __companies: Dict[str, Any] = None

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            RateLimit(500, DatePart.HOUR),
            immediately_stop_statuses=[429],
        )

    async def _make_request(
        self, route: str, params: Dict[str, Any] = dict()
    ) -> Dict[str, Any]:
        return await self.get(f"{self.__BASE_GAMEYE_URL}/{route}", params=params)

    async def deep_search(
        self, title: str, offset: int = 0, limit: Literal[25, 50, 100] = 100
    ) -> Dict[str, Any]:
        return await self._make_request(
            "deep_search",
            {
                "offset": offset,
                "limit": limit,
                "title": title,
                "order": 0,
                "asc": 1,
                "cat": 0,
            },
        )

    async def items(self, iid: int) -> Dict[str, Any]:
        return await self._make_request(f"items/{iid}")

    async def platforms(self) -> Dict[str, Any]:
        return await self._make_request("platforms")

    async def meta(self) -> Dict[str, Any]:
        return await self._make_request("meta")

    async def companies(self) -> Dict[str, Any]:
        return await self._make_request("companies")

    async def genres(self) -> Dict[str, Any]:
        return await self._make_request("genres")

    def should_skip(self, game: ExcelGame) -> bool:
        return game.owned_format not in ("Both", "Physical")

    def __get_match_from_record(
        self, game: ExcelGame, record: Dict[str, Any]
    ) -> Optional[GameMatch]:
        title_without_edition = record["title"]

        if any(game.notes) and "edition" in game.notes.lower():
            re_matches = re.search(self.__EDITION_REGEX, record["title"])

            if re_matches is not None:
                edition_match = re_matches.group("edition")

                edition_match = edition_match.lower().replace(" edition", "")
                notes = game.notes.lower().replace(" edition", "")

                if notes != edition_match:
                    return None

        title_without_edition = re.sub(self.__EDITION_REGEX, "", title_without_edition)

        year = (
            [datetime.datetime.fromtimestamp(record["release_date"]).year]
            if record["release_date"] is not None
            else None
        )

        match = self.validator.validate(
            game,
            title_without_edition,
            [
                next(
                    p["name"]
                    for p in self.__platforms["platforms"]
                    if p["id"] == record["platform_id"]
                )
            ],
            year,
            [
                c["name"]
                for c in filter(
                    lambda _c: _c["id"] in record["pubs"],
                    self.__companies["companies"],
                )
            ]
            if record["pubs"] is not None
            else None,
            [
                c["name"]
                for c in filter(
                    lambda _c: _c["id"] in record["devs"],
                    self.__companies["companies"],
                )
            ]
            if record["devs"] is not None
            else None,
        )

        if match.likely_match:
            return GameMatch(
                record["title"],
                f"{self.__BASE_GAMEYE_URL.replace('/api', '')}/encyclopedia/{record['id']}",
                record["id"],
                record,
                match,
            )

        return None

    def __process_results(
        self, game: ExcelGame, results: Dict[str, Any]
    ) -> List[GameMatch]:
        matches: List[GameMatch] = []
        default_records: List[Any] = []

        if (
            results is None
            or "records" not in results
            or results["records"] is None
            or not any(results["records"])
        ):
            return matches

        for record in results["records"]:
            if any(m.is_guaranteed_match() for m in matches):
                break

            if record["release_type"] != 0:
                continue

            if (
                record["country_id"]
                not in self.__REGION_COUNTRY_MAPPINGS[game.release_region]
            ):
                if (
                    record["country_id"] == 34
                    or record["country_id"]
                    in self.__REGION_COUNTRY_MAPPINGS[ExcelRegion.NORTH_AMERICA]
                    or (
                        record["country_id"]
                        in self.__REGION_COUNTRY_MAPPINGS[ExcelRegion.JAPAN]
                        and game.release_region == ExcelRegion.ASIA
                    )
                    or (
                        record["country_id"]
                        in self.__REGION_COUNTRY_MAPPINGS[ExcelRegion.ASIA]
                        and game.release_region == ExcelRegion.JAPAN
                    )
                ):
                    default_records.append(record)
                continue

            match = self.__get_match_from_record(game, record)

            if match is not None:
                matches.append(match)

        if not any(matches) and any(default_records):
            for default in default_records:
                if any(m.is_guaranteed_match() for m in matches):
                    break

                match = self.__get_match_from_record(game, default)

                if match is not None:
                    matches.append(match)

        return matches

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        matches: List[GameMatch] = []

        if self.__platforms is None:
            self.__platforms = await self.platforms()
        if self.__companies is None:
            self.__companies = await self.companies()

        offset = 0
        limit = 100

        results = await self.deep_search(game.title, offset, limit)
        matches.extend(self.__process_results(game, results))

        while (
            results["records"] is not None
            and len(results["records"]) == limit
            and not any(m.is_guaranteed_match() for m in matches)
        ):
            offset += limit
            results = await self.deep_search(game.title, offset, limit)
            matches.extend(self.__process_results(game, results))

        return matches
