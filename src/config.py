"""Configuration class for ExcelParser

Holds configuration values for the project.
"""

import json


class Config:
    """Configuration class for the ExcelParser project."""

    moby_games_api_key: str
    giant_bomb_api_key: str
    igdb_client_id: str
    igdb_client_secret: str
    steam_web_api_key: str
    price_charting_api_key: str
    user_agent: str

    def __init__(
        self,
        moby_games_api_key: str,
        giant_bomb_api_key: str,
        igdb_client_id: str,
        igdb_client_secret: str,
        steam_web_api_key: str,
        price_charting_api_key: str,
        version: str,
    ):
        self.moby_games_api_key = moby_games_api_key
        self.giant_bomb_api_key = giant_bomb_api_key
        self.igdb_client_id = igdb_client_id
        self.igdb_client_secret = igdb_client_secret
        self.steam_web_api_key = steam_web_api_key
        self.price_charting_api_key = price_charting_api_key
        self.user_agent = f"GamesMaster/{version}"

    @staticmethod
    def create():
        """Creates an instance of Config.

        This method is for creating a Config instance.

        Returns:
            A Config object
        """
        version = ""
        with open("D:/Code/GameMaster/static/version", "r", encoding="utf-8") as file:
            version = file.read()
        with open(
            "D:/Code/GameMaster/static/config.json", "r", encoding="utf-8"
        ) as file:
            config = json.loads(file.read())
            return Config(
                config["mobyGamesApiKey"],
                config["giantBombApiKey"],
                config["igdbClientId"],
                config["igdbClientSecret"],
                config["steamWebApiKey"],
                config["priceChartingApiKey"],
                version,
            )
