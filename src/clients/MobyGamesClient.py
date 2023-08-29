from __future__ import annotations

import aiohttp
import asyncio
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Literal, NamedTuple

from config import Config
from excel_game import ExcelGame
from helpers import validate

class GenreCategory:
    name: str
    id: int

    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id

class Genre:
    category: GenreCategory
    id: int
    description: str
    name: str

    def __init__(self, category: GenreCategory, id: int, name: str, description: str = None):
        self.category = category
        self.id = id
        self.name = name
        self.description = description

class Group:
    description: str
    id: int
    name: str

    def __init__(self, description: str, id: int, name: str):
        self.description = description
        self.id = id
        self.name = name

class Platform:
    id: int
    name: str

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class AlternateTitle:
    description: str
    title: str

    def __init__(self, description: str, title: str):
        self.description = description
        self.title = title

class GamePlatform(NamedTuple):
    platform: Platform
    first_release_date: str

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
            width: int):
        self.height = height
        self.image_url = image_url
        self.platforms = platforms
        self.thumbnail_image_url = thumbnail_image_url
        self.width = width

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
            width: int):
        self.caption = caption
        self.height = height
        self.image_url = image_url
        self.thumbnail_image_url = thumbnail_image_url
        self.width = width

class Game:
    alternate_titles: List[AlternateTitle]
    description: str
    id: int
    genres: List[Genre]
    moby_score: float
    moby_url: str
    num_votes: int
    official_url: str
    platforms: GamePlatform
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
            title: str):
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

class MobyGamesClient:
    __BASE_MOBYGAMES_SEARCH_URL = 'https://api.mobygames.com/v1'

    __api_key: str
    __next_call: datetime

    def __init__(self, api_key: str):
        self.__api_key = api_key
        self.__next_call = datetime.utcnow()

    @staticmethod
    async def create(config: Config = None) -> MobyGamesClient:
        if config is None:
            config = Config.create()

        return MobyGamesClient(config.moby_games_api_key)
    
    async def _make_request(self, route: str, params: Dict = {}) -> any:
        if self.__next_call > datetime.utcnow():
            delta = self.__next_call - datetime.utcnow()
            sleep_time_seconds = delta.seconds \
                + (delta.microseconds / 1_000_000.0)
            await asyncio.sleep(sleep_time_seconds)

        self.__next_call = datetime.utcnow() + timedelta(seconds=10)

        if params.get('api_key') is None:
            params['api_key'] = self.__api_key

        encoded_params = urllib.parse.urlencode(params, doseq=True)
        url = f'{self.__BASE_MOBYGAMES_SEARCH_URL}/{route}?{encoded_params}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                return await res.json()
            
    async def genres(self) -> List[Genre]:
        res = await self._make_request('genres')
        return [
            Genre(
                GenreCategory(genre['genre_category'], genre['genre_category_id']),
                genre['genre_id'],
                genre['genre_name'],
                genre['genre_description']
            ) for genre in res['genres']
        ]
    
    async def groups(self, limit: int = 100, offset: int = 0) -> List[Group]:
        if limit > 100:
            raise ValueError('limit has a maximum of 100')
        res = await self._make_request('groups', {'limit': limit, 'offset': offset})
        return [
            Group(
                group['group_description'],
                group['group_id'],
                group['group_name']
            ) for group in res['groups']
        ]
    
    async def platforms(self) -> List[Platform]:
        res = await self._make_request('platforms')
        return [
            Platform(
                platform['platform_id'],
                platform['platform_name']
            ) for platform in res['platforms']
        ]
            
    async def games(
            self,
            game_ids: List[int] = [],
            limit: int = 100,
            offset: int = 0,
            platform_ids: List[int] = [],
            genre_ids: List[int] = [],
            group_ids: List[int] = [],
            title: str = '',
            format: Literal['id', 'brief', 'normal'] = 'normal'
    ) -> List[Game]:
        res = await self._make_request(
            'games',
            {
                'id': game_ids,
                'limit': limit,
                'offset': offset,
                'platform': platform_ids,
                'genre': genre_ids,
                'group': group_ids,
                'title': title,
                'format': format
            })
        
        try:
            return [
                Game(
                    [AlternateTitle(alt['description'], alt['title']) for alt in game['alternative_titles']] \
                        if game.get('alternative_titles') is not None else [],
                    game['description'],
                    game['game_id'],
                    [Genre(
                        GenreCategory(genre['genre_category'], genre['genre_category_id']),
                        genre['genre_id'],
                        genre['genre_name']
                    ) for genre in game['genres']],
                    game['moby_score'],
                    game['moby_url'],
                    game['num_votes'],
                    game['official_url'],
                    [GamePlatform(
                        Platform(platform['platform_id'], platform['platform_name']),
                        platform['first_release_date']
                    ) for platform in game['platforms']],
                    Cover(
                        game['sample_cover']['height'],
                        game['sample_cover']['image'],
                        game['sample_cover']['platforms'],
                        game['sample_cover']['thumbnail_image'],
                        game['sample_cover']['width']
                    ) if game.get('sample_cover') is not None else None,
                    [Screenshot(
                        screenshot['caption'],
                        screenshot['height'],
                        screenshot['image'],
                        screenshot['thumbnail_image'],
                        screenshot['width']
                    ) for screenshot in game['sample_screenshots']],
                    game['title']
                ) for game in res['games']
            ]
        except KeyError:
            print(res)
            raise

    async def match_game(self, game: ExcelGame):
        results =  await self.games(title=game.title)
        matches = []

        for g in results:
            if g.platforms is None:
                continue
            platform_names = [p.platform.name for p in g.platforms]
            if validate(game, g.title, platform_names):
                matches.append(g)
            elif g.alternate_titles is not None:
                if any(validate(game, alt.title, platform_names) for alt in g.alternate_titles):
                    matches.append(g)

        return matches