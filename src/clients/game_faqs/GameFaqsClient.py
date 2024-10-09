"""A client for scraping game data from GameFAQs.

This file implements a class that is able to scrape GameFAQs for
game information, matching against desired inputs, and returning the
matches as structured output.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, element

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator
from .game_faqs_types import (
    GameFaqsCompany,
    GameFaqsFranchise,
    GameFaqsGame,
    GameFaqsGenre,
    GameFaqsGuide,
    GameFaqsPlatform,
    GameFaqsRegion,
    GameFaqsRelease,
    GameFaqsReleaseStatus,
)


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

    __BASE_GAMEFAQS_URL = "https://gamefaqs.gamespot.com"
    __PLATFORM_TO_URL_PART = {
        "3do": "3do",
        "amstrad cpc": "cpc",
        "android": "android",
        "apple ii": "appleii",
        "arcade": "arcade",
        "atari 2600": "atari2600",
        "atari 7800": "atari7800",
        "atari 8-bit": "atari8bit",
        "atari jaguar": "jaguar",
        "atari lynx": "lynx",
        "atari st": "ast",
        "bbc micro": "bbc",
        "bs-x": "snes",
        "browser": "webonly",
        "colecovision": "colecovision",
        "commodore 64": "c64",
        "commodore amiga": "amiga",
        "commodore amiga cd32": "cd32",
        "commodore vic-20": "vic20",
        "dsiware": "ds",
        "dedicated console": "dedicated",
        "epoch super cassette vision": "scv",
        "fm towns": "fmtowns",
        "fm-7": "fm7",
        "famicom disk system": "famicomds",
        "game boy": "gameboy",
        "game boy advance": "gba",
        "game boy color": "gbc",
        "game.com": "game.com",
        "gamepark 32": "gp32",
        "google stadia": "stadia",
        "intellivision": "intellivision",
        "j2me": "mobile",
        "msx": "msx",
        "msx2": "msx",
        "mac os": "mac",
        "n-gage": "ngage",
        "n-gage 2.0": "ngage",
        "nec pc-8801": "pc88",
        "nec pc-9801": "pc98",
        "nes": "nes",
        "neo-geo": "neo",
        "neo-geo cd": "neogeocd",
        "neo-geo pocket": "ngpocket",
        "neo-geo pocket color": "ngpc",
        "new nintendo 3ds": "3ds",
        "nintendo 3ds": "3ds",
        "nintendo 64": "n64",
        "nintendo 64dd": "n64dd",
        "nintendo ds": "ds",
        "nintendo dsi": "ds",
        "nintendo gamecube": "gamecube",
        "nintendo pokémon mini": "pokemon-mini",
        "nintendo switch": "switch",
        "nintendo wii": "wii",
        "nintendo wii u": "wiiu",
        "oculus quest": "meta-quest",
        "ouya": "ouya",
        "pc": "pc",
        "pc-fx": "pcfx",
        "pdp-10": "pc",
        "philips cd-i": "cdi",
        "pioneer laseractive": "laser",
        "playstation": "ps",
        "playstation 2": "ps2",
        "playstation 3": "ps3",
        "playstation 4": "ps4",
        "playstation 5": "ps5",
        "playstation portable": "psp",
        "playstation vita": "vita",
        "playstation network": "ps4",
        "playdate": "playdate",
        "snes": "snes",
        "sega 32x": "sega32x",
        "sega cd": "segacd",
        "sega dreamcast": "dreamcast",
        "sega game gear": "gamegear",
        "sega genesis": "genesis",
        "sega master system": "sms",
        "sega sg-1000": "sg1000",
        "sega saturn": "saturn",
        "sharp x1": "x1",
        "sharp x68000": "x68000",
        "turbografx-16": "tg16",
        "turbografx-cd": "turbocd",
        "vectrex": "vectrex",
        "virtual boy": "virtualboy",
        "watara supervision": "svision",
        "wiiware": "wii",
        "wonderswan": "wonderswan",
        "wonderswan color": "wsc",
        "xbox": "xbox",
        "xbox 360": "xbox360",
        "xbox one": "xboxone",
        "xbox series x|s": "xbox-series-x",
        "zx spectrum": "sinclair",
        "zeebo": "zeebo",
        "ios": "iphone",
        "trs-80 color computer": "coco",
    }

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            RateLimit(per=DatePart.HOUR, range_req=(240, 600)),
            spoof_headers=True,
            use_vpn=True,
            cycle_vpn_stasues=[401, 403, 429],
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
        return await self._make_request("ajax/home_game_search", {"term": term})

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

    async def __get_guides(self, url: str) -> List[GameFaqsGuide]:
        """Internal method for fetching all guides from a guides page"""
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
                gf_guide.url = f'{self.__BASE_GAMEFAQS_URL}{title_elem.a["href"]}'

                gf_guide.author_name = str(title_elem.span.a.text).strip()
                gf_guide.author_url = (
                    f'{self.__BASE_GAMEFAQS_URL}{title_elem.span.a["href"]}'
                )

                flair_elem = title_elem.find_next_sibling("span", {"class": "flair"})
                if flair_elem is not None:
                    gf_guide.html = str(flair_elem.text).strip() == "HTML"

            version_elem = guide.find_next("div", {"class": "meta float_r"})
            if version_elem is not None:
                vers_string = str(version_elem.text.strip().split(",")[0])
                if vers_string.startswith("v"):
                    gf_guide.version = vers_string

                if version_elem.span.has_attr("title"):
                    gf_guide.updated_date = datetime.strptime(
                        version_elem.span["title"], "%m/%d/%Y"
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
                    gf_guide.faq_of_the_month_month = datetime.strftime(
                        faq_of_the_month.month, "%B"
                    )
                    gf_guide.faq_of_the_month_year = faq_of_the_month.year

            if (
                not gf_guide.html
                and gf_guide.url is not None
                and not (gf_guide.title or "").endswith("Map")
            ):
                game_guide = await self.get(gf_guide.url, json=False)
                soup = BeautifulSoup(game_guide, "html.parser")
                guide_contents = soup.find("div", {"id": "faqtext"})

                if guide_contents is not None:
                    gf_guide.full_text = guide_contents.get_text(" ").strip()

            guides.append(gf_guide)

        return guides

    async def __get_gamefaqs_game(self, match: Dict, platform: str) -> GameFaqsGame:
        """Internal method for fetching info on a game from a game page"""
        url = match["board_url"].replace(
            "boards", self.__PLATFORM_TO_URL_PART[platform.lower()]
        )[1:]

        html_doc = await self.game_page(url)

        soup = BeautifulSoup(html_doc, "html.parser")
        game_info = soup.find("div", {"class": "pod_gameinfo"})
        infos = game_info.find_all("div", {"class": "content"})

        gf_game = GameFaqsGame()
        gf_game.id = int(match["game_id"])
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
                    re.sub(r" \(.*\)", "", alias).strip() for alias in aliases
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
        # gf_game.guides = await self.__get_guides(url)

        return gf_game

    async def get_results(self, game: ExcelGame) -> List[Any]:
        return await self.home_game_search(game.title)

    async def result_to_match(
        self, game: ExcelGame, result: Any
    ) -> Optional[GameMatch]:
        if result.get("footer"):
            return None

        if result.get("game_name") is None or result.get("plats") is None:
            return None

        match = self.validator.validate(
            game,
            result["game_name"],
            result["plats"].split(", "),
            [datetime.strptime(result["date_released"], "%Y-%m-%d").year],
        )

        if match.likely_match:
            gf_game = await self.__get_gamefaqs_game(result, game.platform.value)

            if not match.date_matched:
                match.date_matched = self.validator.verify_release_year(
                    game.release_year,
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

            return GameMatch(gf_game.title, gf_game.url, gf_game.id, gf_game, match)

        return None
