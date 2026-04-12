from __future__ import annotations

import re
from typing import Any, AsyncGenerator, List

from bs4 import BeautifulSoup

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class TheCoverProjectClient(ClientBase):
    __BASE_URL = "https://www.thecoverproject.net"

    __SUPPORTED_PLATFORMS = [
        ExcelPlatform._3DO,
        ExcelPlatform.COMMODORE_AMIGA_CD32,
        ExcelPlatform.ATARI_2600,
        ExcelPlatform.ATARI_5200,
        ExcelPlatform.ATARI_7800,
        ExcelPlatform.ATARI_JAGUAR,
        ExcelPlatform.ATARI_8_BIT,
        ExcelPlatform.COLECOVISION,
        ExcelPlatform.SEGA_DREAMCAST,
        ExcelPlatform.FAMICOM_DISK_SYSTEM,
        ExcelPlatform.NINTENDO_GAMECUBE,
        ExcelPlatform.SEGA_GENESIS,
        ExcelPlatform.INTELLIVISION,
        ExcelPlatform.ATARI_JAGUAR_CD,
        ExcelPlatform.NEO_GEO_CD,
        ExcelPlatform.NES,
        ExcelPlatform.NINTENDO_64,
        ExcelPlatform.NINTENDO_SWITCH,
        ExcelPlatform.NINTENDO_WII,
        ExcelPlatform.NINTENDO_WII_U,
        ExcelPlatform.MAGNAVOX_ODYSSEY_2,
        ExcelPlatform.PC_FX,
        ExcelPlatform.PHILIPS_CD_I,
        ExcelPlatform.PLAYSTATION,
        ExcelPlatform.PLAYSTATION_2,
        ExcelPlatform.PLAYSTATION_3,
        ExcelPlatform.PLAYSTATION_4,
        ExcelPlatform.PLAYSTATION_5,
        ExcelPlatform.SEGA_32X,
        ExcelPlatform.SEGA_CD,
        ExcelPlatform.SEGA_MASTER_SYSTEM,
        ExcelPlatform.SEGA_SATURN,
        ExcelPlatform.SNES,
        ExcelPlatform.TURBOGRAFX_16,
        ExcelPlatform.XBOX,
        ExcelPlatform.XBOX_360,
        ExcelPlatform.XBOX_ONE,
        ExcelPlatform.XBOX_SERIES_X_S,
        ExcelPlatform.NINTENDO_3DS,
        ExcelPlatform.ATARI_LYNX,
        ExcelPlatform.SEGA_GAME_GEAR,
        ExcelPlatform.GAME_BOY,
        ExcelPlatform.GAME_BOY_ADVANCE,
        ExcelPlatform.GAME_BOY_COLOR,
        ExcelPlatform.NEO_GEO_POCKET,
        ExcelPlatform.NEO_GEO_POCKET_COLOR,
        ExcelPlatform.NINTENDO_DS,
        ExcelPlatform.PLAYSTATION_PORTABLE,
        ExcelPlatform.PLAYSTATION_VITA,
        ExcelPlatform.VIRTUAL_BOY,
        ExcelPlatform.WONDERSWAN,
        ExcelPlatform.WONDERSWAN_COLOR,
        ExcelPlatform.COMMODORE_AMIGA,
        ExcelPlatform.PC,
        ExcelPlatform.MAC_OS,
    ]

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config, RateLimit(1, DatePart.SECOND))

    async def search(self, game: str, page: int = 1) -> Any:
        return await self.get(
            f"{self.__BASE_URL}/view.php",
            params={"searchstring": game, "page": page},
            json=False,
        )

    async def search_paginated(self, game: ExcelGame) -> AsyncGenerator[Any, None]:
        page = 1
        while True:
            results = await self.search(game.title, page)
            if not results or "Your search returned no results." in results:
                break

            yield results
            page += 1

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in self.__SUPPORTED_PLATFORMS

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch | None:
        href = result.a["href"]
        game_id = href.split("=")[1]
        html = await self.get(f"{self.__BASE_URL}/{href}", json=False)
        output = {"game_id": game_id, "covers": [], "manuals": []}

        soup = BeautifulSoup(html, "html.parser")

        page_body = soup.find("td", {"class": "pageBody"})
        title_body, meta_body = page_body.find_all("td", {"class": "pageBody"})

        output["title"] = title_body.h2.text.strip()
        output["platform"] = soup.find("td", {"class": "newsHeader"}).a.text.strip()

        covers = soup.find("div", {"id": "covers"})

        for cover in covers.ul.find_all("li"):
            if cover.text.strip() in ("Available Covers", "Available Manuals"):
                continue

            if cover.text.strip().startswith("Manual"):
                output["manuals"].append(
                    {
                        "manual_url": f"{self.__BASE_URL}{cover.a['href']}",
                        "language": cover.a.span.text.strip().split(" ")[-1].strip(),
                    }
                )
                continue

            cover_meta = cover.a.span.text.strip()

            cover_data = {
                "cover_id": cover.a["href"].split("=")[1],
                "cover_url": f"{self.__BASE_URL}/{cover.a['href']}",
                "format": re.search(
                    r"Format: ([^\s]+)", cover_meta.replace("Country:", "")
                ).group(1),
                "country": cover.a.span.img["src"].split("/")[-1].split(".")[0].upper(),
                "custom_cover": "Custom Cover" in cover_meta,
            }

            if cover.has_attr("class") and cover["class"][0] == "tabSelected":
                cover_data["image_url"] = meta_body.img["src"].replace("_thumb", "")
            elif cover.a.has_attr("class") and cover.a["class"][0] == "thumbnail":
                cover_data["image_url"] = (
                    cover.a["onmouseover"].split("'")[-2].replace("_thumb", "")
                )

            meta_text = meta_body.text.strip()
            _, description, _, created_by, _, case_type = meta_text.split(": ")
            description = description.replace("Format", "")
            created_by = created_by.replace("Region", "")
            case_type, download_count = case_type.split(
                "This cover has been downloaded"
            )
            download_count = (
                download_count.replace("times", "").replace("Download", "").strip()
            )

            cover_data["description"] = description.strip()
            cover_data["created_by"] = created_by.strip()
            cover_data["case_type"] = case_type.strip()
            cover_data["download_count"] = int(download_count.strip())

            output["covers"].append(cover_data)

        match = self.validator.validate(game, output["title"], [output["platform"]])

        if match.likely_match:
            return GameMatch(
                output["title"],
                f"{self.__BASE_URL}/{href}",
                output["game_id"],
                output,
                match,
            )

        return None

    async def match_game(self, game: ExcelGame) -> List[Any]:
        matches: List[GameMatch] = []

        async for results in self.search_paginated(game):
            soup = BeautifulSoup(results, "html.parser")

            html_results = soup.find_all("span", {"class": "articleText"})

            for result in html_results:
                if any(m.is_guaranteed_match() for m in matches):
                    break

                match = await self.result_to_match(game, result)

                if match is not None:
                    matches.append(match)

            if any(m.is_guaranteed_match() for m in matches):
                break

        return matches
