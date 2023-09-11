from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from clients.ClientBase import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelRegion
from match_validator import MatchValidator, ValidationInfo


class PriceChartingClient(ClientBase):
    __BASE_PRICE_CHARTING_URL = "https://www.pricecharting.com/api"
    __REGION_REGEX = r"(?P<region>^(pal|jp|asian english)) "
    __EDITION_REGEX = r"( \[(?P<edition>.*)\]$)"
    __MARVEL_REGEX = r"^Marvel "

    __api_key: str

    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config)
        self.__api_key = config.price_charting_api_key

    async def _make_request(self, route: str, params: Dict[str, Any] = {}) -> Any:
        if params.get("t") is None:
            params["t"] = self.__api_key

        return await self.get(
            f"{self.__BASE_PRICE_CHARTING_URL}/{route}", params=params
        )

    async def products(
        self, id: int = None, upc: str = None, query: str = None
    ) -> Dict[str, Any]:
        params = {}

        if id is not None:
            params["id"] = id
        if upc is not None:
            params["upc"] = upc
        if query is not None:
            params["q"] = query

        return await self._make_request("products", params=params)

    def __price_charting_normalization(self, title: str) -> str:
        if "Legend of Zelda" not in title and "Zelda" in title:
            title = title.replace("Zelda", "The Legend of Zelda")

        return re.sub(
            self.__MARVEL_REGEX,
            "",
            re.sub(
                self.__EDITION_REGEX,
                "",
                title,
            ),
        )

    async def match_game(self, game: ExcelGame) -> List[Tuple[Any, ValidationInfo]]:
        if game.owned_format not in ("Both", "Physical"):
            return []

        results = await self.products(query=game.title)
        matches: List[Tuple[Any, ValidationInfo]] = []
        validator = MatchValidator()

        if results["status"] != "success":
            return matches

        default_match = None

        for r in results["products"]:
            platform = str(r["console-name"]).lower()

            if platform.startswith("comic books") or platform == "strategy guide":
                continue

            re_matches = re.search(self.__REGION_REGEX, platform)
            platform = re.sub(self.__REGION_REGEX, "", platform)
            region = ExcelRegion.NORTH_AMERICA

            if re_matches is not None:
                region_match = re_matches.group("region")

                if region_match == "pal":
                    region = ExcelRegion.EUROPE
                elif region_match == "jp":
                    region = ExcelRegion.JAPAN
                elif region_match == "asian english":
                    region = ExcelRegion.ASIA

            product_name = str(r["product-name"])

            re_matches = re.search(self.__EDITION_REGEX, product_name)

            if re_matches is not None:
                edition_match = re_matches.group("edition")

                edition_match = edition_match.lower().replace(" edition", "")
                notes = game.notes.lower().replace(" edition", "")

                if notes != edition_match:
                    continue

            if region != game.release_region:
                if default_match is None and re_matches is None:
                    if (
                        region == ExcelRegion.NORTH_AMERICA
                        or (
                            region == ExcelRegion.JAPAN
                            and game.release_region == ExcelRegion.ASIA
                        )
                        or (
                            region == ExcelRegion.ASIA
                            and game.release_region == ExcelRegion.JAPAN
                        )
                    ):
                        default_match = r
                continue

            match = validator.validate(
                game, self.__price_charting_normalization(r["product-name"]), [platform]
            )
            if match.matched:
                matches.append((r, match))
        if not any(matches) and default_match is not None:
            platform = str(default_match["console-name"]).lower()
            platform = re.sub(self.__REGION_REGEX, "", platform)
            match = validator.validate(
                game,
                self.__price_charting_normalization(default_match["product-name"]),
                [platform],
            )
            if match.matched:
                matches.append((default_match, match))
        return matches
