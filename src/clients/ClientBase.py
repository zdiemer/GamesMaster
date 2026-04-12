from __future__ import annotations

import asyncio
import logging
import random
import traceback
import urllib.parse
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import aiohttp
import aiohttp.client_exceptions
from fake_headers import Headers
from piapy import PiaVpn

from clients import InputHelper
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from logging_decorator import LoggingColor as Color, LoggingDecorator as LD
from match_validator import MatchValidator


class ResponseNotOkError(Exception):
    pass


class ImmediatelyStopStatusError(Exception):
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
    range_req: Tuple[int, int]
    per_multiplier: int

    def __init__(
        self,
        max_req: int = 1,
        per: DatePart = DatePart.SECOND,
        rate_limit_per_route: bool = False,
        get_route_path: Optional[Callable[[str], str]] = None,
        range_req: Optional[Tuple[int, int]] = None,
        per_multipler: int = 1,
    ):
        self.max_req = max_req
        self.per = per
        self.rate_limit_per_route = rate_limit_per_route
        self.get_route_path = get_route_path
        self.range_req = range_req
        self.per_multiplier = per_multipler

        if self.max_req <= 0:
            raise ValueError("`max_req` must be a positive number greater than zero")

        if self.rate_limit_per_route and self.get_route_path is None:
            raise ValueError(
                "Must specify `get_route_path` when `rate_limit_per_route` is True"
            )

        if self.range_req is not None:
            if self.range_req[0] >= self.range_req[1]:
                raise ValueError(
                    "When specifying `range_req`, first value "
                    "must be smaller than the second value"
                )
            if self.range_req[0] <= 0:
                raise ValueError(
                    "`range_req` lower bound must be a positive number greater than zero"
                )


class ExponentialBackoff:
    max_backoffs: int
    backoff_seconds: int
    exponent: int
    _backoffs: int

    def __init__(
        self, initial_backoff: int = 2, exponent: int = 2, max_backoffs: int = 3
    ):
        self.backoff_seconds = initial_backoff
        self.exponent = exponent
        self.max_backoffs = max_backoffs
        self._backoffs = 0

    async def backoff(self, url: str, reason: Union[int, str]):
        if self._backoffs + 1 > self.max_backoffs:
            raise ResponseNotOkError(reason)
        logging.warning(
            "Backing off for %ss for %s due to %s",
            LD.color(self.backoff_seconds, Color.RED),
            url,
            LD.color(reason, Color.RED),
        )
        await asyncio.sleep(self.backoff_seconds + random.random())
        self.backoff_seconds **= self.exponent
        self._backoffs += 1


class RateLimiter:
    settings: RateLimit
    _last_calls: Dict[str, datetime]

    def __init__(self, limit: RateLimit = RateLimit()):
        self.settings = limit
        self._last_calls = {}

    @property
    def seconds_between_requests(self) -> float:
        per = self.settings.per
        _max = self.settings.max_req

        if self.settings.range_req is not None:
            a, b = self.settings.range_req
            _max = random.randint(a, b)

        if per == DatePart.SECOND:
            return 1.0 / (_max / (1.0 * self.settings.per_multiplier))
        if per == DatePart.MINUTE:
            return 1.0 / (_max / (60.0 * self.settings.per_multiplier))
        if per == DatePart.HOUR:
            return 1.0 / (_max / (3600.0 * self.settings.per_multiplier))
        if per == DatePart.DAY:
            return 1.0 / (_max / (86_400.0 * self.settings.per_multiplier))
        if per == DatePart.WEEK:
            return 1.0 / (_max / (604_800.0 * self.settings.per_multiplier))
        if per == DatePart.MONTH:
            return 1.0 / (_max / (2.628e6 * self.settings.per_multiplier))
        if per == DatePart.YEAR:
            return 1.0 / (_max / (3.154e7 * self.settings.per_multiplier))

    def next_call(self, key: str, now: datetime = datetime.now(UTC)) -> datetime:
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
            if not self.settings.rate_limit_per_route
            else self.settings.get_route_path(url)
        )

        utcnow = datetime.now(UTC)
        next_call = self.next_call(key, utcnow)

        if next_call > utcnow:
            delta = next_call - utcnow
            sleep_time_seconds = delta.total_seconds()
            if sleep_time_seconds >= 5.0:
                logging.debug(
                    "Throttling %ss for %s",
                    LD.color(f"{sleep_time_seconds:,.2f}", Color.YELLOW),
                    url,
                )
            await asyncio.sleep(sleep_time_seconds)

        self._last_calls[key] = datetime.now(UTC)
        return await func()


