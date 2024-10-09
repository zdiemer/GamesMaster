import asyncio
from typing import Any, Dict, List, Optional

from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry
from steam import webapi

import clients
import clients.game_faqs
from config import Config
from game_match import GameMatch
from excel_game import ExcelGame, ExcelPlatform
from match_validator import MatchValidator


class SteamWrapper(clients.ClientBase):
    """Wrapper class for third-party Steam client.

    SteamWrapper implements the clients.ClientBase match_game function
    and wraps a third-party Steam client library for fetching information
    about games from Steam.

    Attributes:
        _client: A Steam object which represents the underlying Steam client
    """

    _client: webapi.WebAPI
    _applist: dict

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator, config, clients.RateLimit(5, clients.DatePart.SECOND)
        )
        self._client = webapi.WebAPI(
            config.steam_web_api_key, auto_load_interfaces=True
        )
        self._applist = self._client.ISteamApps.GetAppList_v2()

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform != ExcelPlatform.PC

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        async def do_search() -> Dict[str, list]:
            res = self._client.apps.search_games(game.title)
            await asyncio.sleep(0)
            return res

        max_retries = 3
        retries = 0
        should_retry = True
        results: Optional[List[Any]] = []

        while should_retry and retries < max_retries:
            try:
                results = await self._rate_limiter.request("steam", do_search)
                should_retry = False
            except Exception:  # pylint: disable=broad-except
                retries += 1
                should_retry = True

        if results is None or retries == max_retries:
            return []

        matches: List[GameMatch] = []

        for res in results["apps"]:
            match = self.validator.validate(game, res["name"])
            match.platform_matched = True
            match.date_matched = True
            if match.matched:
                matches.append(
                    GameMatch(res["name"], res["link"], res["id"], res, match)
                )

        return matches


class HLTBWrapper(clients.ClientBase):
    """Wrapper class for third-party How Long to Beat client.

    HLTBWrapper implements the clients.ClientBase match_game function
    and wraps a third-party How Long to Beat client library for fetching
    information about games from How Long to Beat.
    """

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator, config, clients.RateLimit(5, clients.DatePart.SECOND)
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        async def do_search() -> Optional[List[HowLongToBeatEntry]]:
            res = await HowLongToBeat().async_search(game.title)
            return res

        max_retries = 3
        retries = 0
        should_retry = True
        results: Optional[List[HowLongToBeatEntry]] = []

        while should_retry and retries < max_retries:
            try:
                results = await self._rate_limiter.request("hltb", do_search)
                should_retry = False
            except Exception:  # pylint: disable=broad-except
                retries += 1
                should_retry = True

        if results is None or retries == max_retries:
            return []

        matches: List[GameMatch] = []

        for res in results:
            match = self.validator.validate(
                game,
                res.game_name,
                res.profile_platforms,
                [res.release_world],
                developers=[res.profile_dev],
            )

            if match.likely_match:
                matches.append(
                    GameMatch(
                        res.game_name,
                        res.game_web_link,
                        res.game_id,
                        res,
                        match,
                    )
                )
                continue

            match = self.validator.validate(
                game, res.game_alias, res.profile_platforms, [res.release_world]
            )

            if match.likely_match:
                matches.append(
                    GameMatch(
                        res.game_name,
                        res.game_web_link,
                        res.game_id,
                        res,
                        match,
                    )
                )

        return matches
