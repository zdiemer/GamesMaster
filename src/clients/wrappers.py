import asyncio
import datetime
import logging
import logging.config
import re
from enum import Enum
from typing import Any, List, Optional

import wikipedia
from bs4 import BeautifulSoup
from selenium import webdriver
from steam import webapi

import clients
from config import Config
from game_match import GameMatch
from excel_game import ExcelGame
from match_validator import MatchValidator


class SteamWrapper(clients.ClientBase):
    """Wrapper class for third-party Steam client.

    SteamWrapper implements the clients.ClientBase match_game function
    and wraps a third-party Steam client library for fetching information
    about games from Steam.

    Attributes:
        _client: A Steam object which represents the underlying Steam client
    """

    _client: Optional[webapi.WebAPI] = None
    _applist: dict
    _config: Config

    def __init__(self, validator: MatchValidator, config: Config = None):
        self._config = config or Config.create()
        super().__init__(
            validator, self._config, clients.RateLimit(100_000, clients.DatePart.DAY)
        )
        self._applist = None

    @property
    def client(self) -> webapi.WebAPI:
        if self._client is None:
            self._client = webapi.WebAPI(
                self._config.steam_web_api_key, auto_load_interfaces=True
            )

        return self._client

    def should_skip(self, game: ExcelGame) -> bool:
        return game.digital_platform != "Steam"

    async def get_results(self, game: ExcelGame) -> List[Any]:
        if self._applist is None:
            self._applist = self.client.IPlayerService.GetOwnedGames(
                steamid=76561197993375857,
                include_appinfo=True,
                include_played_free_games=True,
                include_free_sub=True,
                appids_filter=[],
                language="en",
                include_extended_appinfo=False,
                skip_unvetted_apps=False,
            )

        return list(
            filter(
                lambda g: self.validator.validate(
                    game, g["name"], [game.platform.value]
                ).likely_match,
                self._applist["response"]["games"],
            )
        )

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        app_details = await self.get(
            "https://store.steampowered.com/api/appdetails",
            params={"appids": result["appid"]},
        )

        app_details = app_details[str(result["appid"])]

        if app_details.get("data") is None:
            return None

        try:
            release_year = int(app_details["data"]["release_date"]["date"][-4:])
        except ValueError:
            release_year = None

        match = self.validator.validate(
            game,
            app_details["data"]["name"],
            [game.platform.value],
            [release_year],
        )

        if match.likely_match:
            reviews = await self.get(
                f"https://store.steampowered.com/appreviews/{result['appid']}",
                params={"json": 1},
            )

            return GameMatch(
                app_details["data"]["name"],
                f"https://store.steampowered.com/app/{result['appid']}",
                result["appid"],
                {
                    "app_details": app_details,
                    "app_reviews": reviews,
                },
                match,
            )

        return None


class WikipediaRegion(Enum):
    NA = "NA"
    JP = "JP"
    EU = "EU"
    AU = "AU"
    BR = "BR"
    FRA = "FRA"
    PAL = "PAL"
    WW = "WW"
    US = "US"


