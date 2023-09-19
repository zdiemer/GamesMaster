import asyncio
from typing import Any, Dict, List, Optional, Tuple, Type, Set

import pandas as pd
from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry
from steam import Steam

from config import Config
from game_match import DataSource, GameMatch
from excel_game import ExcelGame, ExcelRegion as Region
from match_validator import MatchValidator, ValidationInfo
from clients.ClientBase import ClientBase
from clients.GameFaqsClient import GameFaqsClient
from clients.GiantBombClient import GiantBombClient
from clients.IgdbClient import IgdbClient
from clients.MetacriticClient import MetacriticClient
from clients.MobyGamesClient import MobyGamesClient
from clients.PriceChartingClient import PriceChartingClient
from clients.RomHackingClient import RomHackingClient


class SteamWrapper(ClientBase):
    _client: Steam

    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config)
        self._client = Steam(config.steam_web_api_key)

    async def match_game(
        self, game: ExcelGame
    ) -> List[Tuple[GameMatch, ValidationInfo]]:
        if game.platform.lower() != "pc":
            return []

        validator = MatchValidator()
        try:
            results = self._client.apps.search_games(game.title)
            matches: List[Tuple[GameMatch, ValidationInfo]] = []

            for r in results["apps"]:
                if validator.titles_equal_fuzzy(r["name"], game.title):
                    matches.append((GameMatch(r["name"], r["link"], r["id"], r), None))

            return matches
        except ValueError:
            # Swallowing exceptions from Steam API library
            return []


class HLTBWrapper(ClientBase):
    def __init__(self, config: Config = None):
        config = config or Config.create()
        super().__init__(config)

    async def match_game(
        self, game: ExcelGame
    ) -> List[Tuple[GameMatch, ValidationInfo]]:
        results: List[HowLongToBeatEntry] = await HowLongToBeat().async_search(
            game.title
        )
        matches: List[Tuple[GameMatch, ValidationInfo]] = []
        validator = MatchValidator()

        for res in results:
            match = validator.validate(
                game, res.game_name, res.profile_platforms, [res.release_world]
            )
            if match.matched:
                matches.append(
                    (
                        GameMatch(res.game_name, res.game_web_link, res.game_id, res),
                        match,
                    )
                )
                continue
            match = validator.validate(
                game, res.game_alias, res.profile_platforms, [res.release_world]
            )
            if match.matched:
                matches.append(
                    (
                        GameMatch(res.game_name, res.game_web_link, res.game_id, res),
                        match,
                    )
                )

        return matches


