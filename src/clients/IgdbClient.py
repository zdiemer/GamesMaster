from __future__ import annotations

import aiohttp
import asyncio
import unicodedata
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List

from config import Config
from excel_game import ExcelGame
from helpers import validate

class IgdbClient:
    __BASE_TWITCH_AUTH_URL = 'https://id.twitch.tv/oauth2/token?'
    __BASE_IGDB_URL = 'https://api.igdb.com/v4'

    __access_token: str
    __auth_expiration: datetime
    __client_id: str
    __client_secret: str
    __platforms: List[Dict]
    __requests_per_second: Dict[int, int]

    def __init__(self, client_id: str, client_secret: str):
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__requests_per_second = {}

    @staticmethod
    async def create(config: Config = None) -> IgdbClient:
        if config is None:
            config = Config.create()

        client = IgdbClient(config.igdb_client_id, config.igdb_client_secret)
        await client._authorize()
        await client._init_platforms()
        return client

    async def _authorize(self):
        url = self.__BASE_TWITCH_AUTH_URL + urllib.parse.urlencode({
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'client_credentials'})

        async with aiohttp.ClientSession() as session:
            async with session.post(url) as res:
                res_json = await res.json()
                self.__access_token = res_json['access_token']
                self.__auth_expiration = datetime.utcnow() + timedelta(seconds=res_json['expires_in'])

    async def _make_request(self, route: str, data: str):
        cur_sec = datetime.utcnow().second
        if self.__requests_per_second.get(cur_sec) == 4:
            await asyncio.sleep(1)
            self.__requests_per_second.clear()
        elif self.__requests_per_second.get(cur_sec) == 0:
            self.__requests_per_second.clear()
        self.__requests_per_second[cur_sec] = (self.__requests_per_second.get(cur_sec) or 0) + 1
            
        if datetime.utcnow() > self.__auth_expiration:
            self._authorize()

        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.__BASE_IGDB_URL}/{route}', headers=self._get_headers(), data=data) as res:
                return await res.json()

    def _get_headers(self):
        if self.__access_token is None:
            raise RuntimeError
        return {'Client-ID': self.__client_id, 'Authorization': f'Bearer {self.__access_token}'}

    async def _init_platforms(self):
        platforms = await self.platforms('fields name; limit 500;')
        self.__platforms = {}
        for p in platforms:
            self.__platforms[p['id']] = p['name']

    async def alternative_names(self, data: str):
        return await self._make_request('alternative_names/', data)

    async def games(self, data: str):
        return await self._make_request('games/', data)
    
    async def platforms(self, data: str):
        return await self._make_request('platforms/', data)

    async def match_game(self, game: ExcelGame):
        processed_title = unicodedata.normalize('NFKD', game.title).replace('"', '\\"')
        search_data = f'search "{processed_title}"; fields alternative_names,id,name,platforms,genres,parent_game,url;'.encode('utf-8')

        results = await self.games(search_data)
        matches = []
        
        for r in results:
            platforms = r.get('platforms') or []
            platforms_processed = [self.__platforms[p] for p in platforms]
            if validate(game, r.get('name'), platforms_processed):
                matches.append(r)
            elif r.get('alternative_names') is not None:
                for alt in r['alternative_names']:
                    names = await self.alternative_names(f'fields name; where id = {alt};')
                    if len(names) > 1:
                        print('Unexpected multiple results for alternative names, taking first.')
                    elif len(names) == 0:
                        print(f'Failed to fetch alternative name with ID {alt}.')
                        continue
                    if validate(game, names[0].get('name'), platforms_processed):
                        matches.append(r)

        return matches