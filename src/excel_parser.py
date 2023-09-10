import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple

import pandas as pd
from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry
from steam import Steam

from config import Config
from excel_game import ExcelGame, ExcelRegion as Region
from match_validator import MatchValidator, ValidationInfo
from clients.ClientBase import ClientBase
from clients.GiantBombClient import GiantBombClient
from clients.IgdbClient import IgdbClient
from clients.MetacriticClient import MetacriticClient, MetacriticGame
from clients.MobyGamesClient import MobyGamesClient
from clients.PriceChartingClient import PriceChartingClient
from clients.RomHackingClient import RomHackingClient


class DataSource(Enum):
    # GAME_FAQS = 1
    GIANT_BOMB = 2
    IGDB = 3
    METACRITIC = 4
    MOBY_GAMES = 5
    ROM_HACKING = 6
    STEAM = 7
    HLTB = 8
    PRICE_CHARTING = 9
    # TODO: Add ArcadeDb
    # TODO: Add Itch.io
    # TODO: Add Epic
    # TODO: Add uPlay


class GameMatch:
    igdb_id: int
    giantbomb_id: int
    mobygames_id: int
    steam_app_id: int
    hltb_id: int
    metacritic_info: MetacriticGame
    romhacking_info: any
    pc_id: int

    def __init__(
        self,
        igdb_id: int = None,
        giantbomb_id: int = None,
        mobygames_id: int = None,
        steam_app_id: int = None,
        hltb_id: int = None,
        metacritic_info: MetacriticGame = None,
        romhacking_info=None,
        pc_id: int = None,
    ):
        self.igdb_id = igdb_id
        self.giantbomb_id = giantbomb_id
        self.mobygames_id = mobygames_id
        self.steam_app_id = steam_app_id
        self.hltb_id = hltb_id
        self.metacritic_info = metacritic_info
        self.romhacking_info = romhacking_info
        self.pc_id = pc_id

    @property
    def match_count(self):
        return sum(
            [
                self.igdb_id is not None,
                self.giantbomb_id is not None,
                self.mobygames_id is not None,
                self.steam_app_id is not None,
                self.hltb_id is not None,
                self.metacritic_info is not None,
                self.romhacking_info is not None,
                self.pc_id is not None,
            ]
        )

    @property
    def matching_sources(self):
        return list(
            filter(
                lambda x: x is not None,
                [
                    DataSource.IGDB if self.igdb_id is not None else None,
                    DataSource.GIANT_BOMB if self.giantbomb_id is not None else None,
                    DataSource.MOBY_GAMES if self.mobygames_id is not None else None,
                    DataSource.STEAM if self.steam_app_id is not None else None,
                    DataSource.HLTB if self.hltb_id is not None else None,
                    DataSource.METACRITIC if self.metacritic_info is not None else None,
                    DataSource.ROM_HACKING
                    if self.romhacking_info is not None
                    else None,
                    DataSource.PRICE_CHARTING if self.pc_id is not None else None,
                ],
            )
        )


def parse_excel(sheet: str = "Games") -> pd.DataFrame:
    return pd.read_excel("static/games.xlsx", sheet_name=sheet, keep_default_na=False)


def get_match_option_selection(
    source: str, game: ExcelGame, options: List, renderer: Callable[[Any], str]
) -> int:
    print(f"\nMultiple matches on {source} detected:\n")
    for i, option in enumerate(options):
        print(f"{i+1}. {renderer(option)}")
    release = (
        game.release_date.year if game.release_date is not None else "Early Access"
    )
    val = input(
        f"Pick which option best matches {game.title} ({game.platform}) [{release}]: "
    )
    while not str.isdigit(val) or int(val) < 1 or int(val) > len(options):
        val = input("Invalid selection, please select from the above list: ")
    return int(val) - 1


def get_match_id_from_matches(
    game: ExcelGame,
    matches: List[Tuple[Any, ValidationInfo]],
    id_getter: Callable[[Any], Any],
    site_name: str,
    option_renderer: Callable[[Any], str],
) -> Any:
    if len(matches) > 1:
        match_options = matches
        exact_matches = list(filter(lambda m: m[1].exact, matches))
        if len(exact_matches) > 1:
            match_options = exact_matches
        else:
            return id_getter(match_options[0][0])

        selection = get_match_option_selection(
            site_name,
            game,
            [m[0] for m in match_options],
            option_renderer,
        )
        return id_getter(match_options[selection][0])
    elif len(matches) == 1:
        return id_getter(matches[0][0])


