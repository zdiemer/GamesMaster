"""Parser for custom Excel-based game backlog spreadsheet

This class implements functionality for parsing contents of games.xlsx,
matching it with games from multiple DataSources and then re-joining the
parsed data for a unified output.

Typical usage:

    parser = ExcelParser()
    matches = parser.match_all_games()
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Type, Set

import pandas as pd
from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry
from steam import Steam

import clients
from config import Config
from game_match import DataSource, GameMatch
from excel_game import ExcelGame, ExcelRegion as Region
from match_validator import MatchValidator


class SteamWrapper(clients.ClientBase):
    """Wrapper class for third-party Steam client.

    SteamWrapper implements the clients.ClientBase match_game function
    and wraps a third-party Steam client library for fetching information
    about games from Steam.

    Attributes:
        _client: A Steam object which represents the underlying Steam client
    """

    _client: Steam

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config)
        self._client = Steam(config.steam_web_api_key)

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        if game.platform.lower() != "pc":
            return []

        async def do_search() -> Dict[str, list]:
            res = self._client.apps.search_games(game.title)
            await asyncio.sleep(1)
            return res

        max_retries = 3
        retries = 0
        results: List[HowLongToBeatEntry] = []

        while not any(results) and retries < max_retries:
            try:
                results = await do_search()
            except Exception:
                retries += 1

        if retries == max_retries:
            return []

        matches: List[GameMatch] = []

        for res in results["apps"]:
            if self.validator.titles_equal_fuzzy(res["name"], game.title):
                matches.append(GameMatch(res["name"], res["link"], res["id"], res))

        return matches


class HLTBWrapper(clients.ClientBase):
    """Wrapper class for third-party How Long to Beat client.

    HLTBWrapper implements the clients.ClientBase match_game function
    and wraps a third-party How Long to Beat client library for fetching
    information about games from How Long to Beat.
    """

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(validator, config)

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        async def do_search() -> List[HowLongToBeatEntry]:
            res = await HowLongToBeat().async_search(game.title)
            await asyncio.sleep(1)
            return res

        max_retries = 3
        retries = 0
        results: List[HowLongToBeatEntry] = []

        while not any(results) and retries < max_retries:
            try:
                results = await do_search()
            except Exception:
                retries += 1

        if retries == max_retries:
            return []

        matches: List[GameMatch] = []

        for res in results:
            match = self.validator.validate(
                game, res.game_name, res.profile_platforms, [res.release_world]
            )

            if match.matched:
                matches.append(
                    GameMatch(
                        res.game_name,
                        res.game_web_link,
                        res.game_id,
                        res,
                        match,
                    )
                )
                continue

            match = self.validator.validate(
                game, res.game_alias, res.profile_platforms, [res.release_world]
            )

            if match.matched:
                matches.append(
                    GameMatch(
                        res.game_name,
                        res.game_web_link,
                        res.game_id,
                        res,
                        match,
                    )
                )

        return matches


class ExcelParser:
    """A class for extracting information from a custom Excel sheet matching its rows with sources.

    ExcelParser implements functionality for converting a custom Excel sheet
    which holds information on a game backlog into a more structured format by
    matching its contents against a number of external DataSources.

    Attributes:
        _ALL_CLIENTS: A dictionary mapping DataSources to client types
        config: A Config object holding configuration information such as API keys
        games: A pandas.DataFrame loaded on initialization from the Excel sheet
        enabled_clients: A set of clients which should be enabled for this run of the parser
        __validator: A MatchValidator to use for the client classes
    """

    _ALL_CLIENTS: Dict[DataSource, Type[clients.ClientBase]] = {
        DataSource.GAME_FAQS: clients.GameFaqsClient,
        DataSource.GIANT_BOMB: clients.GiantBombClient,
        DataSource.IGDB: clients.IgdbClient,
        DataSource.METACRITIC: clients.MetacriticClient,
        DataSource.MOBY_GAMES: clients.MobyGamesClient,
        DataSource.ROM_HACKING: clients.RomHackingClient,
        DataSource.STEAM: SteamWrapper,
        DataSource.HLTB: HLTBWrapper,
        DataSource.PRICE_CHARTING: clients.PriceChartingClient,
    }

    config: Config
    games: pd.DataFrame
    enabled_clients: Set[DataSource]

    __validator: MatchValidator

    def __init__(self, enabled_clients: Set[DataSource] = None):
        self.config = Config.create()
        self.games = self._parse_excel()
        self.games["Id"] = self.games.index + 1
        self.enabled_clients = enabled_clients or set(self._ALL_CLIENTS.keys())
        self.__validator = MatchValidator()

    def _parse_excel(self, sheet: str = "Games") -> pd.DataFrame:
        """Internal method for parsing Excel to a pandas.DataFrame"""
        return pd.read_excel(
            "static/games.xlsx", sheet_name=sheet, keep_default_na=False
        )

    async def get_matches_for_source(
        self, source: DataSource, games_override: Optional[pd.DataFrame] = None
    ) -> Dict[int, List[GameMatch]]:
        """Fetches matches for the games property for a given source.

        This method will loop through all the rows of the games object and
        match it against a given external source.

        Args:
            source: A DataSource to fetch matches for
            games_override: An optional DataFrame to override the internal games

        Returns:
            A dictionary mapping of game ID (from the pandas.DataFrame) to a list of GameMatches
        """
        matches: Dict[int, List[GameMatch]] = {}
        if source not in self.enabled_clients:
            return matches
        client = self._ALL_CLIENTS[source](self.__validator, self.config)
        games = games_override if games_override is not None else self.games
        row_count, _ = games.shape
        rows_processed = 0
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

            for gmatch in game_matches:
                gmatch.source = source

            matches[game.id] = game_matches
            rows_processed += 1

            print(
                f"{source}: Processed {game.title} - "
                f"{rows_processed}/{row_count} ({(rows_processed/row_count)*100:,.2f}%)"
            )

        print(f"{source}: Finished processing all rows")
        return matches

    def get_match_option_selection(
        self,
        source: DataSource,
        game: ExcelGame,
        options: List[GameMatch],
    ) -> int:
        """Prompts user input to choose a single match when multiple exist.

        When multiple matches exist for a single source, this function can be called
        to prompt user input and deduplicate the multiple matches into a single valid
        match. Every row in the sheet should only map to a single game per source (at most).

        Args:
            source: A DataSource to get a selection about
            game: An ExcelGame corresponding to the row in question
            options: A list of GameMatches to deduplicate
        """
        print(f"\nMultiple matches from {source.name} detected:\n")
        max_i = 0
        for i, option in enumerate(options):
            url = f" ({option.url})" if option.url is not None else ""
            option_id = f", ID = {option.id}" if option.id is not None else ""
            print(f"{i+1}. {option.title}{url}{option_id}")
            max_i = i + 1
        print(f"{max_i+1}. None of the above")
        val = input(f"Pick which option best matches {game.full_name}]: ")
        while not str.isdigit(val) or int(val) < 1 or int(val) > len(options) + 1:
            val = input("Invalid selection, please select from the above list: ")
        return int(val) - 1

    def get_match_from_multiple_matches(
        self,
        game: ExcelGame,
        matches: List[GameMatch],
        source: DataSource,
    ) -> Any:
        """Fetch a single match from multiple matches for a single source.

        This method wraps the get_match_option_selection method in an attempt to
        deduplicate match options without needing to prompt user input. That is, if
        there is a single "exact" match, assume that one is the correct match and don't
        ask for deduplication.

        Args:
            game: An ExcelGame to deduplicate matches for
            matches: A list of GameMatches to deduplicate
            source: A DataSource to deduplicate matches for
        """
        if len(matches) > 1:
            match_options = matches
            exact_matches = list(
                filter(
                    lambda m: m.validation_info is not None and m.validation_info.exact,
                    matches,
                )
            )
            if len(exact_matches) > 1:
                match_options = exact_matches
            else:
                return match_options[0].id

            selection = self.get_match_option_selection(
                source,
                game,
                match_options,
            )

            if selection > len(match_options):
                return None

            return match_options[selection]

        if len(matches) == 1:
            return matches[0]

        return None

    async def match_all_games(
        self, games_override: Optional[pd.DataFrame] = None
    ) -> Dict[int, List[GameMatch]]:
        """Matches all games against all sources.

        This method kicks off an asyncio.Task for each DataSource that's currently
        enabled which matches all games against the source. That is, this method
        matches all games for all enabled sources.

        Args:
            games_override: Overrides the games property for the class

        Returns:
            A dictionary mapping Excel game IDs to GameMatches
        """
        tasks: List[asyncio.Task[Dict[int, List[GameMatch]]]] = [
            asyncio.create_task(self.get_matches_for_source(source, games_override))
            for source in self.enabled_clients
        ]

        running_tasks = []
        running_tasks.extend(tasks)

        results: Dict[int, List[GameMatch]] = {}

        while any(running_tasks):
            await asyncio.sleep(0)
            for task in tasks:
                if task.done() and task in running_tasks:
                    running_tasks.remove(task)
                    for key, val in task.result().items():
                        if key in results:
                            results[key].extend(val)
                        else:
                            results[key] = val

        final_results: Dict[int, List[GameMatch]] = {}
        for game_id, mat in results.items():
            game_results: Dict[int, List[GameMatch]] = {}

            row = self.games.loc[self.games["Id"] == game_id].iloc[0]

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
                source_matches = list(filter(lambda m: m.source == source, mat))

                if len(source_matches) > 1:
                    source_matches = [
                        self.get_match_from_multiple_matches(
                            game, source_matches, source
                        )
                    ]

                if game_id in game_results:
                    game_results[game_id].extend(source_matches)
                else:
                    game_results[game_id] = source_matches
            if not any(game_results[game_id]):
                print(f"Missing a match for {game.full_name}]")
            else:
                print(
                    f"Found {len(game_results[game_id])} match"
                    f"{'es' if len(game_results[game_id]) != 1 else ''} "
                    f"for {game.full_name}"
                )
                final_results.update(game_results)
        with open("static/matches.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(final_results))
        return final_results


if __name__ == "__main__":
    parser = ExcelParser()
    asyncio.run(parser.match_all_games())
