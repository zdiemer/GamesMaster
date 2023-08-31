import asyncio
from typing import Any, Callable, List

import pandas as pd
from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry
from steam import Steam

from config import Config
from excel_game import ExcelGame, ExcelRegion as Region
from helpers import titles_equal_normalized, validate
from clients.GiantBombClient import GiantBombClient
from clients.IgdbClient import IgdbClient
from clients.MetacriticClient import MetacriticClient, MetacriticGame
from clients.MobyGamesClient import MobyGamesClient
from clients.RomHackingClient import RomHackingClient

class GameMatch:
    igdb_id: int
    giantbomb_id: int
    mobygames_id: int
    steam_app_id: int
    hltb_id: int
    metacritic_info: MetacriticGame
    romhacking_info: any

    def __init__(
            self,
            igdb_id: int = None,
            giantbomb_id: int = None,
            mobygames_id: int = None,
            steam_app_id: int = None,
            hltb_id: int = None,
            metacritic_info: MetacriticGame = None,
            romhacking_info = None):
        self.igdb_id = igdb_id
        self.giantbomb_id = giantbomb_id
        self.mobygames_id = mobygames_id
        self.steam_app_id = steam_app_id
        self.hltb_id = hltb_id
        self.metacritic_info = metacritic_info
        self.romhacking_info = romhacking_info

def parse_excel(sheet: str = 'Games') -> pd.DataFrame:
    return pd.read_excel('static/games.xlsx', sheet_name=sheet, keep_default_na=False)

def get_match_option_selection(source: str, game: ExcelGame, options: List, renderer: Callable[[Any], str]) -> int:
    print(f'\nMultiple matches on {source} detected:\n')
    for i, option in enumerate(options):
        print(f'{i+1}. {renderer(option)}')
    release = game.release_date.year if game.release_date is not None else 'Early Access'
    val = input(f'Pick which option best matches {game.title} ({game.platform}) [{release}]: ')
    while not str.isdigit(val) or int(val) < 1 or int(val) > len(options):
        val = input(f'Invalid selection, please select from the above list: ')
    return int(val) - 1


async def search_game_mappings(games: pd.DataFrame):
    config = Config.create()

    igdb_client = await IgdbClient.create(config)
    gb_client = await GiantBombClient.create(config)
    mb_client = await MobyGamesClient.create(config)
    mc_client = MetacriticClient.create()
    rh_client = RomHackingClient.create()

    matches: List[GameMatch] = []

    for _, row in games.loc[games['Release Region'] == Region.JAPAN.value].sample(100).iterrows():
        match: GameMatch = GameMatch()
        game = ExcelGame(
            row['Title'],
            row['Platform'],
            row['Release Date'] if row['Release Date'] != 'Early Access' else None,
            Region(row['Release Region']),
            row['Publisher'],
            row['Developer'],
            row['Franchise'],
            row['Genre'],
            row['Notes']
        )
        print(f'Processing {game.title} ({game.platform}) [{game.release_date.year if game.release_date is not None else "Early Access"}]...')


        igdb_matches = await igdb_client.match_game(game)

        if len(igdb_matches) > 1:
            selection = get_match_option_selection(
                'IGDB', game, igdb_matches, lambda m: f'{m["name"]} ({m["url"]}, ID # {m["id"]})')
            match.igdb_id = igdb_matches[selection]["id"]
        elif len(igdb_matches) == 1:
            match.igdb_id = igdb_matches[0]["id"]

        gb_matches = await gb_client.match_game(game)

        if len(gb_matches) > 1:
            selection = get_match_option_selection(
                'Giant Bomb', game, gb_matches, lambda m: f'{m["name"]} ({m["api_detail_url"]}, ID # {m["guid"]})')
            match.giantbomb_id = gb_matches[selection]["guid"]
        elif len(gb_matches) == 1:
            match.giantbomb_id = gb_matches[0]["guid"]

        mb_matches = await mb_client.match_game(game)

        if len(mb_matches) > 1:
            selection = get_match_option_selection(
                'MobyGames', game, mb_matches, lambda m: f'{m.title} ({m.moby_url}, ID # {m.id})')
            match.mobygames_id = mb_matches[selection].id
        elif len(mb_matches) == 1:
            match.mobygames_id = mb_matches[0].id

        steam_matches = search_steam(game, config.steam_web_api_key)

        if len(steam_matches) > 1:
            selection = get_match_option_selection(
                'Steam', game, steam_matches, lambda m: f'{m["name"]} ({m["link"]}, ID # {m["id"]})')
            match.steam_app_id = steam_matches[selection]['id']
        elif len(steam_matches) == 1:
            match.steam_app_id = steam_matches[0]['id']

        hltb_matches = await search_hltb(game)

        if len(hltb_matches) > 1:
            selection = get_match_option_selection(
                'HLTB', game, hltb_matches, lambda m: f'{m.game_name} ({m.game_web_link}, ID # {m.game_id})')
            match.hltb_id = hltb_matches[selection].game_id
        elif len(hltb_matches) == 1:
            match.hltb_id = hltb_matches[0].game_id

        meta_matches = await mc_client.match_game(game)

        if len(meta_matches) > 1:
            selection = get_match_option_selection(
                'Metacritic', game, meta_matches, lambda m: f'{m.title} ({m.url})')
            match.metacritic_info = meta_matches[selection]
        elif len(meta_matches) == 1:
            match.metacritic_info = meta_matches[0]

        rh_matches = await rh_client.match_game(game)

        if len(rh_matches) > 1:
            selection = get_match_option_selection(
                'RomHacking', game, rh_matches, lambda m: f'{m["name"]} ({m["url"]})')
            match.romhacking_info = rh_matches[selection]
        elif len(rh_matches) == 1:
            print(rh_matches[0])
            match.romhacking_info = rh_matches[0]

        if not match.igdb_id and not match.giantbomb_id \
                and not match.mobygames_id and not match.steam_app_id \
                and not match.hltb_id and not match.metacritic_info \
                and not match.romhacking_info:
            print(f'No matches detected... :(')
            continue

        matches.append(match)

    return matches

async def search_hltb(game: ExcelGame) -> List[HowLongToBeatEntry]:
    results: List[HowLongToBeatEntry] = await HowLongToBeat().async_search(game.title)
    matches = []
    
    for res in results:
        if validate(game, res.game_name, res.profile_platforms) \
                or validate(game, res.game_alias, res.profile_platforms):
            matches.append(res)

    return matches

def search_steam(game: ExcelGame, api_key: str):
    if game.platform.lower() != 'pc':
        return []

    steam = Steam(api_key)
    try:
        results = steam.apps.search_games(game.title)
        matches = []

        for r in results['apps']:
            if titles_equal_normalized(r['name'], game.title):
                matches.append(r)

        return matches
    except ValueError as e:
        return []
    

if __name__ == '__main__':
    asyncio.run(search_game_mappings(parse_excel()))