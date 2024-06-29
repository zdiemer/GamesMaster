import html
from typing import Dict, List, Literal

from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator
from .moby_games_types import *  # pylint: disable=unused-wildcard-import,wildcard-import


class MobyGamesClient(ClientBase):
    __BASE_MOBYGAMES_SEARCH_URL = "https://api.mobygames.com/v1"
    __api_key: str

    def __init__(
        self,
        validator: MatchValidator,
        config: Config = None,
        rate_limit: RateLimit = None,
    ):
        config = config or Config.create()
        super().__init__(validator, config, rate_limit or RateLimit(360, DatePart.HOUR))
        self.__api_key = self._config.moby_games_api_key

    async def _make_request(self, route: str, params: Dict = None) -> any:
        params = params or {}

        if params.get("api_key") is None:
            params["api_key"] = self.__api_key

        url = f"{self.__BASE_MOBYGAMES_SEARCH_URL}/{route}"

        return await self.get(url, params=params)

    async def genres(self) -> List[Genre]:
        res = await self._make_request("genres")
        return [
            Genre(
                GenreCategory(genre["genre_category"], genre["genre_category_id"]),
                genre["genre_id"],
                genre["genre_name"],
                genre["genre_description"],
            )
            for genre in res["genres"]
        ]

    async def groups(self, limit: int = 100, offset: int = 0) -> List[Group]:
        if limit > 100:
            raise ValueError("limit has a maximum of 100")
        res = await self._make_request("groups", {"limit": limit, "offset": offset})
        return [
            Group(group["group_description"], group["group_id"], group["group_name"])
            for group in res["groups"]
        ]

    async def platforms(self) -> List[Platform]:
        res = await self._make_request("platforms")
        return [
            Platform(platform["platform_id"], platform["platform_name"])
            for platform in res["platforms"]
        ]

    async def game_platforms(self, game_id: int, platform_id: int = None):
        platform_string = f"/{platform_id}" if platform_id is not None else ""
        return await self._make_request(f"games/{game_id}/platforms{platform_string}")

    async def games(
        self,
        game_ids: List[int] = None,
        limit: int = 100,
        offset: int = 0,
        platform_ids: List[int] = None,
        genre_ids: List[int] = None,
        group_ids: List[int] = None,
        title: str = "",
        return_format: Literal["id", "brief", "normal"] = "normal",
    ) -> List[Game]:
        res = await self._make_request(
            "games",
            {
                "id": game_ids or [],
                "limit": limit,
                "offset": offset,
                "platform": platform_ids or [],
                "genre": genre_ids or [],
                "group": group_ids or [],
                "title": title,
                "format": return_format,
            },
        )

        return [
            Game(
                (
                    [
                        AlternateTitle(alt["description"], alt["title"])
                        for alt in game["alternate_titles"]
                    ]
                    if game.get("alternate_titles") is not None
                    else []
                ),
                game["description"],
                game["game_id"],
                [
                    Genre(
                        GenreCategory(
                            genre["genre_category"], genre["genre_category_id"]
                        ),
                        genre["genre_id"],
                        genre["genre_name"],
                    )
                    for genre in game["genres"]
                ],
                game["moby_score"],
                game["moby_url"],
                game["num_votes"],
                game["official_url"],
                [
                    GamePlatform(
                        Platform(platform["platform_id"], platform["platform_name"]),
                        platform["first_release_date"],
                    )
                    for platform in game["platforms"]
                ],
                (
                    Cover(
                        game["sample_cover"]["height"],
                        game["sample_cover"]["image"],
                        game["sample_cover"]["platforms"],
                        game["sample_cover"]["thumbnail_image"],
                        game["sample_cover"]["width"],
                    )
                    if game.get("sample_cover") is not None
                    else None
                ),
                [
                    Screenshot(
                        screenshot["caption"],
                        screenshot["height"],
                        screenshot["image"],
                        screenshot["thumbnail_image"],
                        screenshot["width"],
                    )
                    for screenshot in game["sample_screenshots"]
                ],
                html.unescape(game["title"]),
            )
            for game in res["games"]
        ]

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        results = await self.games(title=game.title)
        matches: List[GameMatch] = []

        async def get_years(game_id: int, platform_id: int):
            game_platforms = await self.game_platforms(game_id, platform_id)

            years = []

            for plat in game_platforms.get("releases") or []:
                if plat.get("release_date") is not None:
                    years.append(int(plat["release_date"][0:4]))

            return years

        for res in results:
            if any(m.is_guaranteed_match() for m in matches):
                break

            if res.platforms is None:
                continue

            platform_names = [p.platform.name for p in res.platforms]
            platform_years = []
            pid = 0

            for plat in res.platforms:
                if self.validator.verify_platform(game.platform, [plat.platform.name]):
                    pid = plat.platform.id
                    r_date_parts = plat.first_release_date.split("-")
                    platform_years.append(int(r_date_parts[0]))

            match = self.validator.validate(
                game, res.title, platform_names, platform_years
            )

            if match.likely_match:
                if not match.date_matched:
                    match.date_matched = self.validator.verify_release_year(
                        game.release_year, await get_years(res.id, pid)
                    )

                matches.append(GameMatch(res.title, res.moby_url, res.id, res, match))
            elif res.alternate_titles is not None:
                for alt in res.alternate_titles:
                    match = self.validator.validate(
                        game, alt.title, platform_names, platform_years
                    )

                    if match.likely_match:
                        if not match.date_matched:
                            match.date_matched = self.validator.verify_release_year(
                                game.release_year, await get_years(res.id, pid)
                            )

                        matches.append(
                            GameMatch(res.title, res.moby_url, res.id, res, match)
                        )
                        break

        return matches
