import json

class Config:
    moby_games_api_key: str
    giant_bomb_api_key: str
    igdb_client_id: str
    igdb_client_secret: str
    steam_web_api_key: str
    itchio_api_key: str

    def __init__(
            self,
            moby_games_api_key: str,
            giant_bomb_api_key: str,
            igdb_client_id: str,
            igdb_client_secret: str,
            steam_web_api_key: str,
            itchio_api_key: str):
        self.moby_games_api_key = moby_games_api_key
        self.giant_bomb_api_key = giant_bomb_api_key
        self.igdb_client_id = igdb_client_id
        self.igdb_client_secret = igdb_client_secret
        self.steam_web_api_key = steam_web_api_key
        self.itchio_api_key = itchio_api_key

    @staticmethod
    def create():
        with open('static/config.json', 'r') as f:
            config = json.loads(f.read())
            return Config(
                config['mobyGamesApiKey'],
                config['giantBombApiKey'],
                config['igdbClientId'],
                config['igdbClientSecret'],
                config['steamWebApiKey'],
                config['itchioApiKey'])