class ExcelParser:
    _ALL_CLIENTS: Dict[DataSource, Type[ClientBase]] = {
        # DataSource.GAME_FAQS: GameFaqsClient,
        DataSource.GIANT_BOMB: GiantBombClient,
        DataSource.IGDB: IgdbClient,
        DataSource.METACRITIC: MetacriticClient,
        DataSource.MOBY_GAMES: MobyGamesClient,
        DataSource.ROM_HACKING: RomHackingClient,
        DataSource.STEAM: SteamWrapper,
        DataSource.HLTB: HLTBWrapper,
        DataSource.PRICE_CHARTING: PriceChartingClient,
    }

    config: Config
    games: pd.DataFrame
    enabled_clients: Set[DataSource]

    def __init__(self, enabled_clients: Set[DataSource] = None):
        self.config = Config.create()
        self.games = self._parse_excel()
        self.games["Id"] = self.games.index + 1
        self.enabled_clients = enabled_clients or set(self._ALL_CLIENTS.keys())

    def _parse_excel(self, sheet: str = "Games") -> pd.DataFrame:
        return pd.read_excel(
            "static/games.xlsx", sheet_name=sheet, keep_default_na=False
        )

    async def get_matches_for_source(
        self, source: DataSource, games_override: Optional[pd.DataFrame] = None
    ) -> Dict[int, List[Tuple[GameMatch, ValidationInfo]]]:
        matches: Dict[int, List[Tuple[GameMatch, ValidationInfo]]] = {}
        if source not in self.enabled_clients:
            return matches
        client = self._ALL_CLIENTS[source](self.config)
        games = games_override if games_override is not None else self.games
        for _, row in games.iterrows():
            game = ExcelGame(
                row["Id"],
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

            game_matches = await client.match_game(game)

            for gm in game_matches:
                gm[0].source = source

            matches[game.id] = game_matches

        return matches

    def get_match_option_selection(
        self,
        source: DataSource,
        game: ExcelGame,
        options: List[GameMatch],
    ) -> int:
        print(f"\nMultiple matches from {source.name} detected:\n")
        max_i = 0
        for i, option in enumerate(options):
            url = f" ({option.url})" if option.url is not None else ""
            id = f", ID = {option.id}" if option.id is not None else ""
            print(f"{i+1}. {option.title}{url}{id}")
            max_i = i + 1
        print(f"{max_i+1}. None of the above")
        release = (
            game.release_date.year if game.release_date is not None else "Early Access"
        )
        val = input(
            f"Pick which option best matches {game.title} ({game.platform}) [{release}]: "
        )
        while not str.isdigit(val) or int(val) < 1 or int(val) > len(options) + 1:
            val = input("Invalid selection, please select from the above list: ")
        return int(val) - 1

    def get_match_from_multiple_matches(
        self,
        game: ExcelGame,
        matches: List[Tuple[GameMatch, ValidationInfo]],
        source: DataSource,
    ) -> Any:
        if len(matches) > 1:
            match_options = matches
            exact_matches = list(
                filter(lambda m: m[1] is not None and m[1].exact, matches)
            )
            if len(exact_matches) > 1:
                match_options = exact_matches
            else:
                return match_options[0][0].id

            selection = self.get_match_option_selection(
                source,
                game,
                [m[0] for m in match_options],
            )

            if selection > len(match_options):
                return None

            return match_options[selection][0]
        elif len(matches) == 1:
            return matches[0][0]

    async def match_all_games(self, games_override: Optional[pd.DataFrame] = None):
        tasks: List[asyncio.Task[Dict[int, List[Tuple[GameMatch, ValidationInfo]]]]] = [
            asyncio.create_task(self.get_matches_for_source(source, games_override))
            for source in self.enabled_clients
        ]

        running_tasks = []
        running_tasks.extend(tasks)

        results: Dict[int, List[Tuple[GameMatch, ValidationInfo]]] = {}

        while any(running_tasks):
            await asyncio.sleep(0)
            for t in tasks:
                if t.done() and t in running_tasks:
                    running_tasks.remove(t)
                    for k, v in t.result().items():
                        if k in results:
                            results[k].extend(v)
                        else:
                            results[k] = v

        final_results: Dict[int, List[GameMatch]] = {}
        for id, mat in results.items():
            game_results: Dict[int, List[GameMatch]] = {}

            row = self.games.loc[self.games["Id"] == id].iloc[0]

            game = ExcelGame(
                row["Id"],
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

            for source in self.enabled_clients:
                source_matches = list(filter(lambda m: m[0].source == source, mat))
                matches_only: List[GameMatch] = [m[0] for m in source_matches]

                if len(source_matches) > 1:
                    matches_only = [
                        self.get_match_from_multiple_matches(
                            game, source_matches, source
                        )
                    ]

                if id in game_results:
                    game_results[id].extend(matches_only)
                else:
                    game_results[id] = matches_only
            if not any(game_results[id]):
                print(f"Missing a match for {id}")
            else:
                print(
                    f"Found {len(game_results[id])} match for {game.title} ({game.platform}) [{game.release_date.year}]"
                )
                final_results.update(game_results)
        return final_results


if __name__ == "__main__":
    parser = ExcelParser()
    asyncio.run(parser.match_all_games(parser.games))
