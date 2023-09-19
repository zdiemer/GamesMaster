from __future__ import annotations

import asyncio
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from clients.ClientBase import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator, ValidationInfo


class IgdbClient(ClientBase):
    __BASE_TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token?"
    __BASE_IGDB_URL = "https://api.igdb.com/v4"

    __access_token: str
    __auth_expiration: datetime
    __client_id: str
    __client_secret: str
    __platforms: List[Dict]

    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config, RateLimit(4, DatePart.SECOND))
        self.__client_id = config.igdb_client_id
        self.__client_secret = config.igdb_client_secret
        self.__platforms = {}
        self.__auth_expiration = datetime.utcnow() - timedelta(seconds=30)

    async def _authorize(self):
        res = await self.post(
            self.__BASE_TWITCH_AUTH_URL,
            params={
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
                "grant_type": "client_credentials",
            },
        )
        self.__access_token = res["access_token"]
        self.__auth_expiration = datetime.utcnow() + timedelta(
            seconds=res["expires_in"]
        )

    async def _make_request(self, route: str, data: str):
        if datetime.utcnow() > self.__auth_expiration:
            await self._authorize()

        return await self.post(
            f"{self.__BASE_IGDB_URL}/{route}", headers=self._get_headers(), data=data
        )

    def _get_headers(self):
        if self.__access_token is None:
            raise RuntimeError
        return {
            "User-Agent": self._config.user_agent,
            "Client-ID": self.__client_id,
            "Authorization": f"Bearer {self.__access_token}",
        }

    async def _init_platforms(self):
        platforms = await self.platforms("fields name; limit 500;")
        for p in platforms:
            self.__platforms[int(p["id"])] = p["name"]

    async def alternative_names(self, data: str):
        return await self._make_request("alternative_names/", data)

    async def games(self, data: str):
        return await self._make_request("games/", data)

    async def platforms(self, data: str):
        return await self._make_request("platforms/", data)

    async def release_dates(self, data: str):
        return await self._make_request("release_dates/", data)

    async def match_game(
        self, game: ExcelGame
    ) -> List[Tuple[GameMatch, ValidationInfo]]:
        if not any(self.__platforms):
            await self._init_platforms()

        processed_title = unicodedata.normalize("NFKD", game.title).replace('"', '\\"')
        search_data = f'search "{processed_title}"; fields alternative_names,id,name,platforms,genres,parent_game,url,release_dates;'.encode(
            "utf-8"
        )

        results = await self.games(search_data)
        matches: List[Tuple[GameMatch, ValidationInfo]] = []
        validator = MatchValidator()

        for r in results:
            platforms = r.get("platforms") or []

            platforms_processed = [self.__platforms[p] for p in platforms]

            release_years = []

            date_responses = [
                await self.release_dates(f"fields date; where id = {rid};")
                for rid in (r.get("release_dates") or [])
            ]

            for date_response in date_responses:
                if len(date_response) != 1 or date_response[0].get("date") is None:
                    continue
                release_years.append(
                    datetime.fromtimestamp(date_response[0]["date"]).year
                )

            if not any(release_years):
                continue

            match = validator.validate(
                game, r.get("name"), platforms_processed, release_years
            )

            if match.matched:
                matches.append((GameMatch(r["name"], r["url"], r["id"], r), match))
            elif r.get("alternative_names") is not None:
                for alt in r["alternative_names"]:
                    names = await self.alternative_names(
                        f"fields name; where id = {alt};"
                    )

                    if len(names) != 1:
                        continue

                    match = validator.validate(
                        game, names[0].get("name"), platforms_processed, release_years
                    )

                    if match.matched:
                        matches.append(
                            (GameMatch(r["name"], r["url"], r["id"], r), match)
                        )

        return matches