async def search_game_mappings(games: pd.DataFrame, sources: List[DataSource] = []):
    config = Config.create()

    all_clients: Dict[DataSource, ClientBase] = {
        DataSource.GIANT_BOMB: GiantBombClient(config),
        DataSource.IGDB: await IgdbClient.create(config),
        DataSource.METACRITIC: MetacriticClient.create(),
        DataSource.MOBY_GAMES: await MobyGamesClient.create(config),
        DataSource.ROM_HACKING: RomHackingClient.create(),
        DataSource.STEAM: None,
        DataSource.HLTB: None,
        DataSource.PRICE_CHARTING: PriceChartingClient(config),
    }

    enabled_clients = {}

    if not any(sources):
        enabled_clients = all_clients
    else:
        for source in sources:
            enabled_clients[source] = all_clients[source]

    matches: List[GameMatch] = []

    for _, row in games.sample(10).iterrows():
        expected_sources = len(enabled_clients)
        match: GameMatch = GameMatch()
        game = ExcelGame(
            row["Title"],
            row["Platform"],
            row["Release Date"] if row["Release Date"] != "Early Access" else None,
            Region(row["Release Region"]),
            row["Publisher"],
            row["Developer"],
            row["Franchise"],
            row["Genre"],
            row["Notes"],
            row["Format"],
        )
        print(
            f'Processing {game.title} ({game.platform}) [{game.release_date.year if game.release_date is not None else "Early Access"}]...'
        )

        if DataSource.IGDB in enabled_clients:
            igdb_matches = await enabled_clients[DataSource.IGDB].match_game(game)
            match.igdb_id = get_match_id_from_matches(
                game,
                igdb_matches,
                lambda m: m["id"],
                "IGDB",
                lambda m: f'{m["name"]} ({m["url"]}, ID # {m["id"]})',
            )

        if DataSource.GIANT_BOMB in enabled_clients:
            gb_matches = await enabled_clients[DataSource.GIANT_BOMB].match_game(game)
            match.giantbomb_id = get_match_id_from_matches(
                game,
                gb_matches,
                lambda m: m["guid"],
                "Giant Bomb",
                lambda m: f'{m["name"]} ({m["api_detail_url"]}, ID # {m["guid"]})',
            )

        if DataSource.MOBY_GAMES in enabled_clients:
            mb_matches = await enabled_clients[DataSource.MOBY_GAMES].match_game(game)
            match.mobygames_id = get_match_id_from_matches(
                game,
                mb_matches,
                lambda m: m.id,
                "MobyGames",
                lambda m: f"{m.title} ({m.moby_url}, ID # {m.id})",
            )

        if DataSource.STEAM in enabled_clients:
            if game.platform != "PC":
                expected_sources -= 1

            steam_matches = search_steam(game, config.steam_web_api_key)

            if len(steam_matches) > 1:
                selection = get_match_option_selection(
                    "Steam",
                    game,
                    steam_matches,
                    lambda m: f'{m["name"]} ({m["link"]}, ID # {m["id"]})',
                )
                match.steam_app_id = steam_matches[selection]["id"]
            elif len(steam_matches) == 1:
                match.steam_app_id = steam_matches[0]["id"]

        if DataSource.HLTB in enabled_clients:
            hltb_matches = await search_hltb(game)
            match.hltb_id = get_match_id_from_matches(
                game,
                hltb_matches,
                lambda m: m.game_id,
                "HLTB",
                lambda m: f"{m.game_name} ({m.game_web_link}, ID # {m.game_id})",
            )

        if DataSource.METACRITIC in enabled_clients:
            if game.release_region != Region.NORTH_AMERICA:
                expected_sources -= 1

            pc_matches = await enabled_clients[DataSource.METACRITIC].match_game(game)
            match.metacritic_info = get_match_id_from_matches(
                game,
                pc_matches,
                lambda m: m,
                "Metacritic",
                lambda m: f"{m.title} ({m.url})",
            )

        if DataSource.ROM_HACKING in enabled_clients:
            if game.release_region in (Region.NORTH_AMERICA, Region.EUROPE):
                expected_sources -= 1

            rh_matches = await enabled_clients[DataSource.ROM_HACKING].match_game(game)

            if len(rh_matches) > 1:
                selection = get_match_option_selection(
                    "RomHacking",
                    game,
                    rh_matches,
                    lambda m: f'{m["name"]} ({m["url"]})',
                )
                match.romhacking_info = rh_matches[selection]
            elif len(rh_matches) == 1:
                match.romhacking_info = rh_matches[0]

        if DataSource.PRICE_CHARTING in enabled_clients:
            if game.owned_format not in ("Both", "Physical"):
                expected_sources -= 1

            pc_matches = await enabled_clients[DataSource.PRICE_CHARTING].match_game(
                game
            )
            match.pc_id = get_match_id_from_matches(
                game,
                pc_matches,
                lambda m: m["id"],
                "Price Charting",
                lambda m: f"{m['product-name']}",
            )

        print(
            f"{game.title} matched {match.match_count} out of "
            f"{expected_sources} sources: "
            f"{', '.join([str(s.name) for s in match.matching_sources])}"
        )

        if match.match_count > 0:
            matches.append(match)
        else:
            print(f"{game.title} had no matches!")

    return matches


async def search_hltb(game: ExcelGame) -> List[HowLongToBeatEntry]:
    results: List[HowLongToBeatEntry] = await HowLongToBeat().async_search(game.title)
    matches = []
    validator = MatchValidator()

    for res in results:
        match = validator.validate(
            game, res.game_name, res.profile_platforms, [res.release_world]
        )
        if match.matched:
            matches.append((res, match))
            continue
        match = validator.validate(
            game, res.game_alias, res.profile_platforms, [res.release_world]
        )
        if match.matched:
            matches.append((res, match))

    return matches


def search_steam(game: ExcelGame, api_key: str):
    if game.platform.lower() != "pc":
        return []

    steam = Steam(api_key)
    validator = MatchValidator()
    try:
        results = steam.apps.search_games(game.title)
        matches = []

        for r in results["apps"]:
            if validator.titles_equal_fuzzy(r["name"], game.title):
                matches.append(r)

        return matches
    except ValueError:
        # Swallowing exceptions from Steam API library
        return []


if __name__ == "__main__":
    asyncio.run(search_game_mappings(parse_excel()))
