from __future__ import annotations

import aiohttp
import urllib.parse
from enum import Enum
from typing import Dict

from config import Config
from excel_game import ExcelGame
from match_validator import MatchValidator

class GiantBombFormat(Enum):
    JSON = 'json'
    XML = 'xml'

class GiantBombClient:
    __BASE_GIANTBOMB_URL = 'https://www.giantbomb.com/api'
    __headers = {}

    __api_key: str

    def __init__(self, api_key: str, user_agent: str):
        self.__api_key = api_key
        self.__headers = {'User-Agent': user_agent}

    @staticmethod
    async def create(config: Config = None) -> GiantBombClient:
        if config is None:
            config = Config.create()
        
        return GiantBombClient(config.giant_bomb_api_key, config.user_agent)
    
    async def _make_request(self, route: str, params: Dict, format: GiantBombFormat):
        if params.get('api_key') is None:
            params['api_key'] = self.__api_key

        if params.get('format') is None:
            params['format'] = format.value

        encoded_params = urllib.parse.urlencode(params)
        url = f'{self.__BASE_GIANTBOMB_URL}/{route}?{encoded_params}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.__headers) as res:
                return await res.json()
            
    async def search(self, query: str, format: GiantBombFormat = GiantBombFormat.JSON):
        return await self._make_request('search/', params={'query': query}, format=format)

    async def match_game(self, game: ExcelGame):
        results = await self.search(game.title)
        matches = []
        only_exact = False
        validator = MatchValidator()

        for r in results['results']:
            if r.get('platforms') is None:
                continue
            platforms = [p['name'] for p in r['platforms']]
            match = validator.validate(game, r['name'], platforms):
            if match.matched:
                if match.exact:
                    only_exact = True
                elif only_exact:
                    continue
                matches.append(r)
            elif r.get('aliases') is not None:
                if any(validate(game, alias, platforms) for alias in r['aliases'].split('\n')):
                    matches.append(r)
        return matches