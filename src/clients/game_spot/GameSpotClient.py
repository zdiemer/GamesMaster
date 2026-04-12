import datetime
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Tuple

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator


class GameSpotClient(ClientBase):
    BASE_URL: str = "http://www.gamespot.com/api"
    GAME_SPOT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        validator: MatchValidator,
        config: Config = None,
    ):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            RateLimit(200, per=DatePart.HOUR),
        )

    async def _make_request(
        self,
        route: str = "",
        params: Optional[Dict[str, Any]] = None,
        site_detail_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        params = params or {}

        if params.get("api_key") is None:
            params["api_key"] = self._config.game_spot_api_key

        if params.get("format") is None:
            params["format"] = "json"

        base_url = (
            site_detail_url
            if site_detail_url is not None
            else f"{self.BASE_URL}/{route}"
        )

        return await self.get(base_url, params=params)

    async def _base_request(
        self,
        route: str,
        _format: Literal["xml", "json", "jsonp"] = "json",
        field_list: List[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[Tuple[str, Literal["asc", "desc"]]] = None,
        field_filters: List[Tuple[str, str]] = None,
        date_filter: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
        associated_guid: str = "",
    ) -> Optional[Dict[str, Any]]:
        sort_value = ""
        if sort is not None:
            field, direction = sort
            sort_value = f"{field}:{direction}"

        filters = [f"{field}:{value}" for field, value in field_filters or []]

        if date_filter is not None:
            start, end = date_filter
            filters.append(
                f"release_date:{start.strftime(self.GAME_SPOT_DATE_FORMAT)}|{end.strftime(self.GAME_SPOT_DATE_FORMAT)}"
            )

        if any(associated_guid):
            filters.append(f"association:{associated_guid}")

        _filter = ",".join(filters)

        params = {
            "format": _format,
            "field_list": ",".join(field_list or []),
            "limit": limit,
            "offset": offset,
            "sort": sort_value,
            "filter": _filter,
        }

        return await self._make_request(route, params=params)

    async def games(
        self, title: str, limit: int = 100, offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        return await self._base_request(
            "games",
            limit=limit,
            offset=offset,
            field_filters=[("name", self.validator.romanize(title.replace("<", "")))],
        )

    async def releases(
        self, guid: str, limit: int = 100, offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        return await self._base_request(
            "releases", limit=limit, offset=offset, associated_guid=guid
        )

    async def _games_paginated(
        self,
        title: str,
        limit: int = 100,
        offset: int = 0,
        max_pages: int = 10,
    ) -> AsyncGenerator[Optional[Dict[str, Any]], None]:
        results = await self.games(title, limit, offset)

        yield results

        while (
            offset / limit < max_pages - 1
            and results.get("results") is not None
            and len(results["results"]) == limit
        ):
            offset += limit
            results = await self.games(title, limit, offset)
            yield results

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        matches: List[GameMatch] = []

        async for response in self._games_paginated(game.title):
            if (
                response is None
                or (results := response.get("results")) is None
                or not any(results)
            ):
                continue

            for result in results:
                try:
                    release_date = datetime.datetime.strptime(
                        result["release_date"], self.GAME_SPOT_DATE_FORMAT
                    )
                except ValueError:
                    release_date = None

                match = self.validator.validate(
                    game,
                    result["name"],
                    release_years=[
                        release_date.year if release_date is not None else None
                    ],
                )

                if match.matched:
                    release_response = await self._make_request(
                        site_detail_url=result["releases_api_url"]
                    )

                    releases = None

                    if (
                        release_response is not None
                        and (releases := release_response.get("results")) is not None
                        and any(releases)
                    ):
                        release_years = [
                            datetime.datetime.strptime(
                                release["release_date"], self.GAME_SPOT_DATE_FORMAT
                            ).year
                            for release in releases
                        ]

                        platforms = [release["platform"] for release in releases]

                        match.date_matched = (
                            match.date_matched
                            or self.validator.verify_release_year(
                                game.release_year, release_years
                            )
                        )

                        match.platform_matched = self.validator.verify_platform(
                            game.platform, platforms
                        )

                    if match.likely_match:
                        match_info = result
                        match_info["release_info"] = releases

                        matches.append(
                            GameMatch(
                                result["name"],
                                result["site_detail_url"],
                                result["id"],
                                match_info,
                                match,
                            )
                        )

            if any(m.is_guaranteed_match() for m in matches):
                break

        return matches