class WikipediaWrapper(clients.ClientBase):
    CITATION_REGEX = r"\[([0-9]+)\]"
    CATEGORY_REGEX = r"[0-9]{4} video games?$"

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config)

    def try_parse_date(self, date_str: str) -> Optional[datetime.datetime]:
        try:
            return datetime.datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            pass

        try:
            return datetime.datetime.strptime(date_str, "%d %B %Y")
        except ValueError:
            pass

        try:
            return datetime.datetime.strptime(date_str, "%B %Y")
        except ValueError:
            pass

        try:
            return datetime.datetime.strptime(date_str, "%Y")
        except ValueError:
            pass

        return None

    def is_wikipedia_region(self, region: str) -> bool:
        try:
            WikipediaRegion(region)
            return True
        except ValueError:
            return False

    async def get_results(self, game: ExcelGame) -> List[str]:
        res = wikipedia.search(game.title)
        return res

    async def result_to_match(
        self, game: ExcelGame, result: str, is_fallback: bool = False
    ) -> GameMatch:
        await asyncio.sleep(0.1)

        try:
            page = wikipedia.page(result, auto_suggest=False)
        except wikipedia.exceptions.DisambiguationError:
            return None

        try:
            _ = page.categories
        except KeyError:
            return None

        if not any(re.match(self.CATEGORY_REGEX, cat) for cat in page.categories):
            return None

        soup = BeautifulSoup(page.html(), "html.parser")
        infobox = soup.find("table", {"class": "infobox"})

        match_info = {
            "developers": [],
            "publishers": [],
            "directors": [],
            "producers": [],
            "designers": [],
            "programmers": [],
            "artists": [],
            "writers": [],
            "composers": [],
            "series": [],
            "engine": None,
            "platforms": [],
            "releases": [],
            "genres": [],
            "modes": [],
            "arcade_system": None,
        }

        if infobox is None:
            match = self.validator.validate(
                game,
                page.title,
            )

            if match.matched:
                return GameMatch(page.title, page.url, page.url, match_info, match)

            return None

        for row in infobox.find_all("tr"):
            label = row.find("th", {"class": "infobox-label"})
            data = row.find("td", {"class": "infobox-data"})

            if not label or not data:
                continue

            data_text = list(
                filter(
                    lambda t: len(t.strip()) > 1,
                    re.sub(
                        self.CITATION_REGEX, "", data.get_text(separator="\n").strip()
                    ).split("\n"),
                )
            )

            if "Developer" in label.text.strip():
                for dev in data_text:
                    if self.is_wikipedia_region(dev.strip()):
                        continue
                    match_info["developers"].append(dev.strip())
            elif "Publisher" in label.text.strip():
                for pub in data_text:
                    if self.is_wikipedia_region(pub.strip()):
                        continue
                    match_info["publishers"].append(pub.strip())
            elif "Director" in label.text.strip():
                match_info["directors"].extend(
                    [d.strip() for d in data_text if d.strip()]
                )
            elif "Producer" in label.text.strip():
                match_info["producers"].extend(
                    [p.strip() for p in data_text if p.strip()]
                )
            elif "Designer" in label.text.strip():
                match_info["designers"].extend(
                    [d.strip() for d in data_text if d.strip()]
                )
            elif "Programmer" in label.text.strip():
                match_info["programmers"].extend(
                    [p.strip() for p in data_text if p.strip()]
                )
            elif "Artist" in label.text.strip():
                match_info["artists"].extend(
                    [a.strip() for a in data_text if a.strip()]
                )
            elif "Writer" in label.text.strip():
                match_info["writers"].extend(
                    [w.strip() for w in data_text if w.strip()]
                )
            elif "Composer" in label.text.strip():
                match_info["composers"].extend(
                    [c.strip() for c in data_text if c.strip()]
                )
            elif "Series" in label.text.strip():
                match_info["series"].extend([s.strip() for s in data_text if s.strip()])
            elif "Engine" in label.text.strip():
                match_info["engine"] = data_text[0].strip() if data_text else None
            elif "Platform" in label.text.strip():
                match_info["platforms"] = [p.strip() for p in data_text if p.strip()]
            elif "Release" in label.text.strip():
                cur_regions: List[WikipediaRegion] = []
                cur_platforms: List[str] = []
                for t in data_text:
                    if self.is_wikipedia_region(t.strip()):
                        cur_regions.append(WikipediaRegion(t.strip()))
                        continue

                    parsed_date = self.try_parse_date(t.strip())

                    if parsed_date is None:
                        cur_platforms = t.strip().split(", ")
                        continue

                    match_info["releases"].append(
                        {
                            "platforms": cur_platforms,
                            "regions": cur_regions,
                            "date": parsed_date,
                        }
                    )

                    cur_regions = []
                    cur_platforms = []
            elif "Genre" in label.text.strip():
                match_info["genres"] = [g.strip() for g in data_text if g.strip()]
            elif "Mode" in label.text.strip():
                match_info["modes"] = [m.strip() for m in data_text if m.strip()]
            elif "Arcade system" in label.text.strip():
                match_info["arcade_system"] = (
                    data_text[0].strip() if data_text else None
                )
            else:
                print(f"Unknown label: {label.text.strip()} on {page.url}")

        match = self.validator.validate(
            game,
            page.title,
            match_info["platforms"],
            [
                rel["date"].year if rel["date"] else None
                for rel in match_info["releases"]
            ],
        )

        if match.likely_match:
            return GameMatch(
                page.title,
                page.url,
                page.title,
                match_info,
                match,
            )

        return None
