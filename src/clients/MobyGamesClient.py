from __future__ import annotations

import asyncio
import html
from datetime import datetime, timedelta
from typing import Dict, List, Literal, NamedTuple, Tuple

from clients.ClientBase import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame
from game_match import GameMatch
from match_validator import MatchValidator, ValidationInfo


class GenreCategory:
    name: str
    id: int

    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id

    def __str__(self) -> str:
        return str({"name": self.name, "id": self.id})

    def __repr__(self) -> str:
        return self.__str__()


class Genre:
    category: GenreCategory
    id: int
    description: str
    name: str

    def __init__(
        self, category: GenreCategory, id: int, name: str, description: str = None
    ):
        self.category = category
        self.id = id
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return str(
            {
                "category": self.category,
                "id": self.id,
                "description": self.description,
                "name": self.name,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()


class Group:
    description: str
    id: int
    name: str

    def __init__(self, description: str, id: int, name: str):
        self.description = description
        self.id = id
        self.name = name

    def __str__(self) -> str:
        return str({"description": self.description, "id": self.id, "name": self.name})

    def __repr__(self) -> str:
        return self.__str__()


class Platform:
    id: int
    name: str

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __str__(self) -> str:
        return str({"id": self.id, "name": self.name})

    def __repr__(self) -> str:
        return self.__str__()


class AlternateTitle:
    description: str
    title: str

    def __init__(self, description: str, title: str):
        self.description = description
        self.title = title

    def __str__(self) -> str:
        return str({"description": self.description, "title": self.title})

    def __repr__(self) -> str:
        return self.__str__()


class GamePlatform(NamedTuple):
    platform: Platform
    first_release_date: str

    def __str__(self) -> str:
        return str(
            {"platform": self.platform, "first_release_date": self.first_release_date}
        )

    def __repr__(self) -> str:
        return self.__str__()


class Cover:
    height: int
    image_url: str
    platforms: List[str]
    thumbnail_image_url: str
    width: int

    def __init__(
        self,
        height: int,
        image_url: str,
        platforms: List[str],
        thumbnail_image_url: str,
        width: int,
    ):
        self.height = height
        self.image_url = image_url
        self.platforms = platforms
        self.thumbnail_image_url = thumbnail_image_url
        self.width = width

    def __str__(self) -> str:
        return str(
            {
                "height": self.height,
                "image_url": self.image_url,
                "platforms": self.platforms,
                "thumbnail_image_url": self.thumbnail_image_url,
                "width": self.width,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()


class Screenshot:
    caption: str
    height: int
    image_url: str
    thumbnail_image_url: str
    width: str

    def __init__(
        self,
        caption: str,
        height: int,
        image_url: str,
        thumbnail_image_url: str,
        width: int,
    ):
        self.caption = caption
        self.height = height
        self.image_url = image_url
        self.thumbnail_image_url = thumbnail_image_url
        self.width = width

    def __str__(self) -> str:
        return str(
            {
                "caption": self.caption,
                "height": self.height,
                "image_url": self.image_url,
                "thumbnail_image_url": self.thumbnail_image_url,
                "width": self.width,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()


class Game:
    alternate_titles: List[AlternateTitle]
    description: str
    id: int
    genres: List[Genre]
    moby_score: float
    moby_url: str
    num_votes: int
    official_url: str
    platforms: List[GamePlatform]
    sample_cover: Cover
    sample_screenshots: List[Screenshot]
    title: str

    def __init__(
        self,
        alternate_titles: List[AlternateTitle],
        description: str,
        id: int,
        genres: List[Genre],
        moby_score: float,
        moby_url: str,
        num_votes: int,
        official_url: str,
        platforms: GamePlatform,
        sample_cover: Cover,
        sample_screenshots: List[Screenshot],
        title: str,
    ):
        self.alternate_titles = alternate_titles
        self.description = description
        self.id = id
        self.genres = genres
        self.moby_score = moby_score
        self.moby_url = moby_url
        self.num_votes = num_votes
        self.official_url = official_url
        self.platforms = platforms
        self.sample_cover = sample_cover
        self.sample_screenshots = sample_screenshots
        self.title = title

    def __str__(self) -> str:
        return str(
            {
                "alternate_titles": self.alternate_titles,
                "description": self.description,
                "id": self.id,
                "genres": self.genres,
                "moby_score": self.moby_score,
                "moby_url": self.moby_url,
                "official_url": self.official_url,
                "platforms": self.platforms,
                "sample_cover": self.sample_cover,
                "sample_screenshots": self.sample_screenshots,
                "title": self.title,
            }
        )

    def __repr__(self) -> str:
        return self.__str__()


class MobyGamesClient(ClientBase):
    __BASE_MOBYGAMES_SEARCH_URL = "https://api.mobygames.com/v1"
    __api_key: str

    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config, RateLimit(360, DatePart.HOUR))
        self.__api_key = self._config.moby_games_api_key

    async def _make_request(self, route: str, params: Dict = {}) -> any:
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
        game_ids: List[int] = [],
        limit: int = 100,
        offset: int = 0,
        platform_ids: List[int] = [],
        genre_ids: List[int] = [],
        group_ids: List[int] = [],
        title: str = "",
        format: Literal["id", "brief", "normal"] = "normal",
    ) -> List[Game]:
        res = await self._make_request(
            "games",
            {
                "id": game_ids,
                "limit": limit,
                "offset": offset,
                "platform": platform_ids,
                "genre": genre_ids,
                "group": group_ids,
                "title": title,
                "format": format,
            },
        )

        try:
            return [
                Game(
                    [
                        AlternateTitle(alt["description"], alt["title"])
                        for alt in game["alternative_titles"]
                    ]
                    if game.get("alternative_titles") is not None
                    else [],
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
                            Platform(
                                platform["platform_id"], platform["platform_name"]
                            ),
                            platform["first_release_date"],
                        )
                        for platform in game["platforms"]
                    ],
                    Cover(
                        game["sample_cover"]["height"],
                        game["sample_cover"]["image"],
                        game["sample_cover"]["platforms"],
                        game["sample_cover"]["thumbnail_image"],
                        game["sample_cover"]["width"],
                    )
                    if game.get("sample_cover") is not None
                    else None,
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
        except KeyError:
            raise

    async def match_game(
        self, game: ExcelGame
    ) -> List[Tuple[GameMatch, ValidationInfo]]:
        results = await self.games(title=game.title)
        matches: List[Tuple[GameMatch, ValidationInfo]] = []
        validator = MatchValidator()

        async def get_years(game_id: int, platform_id: int):
            game_platforms = await self.game_platforms(game_id, platform_id)

            years = []

            for gp in game_platforms.get("releases") or []:
                if gp.get("release_date") is not None:
                    years.append(int(gp["release_date"][0:4]))

            return years

        for g in results:
            if g.platforms is None:
                continue

            platform_names = [p.platform.name for p in g.platforms]
            pid = 0

            for p in g.platforms:
                if MatchValidator.verify_platform(game.platform, [p.platform.name]):
                    pid = p.platform.id

            match = validator.validate(game, g.title, platform_names)

            if match.matched:
                if MatchValidator.verify_release_year(
                    game.release_date.year, await get_years(g.id, pid)
                ):
                    matches.append((GameMatch(g.title, g.moby_url, g.id, g), match))
            elif g.alternate_titles is not None:
                if any(
                    match.matched
                    for match in [
                        validator.validate(game, alt.title, platform_names)
                        for alt in g.alternate_titles
                    ]
                ):
                    if MatchValidator.verify_release_year(
                        game.release_date.year, await get_years(g.id, pid)
                    ):
                        matches.append((GameMatch(g.title, g.moby_url, g.id, g), match))

        return matches
