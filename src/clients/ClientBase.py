from __future__ import annotations

import aiohttp
from typing import Any, Dict, List, Optional, Tuple

from config import Config
from excel_game import ExcelGame
from match_validator import ValidationInfo


class ClientBase:
    _config: Config
    _default_headers: Dict[str, str]

    def __init__(self, config: Config = None):
        self._config = config or Config.create()
        self._default_headers = {"User-Agent": self._config.user_agent}

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: bool = True,
    ) -> str | Any:
        if headers is None:
            headers = self._default_headers
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as res:
                return await res.json() if json else await res.text()

    async def post(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        json: bool = True,
    ) -> str | Any:
        if headers is None:
            headers = self._default_headers
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, params=params, headers=headers, data=data
            ) as res:
                return await res.json() if json else await res.text()

    async def match_game(self, game: ExcelGame) -> List[Tuple[Any, ValidationInfo]]:
        raise NotImplementedError
