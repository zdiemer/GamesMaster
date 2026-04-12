"""A client for scraping game data from GameFAQs.

This file implements a class that is able to scrape GameFAQs for
game information, matching against desired inputs, and returning the
matches as structured output.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp.client_exceptions
from bs4 import BeautifulSoup, element

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator, ValidationInfo
from .game_faqs_types import (
    GameFaqsCompany,
    GameFaqsExpansion,
    GameFaqsFranchise,
    GameFaqsGame,
    GameFaqsGenre,
    GameFaqsGuide,
    GameFaqsPlatform,
    GameFaqsRegion,
    GameFaqsRelease,
    GameFaqsReleaseStatus,
)

GAMEFAQS_PLATFORM_SHORT_NAME_TO_SLUG: Dict[str, str] = {
    "APL2": "appleii",
    "2600": "atari2600",
    "5200": "atari5200",
    "A800": "atari8bit",
    "CVIS": "colecovision",
    "INTV": "intellivision",
    "AQU": "aquarius",
    "MVIS": "microvision",
    "O2": "odyssey2",
    "SG1": "sg1000",
    "TI": "ti99",
    "VECX": "vectrex",
    "VC20": "vic20",
    "AM": "actionmax",
    "7800": "atari7800",
    "ST": "ast",
    "FDS": "famicomds",
    "ORIC": "oric1",
    "ZX": "sinclair",
    "AMI": "amiga",
    "GB": "gameboy",
    "GG": "gamegear",
    "GEN": "genesis",
    "HYP": "hyperscan",
    "LA": "laser",
    "MGD": "mega-duck",
    "NGCD": "neogeocd",
    "32X": "sega32x",
    "SCD": "segacd",
    "X68": "x68000",
    "SAC": "superacan",
    "TCD": "turbocd",
    "PIP": "pippin",
    "CL": "loopy",
    "FMT": "fmtowns",
    "GCOM": "gamecom",
    "JAG": "jaguar",
    "JCD": "jaguarcd",
    "N64D": "n64dd",
    "POS": "palmos",
    "PLD": "playdia",
    "SAT": "saturn",
    "VBOY": "virtualboy",
    "WS": "wonderswan",
    "DC": "dreamcast",
    "ERDR": "ereader",
    "GC": "gamecube",
    "GIZ": "gizmondo",
    "NGE": "ngage",
    "NGP": "ngpocket",
    "PMM": "pokemon-mini",
    "MOBI": "mobile",
    "WOS": "palm-webos",
    "X360": "xbox360",
    "ZB": "zeebo",
    "FIRE": "firetv",
    "WIIU": "wii-u",
    "WINM": "windows-mobile",
    "XONE": "xboxone",
    "AND": "android",
    "ARC": "arcade",
    "DED": "dedicated",
    "EVC": "evercade",
    "IOS": "iphone",
    "LNX": "unixlinux",
    "MQ": "meta-quest",
    "NS": "switch",
    "NS2": "switch-2",
    "WEB": "webonly",
    "PD": "playdate",
    "STA": "stadia",
    "XBSX": "xbox-series-x",
}


class GameFaqsClient(ClientBase):
    """Client for fetching game information from GameFAQs.

    This class implements multiple routes for fetching information from
    GameFAQs, including exposing internal API functionality and fetching
    direct HTML pages.

    Attributes:
        __BASE_GAMEFAQS_URL: The base URL to use for requests
        __PLATFORM_TO_URL_PART: Maps platform name to URL slug on GameFAQs
        __PERCENT_CHANCE_DISGUISE_TRAFFIC: A percent chance to make a disguised request
    """

    guide_cache: Dict[str, Any] = {}

    __BASE_GAMEFAQS_URL = "https://gamefaqs.gamespot.com"

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            RateLimit(per=DatePart.MINUTE, range_req=(10, 40)),
            spoof_headers=True,
            use_vpn=True,
            cycle_vpn_stasues=[401, 403, 429],
            cycle_vpn_errors=[aiohttp.client_exceptions.ClientConnectorError],
        )

    async def _make_request(
        self, route: str, params: Dict = None, as_json: bool = True
    ) -> Any:
        """Internal method for requesting for GameFAQs"""
        url = f"{self.__BASE_GAMEFAQS_URL}/{route}"
        return await self.get(url, params=params, json=as_json)

    async def home_game_search(self, term: str) -> Dict[str, Any]:
        """Performs a search for a term using GameFAQs's internal API.

        This method will use GameFAQs's internal home_game_search route
        to search for a specified search term, returning a JSON object.

        Args:
            term: A search term

        Returns:
            A JSON object containing search results
        """
        return await self._make_request(
            "ajax/home_game_search", {"term": self.validator.romanize(term)}
        )

    async def game_page(self, url: str):
        """Request a game page using the specified URL.

        This method will return the raw HTML of a given URL, specifically
        used for game pages.

        Args:
            url: The game page's URL

        Returns:
            An HTML string for the game page
        """
        return await self._make_request(url, as_json=False)

    async def release_data_page(self, url: str):
        """Request a game's release data page using the specified URL.

        This method will return the raw HTML of a given game URL's release
        data subpage.

        Args:
            url: The game page's URL

        Returns:
            An HTML string for the game's release data page
        """
        return await self._make_request(f"{url}/data", as_json=False)

    async def guides_page(self, url: str):
        """Request a game's guides page using the specified URL.

        This method will return the raw HTML of a given game URL's guides
        subpage.

        Args:
            url: The game page's URL

        Returns:
            An HTML string for the game's guides page
        """
        return await self._make_request(f"{url}/faqs", as_json=False)

    async def __get_guides(self, url: str, has_guides: bool) -> List[GameFaqsGuide]:
        """Internal method for fetching all guides from a guides page"""
        if not has_guides:
            return []

        html = await self.guides_page(url)

        soup = BeautifulSoup(html, "html.parser")
        guide_sections: List[element.Tag] = (
            soup.find_all("ol", {"class": "list flex col1 stripe guides gf_guides"})
            or []
        )

        guide_elems: List[element.Tag] = []
        guides: List[GameFaqsGuide] = []

        for section in guide_sections:
            guide_elems.extend(section.find_all("li") or [])

        for guide in guide_elems:
            gf_guide = GameFaqsGuide()

            gf_guide.platform = GameFaqsPlatform(guide["data-platform"])

            title_elem = guide.find_next("div", {"class": "float_l"})
            if title_elem is not None:
                gf_guide.title = str(title_elem.a.text).strip()
                gf_guide.url = f"{self.__BASE_GAMEFAQS_URL}{title_elem.a['href']}"

                incomplete_span = title_elem.find("span", {"class": "ital"})

                gf_guide.incomplete = (
                    incomplete_span is not None
                    and "Incomplete" in str(incomplete_span.text)
                )

                author_span = title_elem.find(
                    "span", {"style": "font-size:12px;font-weight:normal;"}
                )

                if author_span is not None:
                    gf_guide.author_name = str(author_span.a.text).strip()
                    gf_guide.author_url = (
                        f"{self.__BASE_GAMEFAQS_URL}{author_span.a['href']}"
                    )

                flair_elem = title_elem.find_next("span", {"class": "flair"})
                if flair_elem is not None:
                    gf_guide.html = str(flair_elem.text).strip() == "HTML"

            version_elem = guide.find_next("div", {"class": "meta float_r"})
            if version_elem is not None:
                vers_string = str(version_elem.text.strip().split(",")[0])
                if vers_string.startswith("v"):
                    gf_guide.version = vers_string

                if version_elem.span is not None and version_elem.span.has_attr(
                    "title"
                ):
                    try:
                        gf_guide.updated_date = datetime.strptime(
                            version_elem.span["title"], "%m/%d/%Y"
                        )
                    except ValueError:
                        logging.warning(
                            "Failed to parse updated date for %s by %s (%s)",
                            gf_guide.title,
                            gf_guide.author_name,
                            gf_guide.url,
                        )

            accolade_elem = guide.find_next("div", {"class": "meta float_l bold ital"})
            if accolade_elem is not None:
                accolade = accolade_elem.text.strip()
                if accolade == "*Highest Rated*":
                    gf_guide.highest_rated = True
                elif accolade == "*Most Recommended*":
                    gf_guide.most_recommended = True
                elif accolade.startswith("*FAQ of the Month Winner:"):
                    gf_guide.faq_of_the_month_winner = True
                    faq_of_the_month = datetime.strptime(
                        accolade.split(":")[1].strip(), "%B %Y*"
                    )
                    gf_guide.faq_of_the_month_month = faq_of_the_month.strftime("%B")
                    gf_guide.faq_of_the_month_year = faq_of_the_month.year

            header = guide.find_previous("div", {"class": "head"})

            if (
                not gf_guide.html
                and gf_guide.url is not None
                and (header is None or "Guides" in header.text.strip())
            ):
                if gf_guide.hash_id in self.guide_cache:
                    logging.debug(
                        "Serving %s by %s (%s) from cache",
                        gf_guide.title,
                        gf_guide.author_name,
                        gf_guide.url,
                    )
                    gf_guide.full_text = self.guide_cache[gf_guide.hash_id]
                else:
                    try:
                        game_guide = await self.get(gf_guide.url, json=False)
                    except UnicodeDecodeError:
                        logging.debug(
                            "Failed to decode %s by %s (%s)",
                            gf_guide.title,
                            gf_guide.author_name,
                            gf_guide.url,
                        )
                        game_guide = None

                    if game_guide is not None:
                        soup = BeautifulSoup(game_guide, "html.parser")
                        guide_contents = soup.find("div", {"id": "faqtext"})

                        if guide_contents is not None:
                            gf_guide.full_text = guide_contents.get_text(" ").strip()

                    self.guide_cache[gf_guide.hash_id] = gf_guide.full_text

            guides.append(gf_guide)

        return guides

    async def __get_gamefaqs_games(
        self,
        game: ExcelGame,
        match: Dict,
        platform: ExcelPlatform,
        fetch_dlc: bool = False,
        virtual_console: bool = False,
    ) -> List[GameFaqsGame]:
        """Internal method for fetching info on a game from a game page"""
        url = match["url"][1:]
        html_doc = await self.game_page(url)

        soup = BeautifulSoup(html_doc, "html.parser")

        current_platform = soup.find("span", {"class": "header_more"}).text.strip()
        plat_select = soup.find("div", {"class": "contrib_jumper"})

        other_platforms = plat_select.find_all("option") if plat_select else []

        gf_games: List[GameFaqsGame] = []

        should_skip_linux = (
            platform == ExcelPlatform.PC
            and current_platform == "Linux"
            and other_platforms is not None
        )

        has_guides = bool(int(match["has_guides"]))

        if not should_skip_linux and (
            virtual_console
            or self.validator.verify_platform(platform, [current_platform])
        ):
            gf_games.append(
                await self.__get_gamefaqs_game(
                    html_doc, match["game_id"], url, has_guides
                )
            )

        def sluggify(game_name: str) -> str:
            return " ".join(
                re.sub(r"[^\w\s]", "", game_name).strip().lower().split()
            ).replace(" ", "-")

        def platform_to_slug(p: str) -> str:
            """Convert a platform name to a slug for URL matching."""
            return GAMEFAQS_PLATFORM_SHORT_NAME_TO_SLUG.get(p.upper(), sluggify(p))

        url_matches: Dict[str, ValidationInfo] = {}
        exact_match_url: Optional[str] = None
        exact_match_id: Optional[int] = None

        for platform_elem in other_platforms:
            name, gf_platform = platform_elem.text.strip()[:-1].rsplit(" (", maxsplit=1)

            if platform == ExcelPlatform.PC and gf_platform == "LNX":
                continue

            platform_url = f"{platform_to_slug(gf_platform)}/{platform_elem['value']}-{sluggify(name)}"

            v_info = self.validator.validate(
                game,
                name,
                [gf_platform],
            )

            if v_info.exact and v_info.platform_matched:
                exact_match_url = platform_url
                exact_match_id = platform_elem["value"]
                break

            url_matches[platform_url] = v_info

        if exact_match_url:
            return [
                await self.__get_gamefaqs_game(
                    await self.game_page(exact_match_url),
                    int(exact_match_id),
                    exact_match_url,
                    has_guides,
                )
            ]

        for url, validation_info in url_matches.items():
            if virtual_console or validation_info.likely_match:
                gf_games.append(
                    await self.__get_gamefaqs_game(
                        await self.game_page(url),
                        int(url.split("/")[-1].split("-")[0]),
                        url,
                        has_guides,
                    )
                )

        if fetch_dlc:
            expansions: List[GameFaqsGame] = []
            for gf_game in gf_games:
                for gf_game_expansion in gf_game.expansions:
                    url = gf_game_expansion.url[1:]
                    expansions.append(
                        await self.__get_gamefaqs_game(
                            await self.game_page(url),
                            int(url.split("/")[-1].split("-")[0]),
                            url,
                            False,
                        )
                    )

            gf_games.extend(expansions)

        return gf_games

    async def __get_gamefaqs_game(
        self, html: Any, match_id: int, url: str, has_guides: bool
    ) -> GameFaqsGame:
        """Internal method for fetching info on a game from a game page"""
        soup = BeautifulSoup(html, "html.parser")

        game_info = soup.find("div", {"class": "pod_gameinfo"})
        infos = game_info.find_all("div", {"class": "content"})

        gf_game = GameFaqsGame()
        gf_game.id = match_id
        gf_game.url = f"{self.__BASE_GAMEFAQS_URL}/{url}"
        gf_game.title = soup.find("h1", {"class": "page-title"}).text.strip()

        for i in infos:
            label = i.b.text.strip()
            if label == "Platform:":
                gf_game.platform = GameFaqsPlatform(str(i.a.text).strip())
            elif label == "Genre:":
                genre_parts = [
                    GameFaqsGenre(str(g.text).strip()) for g in i.find_all("a")
                ]
                idx = len(genre_parts) - 1
                while idx > 0:
                    genre_parts[idx].parent_genre = genre_parts[idx - 1]
                    idx -= 1
                gf_game.genre = genre_parts[-1]
            elif label == "Franchises:":
                gf_game.franchises = [
                    GameFaqsFranchise(str(f.text).strip()) for f in i.find_all("a")
                ]
            elif label in ["Developer:", "Developer/Publisher:"]:
                gf_game.developer = GameFaqsCompany(str(i.a.text).strip())
            elif label == "Also Known As:":
                aliases = str(i.i.text).split("•")
                gf_game.aliases = [
                    re.sub(r" \(.*\)$", "", alias).strip()
                    for alias in aliases
                    if alias.strip() != ""
                ]

        rating_child = soup.find(id="gs_rate_avg")
        if rating_child is not None:
            empty_title = "Average: 0 stars from  users"
            rating_elem = rating_child.parent
            if rating_elem["title"] != empty_title:
                results = re.search(
                    r"(?P<rating>[0-9]+(\.[0-9]+)*) stars* from (?P<count>[0-9]+) users",
                    rating_elem["title"],
                )

                if results is not None:
                    gf_game.user_rating = float(results.group("rating"))
                    gf_game.user_rating_count = int(results.group("count"))

        difficulty_child = soup.find(id="gs_difficulty_avg")
        if difficulty_child is not None:
            difficulty_elem = difficulty_child.parent
            empty_title = "Average: 0 hearts from  users"
            if difficulty_elem["title"] != empty_title:
                results = re.search(
                    r"(?P<rating>[0-9]+(\.[0-9]+)*) hearts* from (?P<count>[0-9]+) users",
                    difficulty_elem["title"],
                )

                if results is not None:
                    gf_game.user_difficulty = float(results.group("rating"))
                    gf_game.user_difficulty_count = int(results.group("count"))

        length_child = soup.find(id="gs_length_avg_hint")
        if length_child is not None:
            length_elem = length_child.parent
            empty_title = "Average: 0 hours from  users"
            if length_elem["title"] != empty_title:
                results = re.search(
                    r"(?P<rating>[0-9]+(\.[0-9]+)*) hours* from (?P<count>[0-9]+) users",
                    length_elem["title"],
                )

                if results is not None:
                    gf_game.user_length_hours = float(results.group("rating"))
                    gf_game.user_length_hours_count = int(results.group("count"))

        html_doc = await self.release_data_page(url)
        release_elems = []

        if html_doc is not None:
            soup = BeautifulSoup(html_doc, "html.parser")
            release_elems = soup.find("table", {"class": "rdates"}).tbody.find_all("tr")

        releases: List[GameFaqsRelease] = []

        for i in range(0, len(release_elems), 2):
            release = GameFaqsRelease()
            if i + 1 > len(release_elems) - 1:
                break
            release.title = release_elems[i].find("td", {"class": "bold"}).text.strip()
            for idx, td in enumerate(release_elems[i + 1].find_all("td")):
                value = td.text.strip()
                if value == "&nbsp;":
                    continue
                if idx == 0:
                    release.release_region = GameFaqsRegion(value)
                elif idx == 1:
                    release.publisher = GameFaqsCompany(td.a.text.strip())
                elif idx == 2:
                    release.product_id = value
                elif idx == 3:
                    release.distribution_or_barcode = value
                elif idx == 4:
                    if len(value) == 4:
                        release.release_year = int(value)
                    elif "/" in value:
                        date: datetime = datetime.strptime(value, "%m/%d/%y")
                        release.release_day = date.day
                        release.release_month = date.month
                        release.release_year = date.year
                    elif value == "Canceled":
                        release.status = GameFaqsReleaseStatus.CANCELED
                    elif "TBA" in str(value):
                        release.status = GameFaqsReleaseStatus.UNRELEASED
                    else:
                        try:
                            date: datetime = datetime.strptime(value, "%B %Y")
                            release.release_month = date.month
                            release.release_year = date.year
                        except ValueError:
                            release.status = GameFaqsReleaseStatus.UNRELEASED
                elif idx == 5:
                    release.age_rating = value

            releases.append(release)

        gf_game.releases = releases

        expansions_elem = soup.find("div", {"id": "dlc"})
        expansions: List[GameFaqsExpansion] = []

        if expansions_elem is not None:
            for elem in expansions_elem.find_all("tr"):
                try:
                    expansion_year = int(elem.find_all("td")[-1].text.strip())
                except ValueError:
                    expansion_year = None

                expansions.append(
                    GameFaqsExpansion(
                        elem.td.a.text.strip(), elem.td.a["href"], expansion_year
                    )
                )

        gf_game.expansions = expansions
        gf_game.guides = await self.__get_guides(url, has_guides)

        return gf_game

    async def get_results(self, game: ExcelGame) -> List[Any]:
        return await self.home_game_search(game.title)

    async def result_to_matches(
        self, game: ExcelGame, result: Any, check_aliases: bool = False
    ) -> List[GameMatch]:
        if result.get("footer"):
            return []

        if result.get("game_name") is None or result.get("plats") is None:
            return []

        match = self.validator.validate(
            game,
            [result["game_name"], result["product_name"]],
            [result["platform_url"], *result["plats"].split(", ")],
            [datetime.strptime(result["date_released"], "%Y-%m-%d").year],
        )

        matches: List[GameMatch] = []

        if check_aliases or match.likely_match:
            gf_games = await self.__get_gamefaqs_games(
                game,
                result,
                game.platform,
                game.dlc,
                virtual_console=game.digital_platform
                in (
                    "Virtual Console",
                    "Nintendo 3DS Ambassador Program",
                )
                or game.subscription_service == "Nintendo Switch Online"
                or game.platform == ExcelPlatform.PLAYSTATION_NETWORK,
            )

            for gf_game in gf_games:
                if any(m.is_guaranteed_match() for m in matches):
                    break

                if any(int(m.match_info.id) == int(gf_game.id) for m in matches):
                    continue

                match = self.validator.validate(
                    game,
                    [
                        gf_game.title,
                        *(gf_game.aliases or []),
                        *(r.title for r in (gf_game.releases or [])),
                    ],
                    [
                        gf_game.platform.name,
                        *(r.distribution_or_barcode for r in (gf_game.releases or [])),
                    ],
                    [
                        rel.release_year
                        for rel in filter(
                            # Filter unreleased games
                            lambda _rel: _rel.status == GameFaqsReleaseStatus.RELEASED,
                            gf_game.releases,
                        )
                    ],
                )

                match.publisher_matched = self.validator.verify_component(
                    game.publisher,
                    [r.publisher.name for r in (gf_game.releases or [])],
                )

                match.developer_matched = self.validator.verify_component(
                    game.developer,
                    [gf_game.developer] if gf_game.developer is not None else None,
                )

                match.franchise_matched = self.validator.verify_component(
                    game.franchise, [f.name for f in (gf_game.franchises or [])]
                )

                if match.likely_match:
                    matches.append(
                        GameMatch(
                            gf_game.title, gf_game.url, gf_game.id, gf_game, match
                        )
                    )

        return matches

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform in (
            ExcelPlatform.ACORN_ATOM,
            ExcelPlatform.ACORN_ELECTRON,
            ExcelPlatform.AMSTRAD_PCW,
            ExcelPlatform.APPLE_III,
            ExcelPlatform.ARDUBOY,
            ExcelPlatform.COLECO_ADAM,
            ExcelPlatform.COMMODORE_PLUS_4,
            ExcelPlatform.DRAGON_32_64,
            ExcelPlatform.EXIDY_SORCERER,
            ExcelPlatform.GALAKSIJA,
            ExcelPlatform.GAMATE,
            ExcelPlatform.GP2X,
            ExcelPlatform.GP2X_CAANOO,
            ExcelPlatform.GP2X_WIZ,
            ExcelPlatform.HARTUNG_GAME_MASTER,
            ExcelPlatform.IPOD,
            ExcelPlatform.MONON_COLOR,
            ExcelPlatform.NEC_PC_6001,
            ExcelPlatform.THUMBY,
            ExcelPlatform.THUMBY_COLOR,
            ExcelPlatform.TIMETOP_GAMEKING,
            ExcelPlatform.TIMETOP_GAMEKING_III,
            ExcelPlatform.TVOS,
            ExcelPlatform.WATCHOS,
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        results = await self.get_results(game)

        matches: List[GameMatch] = []

        for result in results:
            if any(m.is_guaranteed_match() for m in matches):
                break

            matches.extend(await self.result_to_matches(game, result))

        if not any(matches) or all(not m.is_guaranteed_match() for m in matches):
            for result in results:
                if any(m.is_guaranteed_match() for m in matches):
                    break

                for m in await self.result_to_matches(game, result, check_aliases=True):
                    if any(_m.match_info.id == m.match_info.id for _m in matches):
                        continue
                    matches.append(m)

        return matches