class ClientBase:
    __SPOOF_HEADER_LIFETIME_MINUTES: int = 60
    __VPN_FAILURE_THRESHOLD: int = 3

    __cached_headers: Optional[dict]
    __cached_responses: Dict[int, Union[Any, str]]
    __default_headers: Dict[str, str]
    __immediately_stop_statuses: List[int]
    __next_headers: datetime
    __spoof_headers: bool
    __cycle_vpn_stasues: List[int]
    __cycle_vpn_errors: List[Exception]
    __vpn_regions: List[str]
    __vpn_requests: int
    __vpn_current_region: Optional[str]
    __vpn_region_failures: Dict[str, int]

    _config: Config
    _rate_limiter: RateLimiter

    base_url: Optional[str]
    use_vpn: bool
    validator: MatchValidator

    CACHE_FILE_NAME = "cache.pkl"

    def __init__(
        self,
        validator: MatchValidator = None,
        config: Optional[Config] = None,
        limit: RateLimit = RateLimit(),
        spoof_headers: bool = False,
        immediately_stop_statuses: Optional[List[int]] = None,
        use_vpn: bool = False,
        cycle_vpn_stasues: Optional[List[int]] = None,
        cycle_vpn_errors: Optional[List[Exception]] = None,
        vpn_regions: Optional[List[str]] = None,
        base_url: Optional[str] = None,
    ):
        self.base_url = base_url
        self.use_vpn = use_vpn
        self.validator = validator or MatchValidator()
        self._config = config or Config.create()
        self.__default_headers = {"User-Agent": self._config.user_agent}
        self._rate_limiter = RateLimiter(limit)
        self.__spoof_headers = spoof_headers
        self.__next_headers = datetime.now(UTC)
        self.__cached_headers = None
        self.__cached_responses = {}
        self.__immediately_stop_statuses = immediately_stop_statuses or []
        self.__cycle_vpn_stasues = cycle_vpn_stasues or []
        self.__cycle_vpn_errors = cycle_vpn_errors or []
        self.__vpn_regions = vpn_regions or []
        self.__vpn_requests = 0
        self.__vpn_region_failures = {}
        self.__vpn_current_region = None

    def _get_headers(self, url: str) -> dict:
        if self.__cached_headers is None or datetime.now(UTC) > self.__next_headers:
            new_headers = Headers().generate()
            new_headers["Referer"] = random.choice(
                [
                    "https://www.google.com/",
                    "https://www.bing.com/",
                    "https://search.yahoo.com/",
                    "https://duckduckgo.com/",
                    urllib.parse.urljoin(url, urllib.parse.urlparse(url).path),
                    "https://twitter.com/",
                ]
            )
            new_headers["Accept-Encoding"] = "gzip, deflate, br"
            new_headers["Accept-Language"] = "en-US,en;q=0.9,ja;q=0.8"
            new_headers["Accept"] = (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            )
            self.__cached_headers = new_headers
            logging.debug(
                "Refreshing spoofed headers with User-Agent: %s",
                LD.color(self.__cached_headers.get("User-Agent"), Color.BLUE),
            )
            self.__next_headers = datetime.now(UTC) + timedelta(
                minutes=self.__SPOOF_HEADER_LIFETIME_MINUTES
            )
        return self.__cached_headers

    def _hash_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
        json_body: Any = None,
    ) -> int:
        return hash(
            url
            + (
                ",".join([str(v) for v in params.values()])
                if params is not None
                else ""
            )
            + (str(data) if data is not None else "")
            + (str(json_body) if json_body is not None else "")
        )

    async def _safe_status(self, vpn: PiaVpn, retries: int = 5) -> str:
        tries = 0
        last_exception = None

        while tries < retries:
            try:
                return vpn.status()
            except SystemError as exc:
                logging.warning(
                    "VPN status check failed: %s%s",
                    exc,
                    ", retrying..." if tries < retries - 1 else "",
                )
                tries += 1
                last_exception = exc
                await asyncio.sleep(1)

        raise last_exception

    async def _safe_connect(self, retries: int = 5):
        tries = 0
        last_exception = None

        while tries < retries:
            try:
                await self._connect_vpn()
                return
            except (SystemError, TimeoutError) as exc:
                logging.warning(
                    "VPN connection failed: %s%s",
                    exc,
                    ", retrying..." if tries < retries - 1 else "",
                )
                tries += 1
                last_exception = exc
                await asyncio.sleep(1)

        raise last_exception

    async def _connect_vpn(self):
        if not self.use_vpn:
            return

        vpn = PiaVpn()

        status = await self._safe_status(vpn)
        timeout = 60
        start_time = datetime.now()

        while status in (
            "Connecting",
            "Disconnecting",
            "Reconnecting",
            "StillConnecting",
            "DisconnectingToReconnect",
            "StillReconnecting",
        ):
            status = await self._safe_status(vpn)
            await asyncio.sleep(1)
            if datetime.now() - start_time > timedelta(seconds=timeout):
                logging.warning("VPN connection timed out, throwing")
                raise TimeoutError(
                    f"VPN connection timed out after {timeout} seconds with status {status}."
                )

        if status != "Connected":
            logging.debug("Attempting VPN reconnection with status: %s", status)
            server_name = (
                random.choice(vpn.regions())
                if not any(self.__vpn_regions)
                else random.choice(self.__vpn_regions)
            )
            vpn.set_region(server=server_name)
            region = vpn.connect()
            logging.debug("VPN connected to %s", region)
            self.__vpn_requests = 0
            self.__vpn_current_region = region

            while (
                server_name == "random"
                and self.__vpn_region_failures.get(self.__vpn_current_region, 0)
                >= self.__VPN_FAILURE_THRESHOLD
            ):
                logging.warning(
                    "VPN region %s has failed %d times, recycling.",
                    self.__vpn_current_region,
                    self.__VPN_FAILURE_THRESHOLD,
                )
                vpn.set_region(server=server_name)
                region = vpn.connect()
                logging.debug("VPN connected to %s", region)
                self.__vpn_requests = 0
                self.__vpn_current_region = region

    async def _cycle_vpn(self):
        if not self.use_vpn:
            return

        logging.info(
            "VPN has been compromised after %d request%s, cycling IP.",
            self.__vpn_requests,
            "s" if self.__vpn_requests != 1 else "",
        )
        vpn = PiaVpn()

        if self.__vpn_current_region is not None and self.__vpn_requests == 1:
            if self.__vpn_current_region in self.__vpn_region_failures:
                self.__vpn_region_failures[self.__vpn_current_region] += 1
            else:
                self.__vpn_region_failures[self.__vpn_current_region] = 1

        if await self._safe_status(vpn) == "Connected":
            if vpn.disconnect():
                logging.debug("VPN disconnected.")
            else:
                logging.error("VPN failed to disconnect.")

        self.__cached_headers = None
        await self._safe_connect()

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        json: bool = True,
        retry_errors: Optional[List[Exception]] = None,
        json_body: Any = None,
    ) -> Union[Any, str]:
        await self._safe_connect()

        req_hash = self._hash_request(url, params, data, json_body)

        if req_hash in self.__cached_responses:
            logging.debug("Serving %s from cache", url)
            return self.__cached_responses[req_hash]

        if headers is None:
            headers = (
                self.__default_headers
                if not self.__spoof_headers
                else self._get_headers(url)
            )
        elif self.__spoof_headers:
            headers = {**self.__default_headers, **headers}
            headers.update(self._get_headers(url))

        backoff = ExponentialBackoff()

        async def do_req():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        params=params,
                        headers=headers,
                        data=data,
                        json=json_body,
                    ) as res:
                        if res.status != 200:
                            if res.status in self.__immediately_stop_statuses:
                                raise ImmediatelyStopStatusError
                            if res.status in self.__cycle_vpn_stasues:
                                await self._cycle_vpn()
                            else:
                                text = await res.text()
                                await backoff.backoff(res.url, text or res.status)
                            return await do_req()
                        res_val = await res.json() if json else await res.text()
                        if res_val is None:
                            await backoff.backoff(url, "Empty response")
                            return await do_req()
                        self.__cached_responses[req_hash] = res_val
                        if self.use_vpn:
                            self.__vpn_requests += 1
                        return res_val
            except Exception as exc:
                if type(exc) in self.__cycle_vpn_errors:
                    await self._cycle_vpn()
                    return await do_req()
                if (
                    type(exc)
                    in (
                        aiohttp.client_exceptions.ClientError,
                        aiohttp.client_exceptions.ClientOSError,
                        aiohttp.client_exceptions.ClientConnectionError,
                        aiohttp.client_exceptions.ClientPayloadError,
                        aiohttp.client_exceptions.ClientConnectorError,
                        aiohttp.client_exceptions.ServerDisconnectedError,
                        asyncio.TimeoutError,
                        ConnectionError,
                    )
                    or retry_errors is not None
                    and type(exc) in retry_errors
                ):
                    print(exc)
                    await backoff.backoff(url, type(exc).__name__)
                    return await do_req()
                raise

        return await self._rate_limiter.request(url, do_req)

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: bool = True,
        retry_errors: Optional[List[Exception]] = None,
        json_body: Any = None,
    ) -> Union[Any, str]:
        return await self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            json=json,
            retry_errors=retry_errors,
            json_body=json_body,
        )

    async def post(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        json: bool = True,
        retry_errors: Optional[List[Exception]] = None,
        json_body: Any = None,
    ) -> Union[Any, str]:
        return await self.request(
            "POST",
            url,
            params=params,
            headers=headers,
            data=data,
            json=json,
            retry_errors=retry_errors,
            json_body=json_body,
        )

    async def get_results(self, game: ExcelGame) -> List[Any]:
        raise NotImplementedError

    async def get_results_paginated(self, game: ExcelGame) -> AsyncGenerator[List[Any]]:
        raise NotImplementedError

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> Optional[GameMatch]:
        raise NotImplementedError

    async def process_results(
        self, game: ExcelGame, results: List[Any]
    ) -> List[GameMatch]:
        matches: List[GameMatch] = []

        for result in results:
            if any(m.is_guaranteed_match() for m in matches):
                break

            match = await self.result_to_match(game, result)

            if match is not None:
                matches.append(match)

        if not any(matches) or all(not m.is_guaranteed_match() for m in matches):
            for result in results:
                if any(m.is_guaranteed_match() for m in matches):
                    break

                match = await self.result_to_match(game, result, is_fallback=True)

                if match is not None and match.id not in [m.id for m in matches]:
                    matches.append(match)

        return matches

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        try:
            results = await self.get_results(game)
            return await self.process_results(game, results)
        except NotImplementedError:
            matches: List[GameMatch] = []

            async for results in self.get_results_paginated(game):
                if any(m.is_guaranteed_match() for m in matches):
                    break

                matches.extend(await self.process_results(game, results))

            return matches

    def should_skip(self, game: ExcelGame) -> bool:
        return False

    async def manual_match(self, game: ExcelGame) -> Optional[GameMatch]:
        should_manual_match = InputHelper.boolean_input(
            f"Does {game.full_name} have a match for {type(self).__name__.replace('Client', '')}?"
        )

        if should_manual_match:
            return await self._manual_match_impl(game)

        return None

    async def _manual_match_impl(self, game: ExcelGame) -> Optional[GameMatch]:
        raise NotImplementedError

    async def try_match_game(
        self, game: ExcelGame
    ) -> Tuple[bool, Optional[List[GameMatch]], Optional[str]]:
        try:
            if self.should_skip(game):
                return (True, None, None)
            return (True, await self.match_game(game), None)
        except NotImplementedError:
            raise
        except ImmediatelyStopStatusError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            return (False, None, "\n".join(traceback.format_exception(exc)))

    def try_parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if date_str is None:
            return None

        try:
            return datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str, "%Y")
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str, "%d %B %Y")
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str, "%B %Y")
        except ValueError:
            pass

        return None

    def try_parse_date_year(self, date_str: Optional[str]) -> Optional[int]:
        date = self.try_parse_date(date_str)
        return date.year if date else None
