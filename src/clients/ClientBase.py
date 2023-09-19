from __future__ import annotations

import aiohttp
import asyncio
import random
import urllib.parse
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

from fake_headers import Headers

from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator


class ResponseNotOkError(Exception):
    pass


class DatePart(Enum):
    SECOND = 1
    MINUTE = 2
    HOUR = 3
    DAY = 4
    WEEK = 5
    MONTH = 6
    YEAR = 7


class RateLimit:
    max_req: int
    per: DatePart
    rate_limit_per_route: bool
    get_route_path: Optional[Callable[[str], str]]

    def __init__(
        self,
        max_req: int = 1,
        per: DatePart = DatePart.SECOND,
        rate_limit_per_route: bool = False,
        get_route_path: Optional[Callable[[str], str]] = None,
    ):
        self.max_req = max_req
        self.per = per
        self.rate_limit_per_route = rate_limit_per_route
        self.get_route_path = get_route_path

        if self.rate_limit_per_route and self.get_route_path is None:
            raise ValueError(
                "Must specify `get_route_path` when `rate_limit_per_route` is True"
            )


class ExponentialBackoff:
    max_backoffs: int
    backoff_seconds: int
    exponent: int
    _backoffs: int

    def __init__(
        self, initial_backoff: int = 2, exponent: int = 2, max_backoffs: int = 2
    ):
        self.backoff_seconds = initial_backoff
        self.exponent = exponent
        self.max_backoffs = max_backoffs
        self._backoffs = 0

    async def backoff(self, url: str, status: int):
        if self._backoffs + 1 > self.max_backoffs:
            raise ResponseNotOkError
        print(f"Backing off for {self.backoff_seconds}s for {url} due to {status}")
        await asyncio.sleep(self.backoff_seconds + random.random())
        self.backoff_seconds **= self.exponent
        self._backoffs += 1


class RateLimiter:
    _settings: RateLimit
    _last_calls: Dict[str, datetime]

    def __init__(self, limit: RateLimit = RateLimit()):
        self._settings = limit
        self._last_calls = {}

    @property
    def seconds_between_requests(self) -> float:
        per = self._settings.per
        _max = self._settings.max_req
        if per == DatePart.SECOND:
            return 1.0 / _max
        if per == DatePart.MINUTE:
            return 1.0 / (_max / 60.0)
        if per == DatePart.HOUR:
            return 1.0 / (_max / 3600.0)
        if per == DatePart.DAY:
            return 1.0 / (_max / 86_400.0)
        if per == DatePart.WEEK:
            return 1.0 / (_max / 604_800.0)
        if per == DatePart.MONTH:
            return 1.0 / (_max / 2.628e6)
        if per == DatePart.YEAR:
            return 1.0 / (_max / 3.154e7)

    def next_call(self, key: str, now: datetime = datetime.utcnow()) -> datetime:
        if key not in self._last_calls:
            return now

        return self._last_calls[key] + timedelta(
            seconds=self.seconds_between_requests + random.random()
        )

    async def request(
        self, url: str, func: Coroutine[Any, Any, Union[str, Any]]
    ) -> Union[str, Any]:
        key = (
            urllib.parse.urlparse(url).netloc
            if not self._settings.rate_limit_per_route
            else self._settings.get_route_path(url)
        )

        utcnow = datetime.utcnow()
        next_call = self.next_call(key, utcnow)

        if next_call > utcnow:
            delta = next_call - utcnow
            sleep_time_seconds = delta.seconds + (delta.microseconds / 1_000_000.0)
            if sleep_time_seconds >= 5.0:
                print(f"Throttling {sleep_time_seconds:,.2f}s for {url}")
            await asyncio.sleep(sleep_time_seconds)

        self._last_calls[key] = datetime.utcnow()
        return await func()


class ClientBase:
    __SPOOF_HEADER_LIFETIME_MINUTES: int = 5

    __cached_headers: Optional[dict]
    __cached_responses: Dict[int, Union[Any, str]]
    __default_headers: Dict[str, str]
    __next_headers: datetime
    __rate_limiter: RateLimiter
    __spoof_headers: bool

    _config: Config

    validator: MatchValidator

    def __init__(
        self,
        validator: MatchValidator,
        config: Config = None,
        limit: RateLimit = RateLimit(),
        spoof_headers: bool = False,
    ):
        self.validator = validator
        self._config = config or Config.create()
        self.__default_headers = {"User-Agent": self._config.user_agent}
        self.__rate_limiter = RateLimiter(limit)
        self.__spoof_headers = spoof_headers
        self.__next_headers = datetime.utcnow()
        self.__cached_headers = None
        self.__cached_responses = {}

    def _get_headers(self) -> dict:
        if self.__cached_headers is None or datetime.utcnow() > self.__next_headers:
            self.__cached_headers = Headers().generate()
            print(
                "Refreshing spoofed headers with User-Agent: "
                f"{self.__cached_headers.get('User-Agent')}"
            )
            self.__next_headers = datetime.utcnow() + timedelta(
                minutes=self.__SPOOF_HEADER_LIFETIME_MINUTES
            )
        return self.__cached_headers

    def _hash_request(
        self, url: str, params: Optional[Dict[str, Any]] = None, data: Any = None
    ) -> int:
        return hash(
            url
            + (
                ",".join([str(v) for v in params.values()])
                if params is not None
                else ""
            )
            + (str(data) if data is not None else "")
        )

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        json: bool = True,
    ) -> Union[Any, str]:
        req_hash = self._hash_request(url, params, data)

        if req_hash in self.__cached_responses:
            print(f"Serving {url} from cache")
            return self.__cached_responses[req_hash]

        if headers is None:
            headers = (
                self.__default_headers
                if not self.__spoof_headers
                else self._get_headers()
            )

        backoff = ExponentialBackoff()

        async def do_req():
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, params=params, headers=headers, data=data
                ) as res:
                    if res.status != 200:
                        await backoff.backoff(res.url, res.status)
                        return await do_req()
                    res_val = await res.json() if json else await res.text()
                    self.__cached_responses[req_hash] = res_val
                    return res_val

        return await self.__rate_limiter.request(url, do_req)

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: bool = True,
    ) -> Union[Any, str]:
        return await self.request("GET", url, params=params, headers=headers, json=json)

    async def post(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        json: bool = True,
    ) -> Union[Any, str]:
        return await self.request(
            "POST", url, params=params, headers=headers, data=data, json=json
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        raise NotImplementedError
