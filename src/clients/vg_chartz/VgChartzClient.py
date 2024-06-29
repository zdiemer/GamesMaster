from __future__ import annotations

import datetime
import logging
from typing import Dict, List

from bs4 import BeautifulSoup

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator


class VgChartzClient(ClientBase):
    __BASE_VG_CHARTZ_URL = "https://www.vgchartz.com"

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator,
            config,
            RateLimit(30, DatePart.MINUTE),
            spoof_headers=True,
        )

    async def _make_request(self, route: str, params: Dict = None) -> any:
        url = f"{self.__BASE_VG_CHARTZ_URL}/{route}"

        return await self.get(url, params=params, json=False)

    async def games(self, title: str, page: int = 1) -> any:
        return await self._make_request(
            "games/games.php",
            {
                "name": title,
                "region": "All",
                "boxart": "Both",
                "banner": "Both",
                "ownership": "Both",
                "showmultiplat": "No",
                "results": 200,
                "order": "Sales",
                "showtotalsales": 0,
                "showpublisher": 1,
                "showvgchartzscore": 1,
                "shownasales": 0,
                "showdeveloper": 1,
                "showcriticscore": 0,
                "showpalsales": 0,
                "showreleasedate": 1,
                "showuserscore": 1,
                "showjapansales": 0,
                "showlastupdate": 0,
                "showothersales": 0,
                "showshipped": 1,
                "page": page,
            },
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        matches: List[GameMatch] = []

        page = 1
        results = []

        while page == 1 or (
            len(results) > 0 and not any(m.is_guaranteed_match() for m in matches)
        ):
            response = await self.games(title=game.title, page=page)
            page += 1

            soup = BeautifulSoup(response, "html.parser")
            result_body = soup.find("div", {"id": "generalBody"})
            results = result_body.find_all(
                "tr",
                {
                    "style": [
                        "background-image:url(../imgs/chartBar_large.gif); height:70px",
                        "background-image:url(../imgs/chartBar_alt_large.gif); height:70px",
                    ],
                },
            )

            for res in results:
                cells = res.find_all("td")

                (
                    _,  # Pos
                    _,  # Box Art
                    title,
                    console,
                    publisher,
                    developer,
                    vg_chartz_score,
                    user_score,
                    total_shipped,
                    release_date,
                ) = cells

                vg_chartz_score = (
                    float(vg_chartz_score.getText().strip())
                    if vg_chartz_score.getText().strip() != "N/A"
                    else None
                )

                user_score = (
                    float(user_score.getText().strip())
                    if user_score.getText().strip() != "N/A"
                    else None
                )

                total_shipped = (
                    float(total_shipped.getText().strip()[:-1]) * 1_000_000
                    if total_shipped.getText().strip() != "N/A"
                    else None
                )

                release_text = release_date.getText().strip()
                day_suffix = release_text[2:4] if release_text != "N/A" else None

                release_date = (
                    datetime.datetime.strptime(release_text, "%dth %b %y")
                    if day_suffix == "th"
                    else datetime.datetime.strptime(release_text, "%dst %b %y")
                    if day_suffix == "st"
                    else datetime.datetime.strptime(release_text, "%drd %b %y")
                    if day_suffix == "rd"
                    else datetime.datetime.strptime(release_text, "%dnd %b %y")
                    if day_suffix == "nd"
                    else None
                )

                vg_info = {
                    "title": title.a.getText().strip(),
                    "console": console.img["alt"],
                    "publisher": publisher.getText().strip(),
                    "developer": developer.getText().strip(),
                    "vg_chartz_score": vg_chartz_score,
                    "user_score": user_score,
                    "total_shipped": total_shipped,
                    "release_date": release_date,
                }

                if (
                    vg_info["console"] == "Series"
                    or vg_info["console"] == "All"
                    or vg_info["total_shipped"] is None
                ):
                    continue

                if not self.validator.check_platform_alias_is_mapped(
                    vg_info["console"]
                ):
                    logging.warning(
                        (
                            "Platform alias '%s' was not mapped to any "
                            "known platform in `PLATFORM_NAMES`."
                        ),
                        vg_info["console"],
                    )
                    continue

                match = self.validator.validate(
                    game,
                    vg_info["title"],
                    [vg_info["console"]],
                    [vg_info["release_date"].year]
                    if release_date is not None
                    else None,
                    [vg_info["publisher"]],
                    [vg_info["developer"]],
                )

                if match.likely_match:
                    matches.append(
                        GameMatch(
                            vg_info["title"],
                            title.a["href"],
                            title.a["href"].split("/")[4],
                            vg_info,
                            match,
                        )
                    )

        return matches
