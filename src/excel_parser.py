"""Parser for custom Excel-based game backlog spreadsheet

This class implements functionality for parsing contents of games.xlsx,
matching it with games from multiple DataSources and then re-joining the
parsed data for a unified output.

Typical usage:

    parser = ExcelParser()
    matches = parser.match_all_games()
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Type, Set

import jsonpickle
import pandas as pd
from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry
from steam import Steam

import clients
from config import Config
from game_match import DataSource, GameMatch, GameMatchResult, GameMatchResultSet
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
        super().__init__(
            validator, config, clients.RateLimit(5, clients.DatePart.SECOND)
        )
        self._client = Steam(config.steam_web_api_key)

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform != "PC"

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        async def do_search() -> Dict[str, list]:
            res = self._client.apps.search_games(game.title)
            await asyncio.sleep(0)
            return res

        max_retries = 3
        retries = 0
        should_retry = True
        results: List[HowLongToBeatEntry] = []

        while should_retry and retries < max_retries:
            try:
                results = await self._rate_limiter.request("steam", do_search)
                should_retry = False
            except Exception:
                retries += 1
                should_retry = True

        if results is None or retries == max_retries:
            return []

        matches: List[GameMatch] = []

        for res in results["apps"]:
            match = self.validator.validate(game, res["name"])
            match.platform_matched = True
            match.date_matched = True
            if match.matched:
                matches.append(
                    GameMatch(res["name"], res["link"], res["id"], res, match)
                )

        return matches


class HLTBWrapper(clients.ClientBase):
    """Wrapper class for third-party How Long to Beat client.

    HLTBWrapper implements the clients.ClientBase match_game function
    and wraps a third-party How Long to Beat client library for fetching
    information about games from How Long to Beat.
    """

    def __init__(self, validator: MatchValidator, config: Config = None):
        config = config or Config.create()
        super().__init__(
            validator, config, clients.RateLimit(5, clients.DatePart.SECOND)
        )

    async def match_game(self, game: ExcelGame) -> List[GameMatch]:
        async def do_search() -> Optional[List[HowLongToBeatEntry]]:
            res = await HowLongToBeat().async_search(game.title)
            return res

        max_retries = 3
        retries = 0
        should_retry = True
        results: Optional[List[HowLongToBeatEntry]] = []

        while should_retry and retries < max_retries:
            try:
                results = await self._rate_limiter.request("hltb", do_search)
                should_retry = False
            except Exception:
                retries += 1
                should_retry = True

        if results is None or retries == max_retries:
            return []

        matches: List[GameMatch] = []

        for res in results:
            match = self.validator.validate(
                game, res.game_name, res.profile_platforms, [res.release_world]
            )

            if match.likely_match:
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

            if match.likely_match:
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
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG,
            format="%(levelname)s %(asctime)s - %(message)s",
            datefmt="%y-%m-%d %I:%M:%S %p",
        )

    def _parse_excel(self, sheet: str = "Games") -> pd.DataFrame:
        """Internal method for parsing Excel to a pandas.DataFrame"""
        return pd.read_excel(
            "static/games.xlsx", sheet_name=sheet, keep_default_na=False
        )

    def row_to_game(self, row: pd.Series) -> ExcelGame:
        return ExcelGame(
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

    async def get_matches_for_source(
        self, source: DataSource, games_override: Optional[pd.DataFrame] = None
    ) -> GameMatchResultSet:
        """Fetches matches for the games property for a given source.

        This method will loop through all the rows of the games object and
        match it against a given external source.

        Args:
            source: A DataSource to fetch matches for
            games_override: An optional DataFrame to override the internal games

        Returns:
            A dictionary mapping of game ID (from the pandas.DataFrame) to a list of GameMatches
        """
        results = GameMatchResultSet()
        if source not in self.enabled_clients:
            return results

        client = self._ALL_CLIENTS[source](self.__validator, self.config)
        games = games_override if games_override is not None else self.games

        row_count, _ = games.shape
        processed_count = 0
        start = datetime.utcnow()
        last_log = datetime.utcnow() - timedelta(seconds=5)

        def as_cyan(s: str) -> str:
            return f"\033[96m{s}\033[00m"

        def as_purple(s: str) -> str:
            return f"\033[95m{s}\033[00m"

        def as_green(s: str) -> str:
            return f"\033[92m{s}\033[00m"

        def as_red(s: str) -> str:
            return f"\033[91m{s}\033[00m"

        for _, row in games.iterrows():
            game = self.row_to_game(row)

            success, game_matches, exc = await client.try_match_game(game)
            processed_count += 1

            if success and game_matches is not None:
                gmr = GameMatchResult(game, self.filter_matches(game_matches))
                results.successes.append(gmr)

            if not success:
                results.errors.append(GameMatchResult(game, error=exc))
                continue

            if game_matches is None:
                # Game was skipped due to should_skip, no need to log process
                results.skipped.append(GameMatchResult(game))
                continue

            match_string = (
                f"{len(game_matches)} potential match"
                f"{'es' if len(game_matches) != 1 else ''}"
            )

            row_time = datetime.utcnow()
            elapsed = row_time - start
            estimated_s = (row_count - processed_count) * (
                elapsed.total_seconds() / processed_count
            )
            estimated = timedelta(seconds=estimated_s)

            if last_log <= datetime.utcnow() - timedelta(seconds=5):
                logging.info(
                    (
                        "%s: Processed %s - %s - %s/%s (%s%%), "
                        "Elapsed: %s, Estimated Time Remaining: %s"
                    ),
                    as_cyan(source),
                    as_purple(game.full_name),
                    match_string,
                    processed_count,
                    row_count,
                    f"{(processed_count/row_count)*100:,.2f}",
                    as_green(str(elapsed)),
                    as_red(str(estimated)),
                )

        logging.info(
            "%s: Finished processing all rows, Total Elapsed: %s",
            as_cyan(source),
            as_green(str(datetime.utcnow() - start)),
        )
        return results

    def filter_matches(
        self,
        matches: List[GameMatch],
    ) -> List[GameMatch]:
        if len(matches) > 1:

            def filter_full_matches(mats: List[GameMatch]) -> List[GameMatch]:
                return list(
                    filter(
                        lambda m: m.validation_info is not None
                        and m.validation_info.full_match,
                        mats,
                    )
                )

            filtered_matches = matches

            exact_matches = list(
                filter(
                    lambda m: m.validation_info is not None and m.validation_info.exact,
                    matches,
                )
            )

            if len(exact_matches) > 1:
                filtered_matches = exact_matches

                full_matches = filter_full_matches(exact_matches)

                if len(full_matches) > 1:
                    filtered_matches = full_matches
                elif len(full_matches) == 1:
                    return [full_matches[0]]
            elif len(exact_matches) == 1:
                return [exact_matches[0]]
            else:
                full_matches = filter_full_matches(exact_matches)

                if len(full_matches) > 1:
                    filtered_matches = full_matches
                elif len(full_matches) == 1:
                    return [full_matches[0]]

            return filtered_matches

        if len(matches) == 1:
            return [matches[0]]

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

        Returns:
            The array location selection.
        """
        print(f"\nMultiple matches from {source.name} detected:\n")
        max_i = 0
        for i, option in enumerate(options):
            url = f" ({option.url})" if option.url is not None else ""
            option_id = f", ID = {option.id}" if option.id is not None else ""
            print(f"{i+1}. {option.title}{url}{option_id}")
            max_i = i + 1
        print(f"{max_i+1}. None of the above")
        val = input(f"Pick which option best matches {game.full_name}: ")
        while not str.isdigit(val) or int(val) < 1 or int(val) > len(options) + 1:
            val = input("Invalid selection, please select from the above list: ")
        return int(val) - 1

    def get_match_from_multiple_matches(
        self,
        game: ExcelGame,
        matches: List[GameMatch],
        source: DataSource,
    ) -> Tuple[bool, Optional[GameMatch]]:
        """Fetch a single match from multiple matches for a single source.

        This method wraps the get_match_option_selection method in an attempt to
        deduplicate match options without needing to prompt user input. That is, if
        there is a single "exact" match, assume that one is the correct match and don't
        ask for deduplication.

        Args:
            game: An ExcelGame to deduplicate matches for
            matches: A list of GameMatches to deduplicate
            source: A DataSource to deduplicate matches for

        Returns:
            The match selected or None if none of the above is selected.
        """
        if len(matches) > 1:
            selection = self.get_match_option_selection(
                source,
                game,
                matches,
            )

            if selection >= len(matches):
                return (True, None)

            return (True, matches[selection])

        if len(matches) == 1:
            return (False, matches[0])

        return (False, None)

    def confirm_non_full_match(
        self,
        source: DataSource,
        game: ExcelGame,
        match: GameMatch,
    ) -> bool:
        print(f"\nOne non-full match from {source.name} detected.\n")

        url = f" ({match.url})" if match.url is not None else ""
        option_id = f", ID = {match.id}" if match.id is not None else ""
        print(f"\t{match.title}{url}{option_id}\n")

        val = input(f"Is this an accurate match for {game.full_name}? (y/n): ")

        while val.lower().strip() not in {"y", "n"}:
            val = input("Invalid selection, please indicate y/n: ")

        return val.lower().strip() == "y"

    async def match_all_games(self, games_override: Optional[pd.DataFrame] = None):
        """Matches all games against all sources.

        This method kicks off an asyncio.Task for each DataSource that's currently
        enabled which matches all games against the source. That is, this method
        matches all games for all enabled sources.

        Args:
            games_override: Overrides the games property for the class

        Returns:
            A dictionary mapping Excel game IDs to GameMatches
        """
        tasks: List[asyncio.Task[GameMatchResultSet]] = [
            asyncio.create_task(
                self.get_matches_for_source(source, games_override), name=source.name
            )
            for source in self.enabled_clients
        ]

        results: Dict[DataSource, Dict[int, GameMatch]] = {}

        async def are_all_done(_tasks: List[asyncio.Task[GameMatchResultSet]]) -> bool:
            await asyncio.sleep(0)
            return all(t.done() for t in _tasks)

        processed: List[asyncio.Task[GameMatchResultSet]] = []

        while not await are_all_done(tasks):
            for task in tasks:
                if task.done() and task not in processed:
                    source = DataSource[task.get_name()]
                    if task.exception() is not None:
                        logging.warning(
                            "%s: Failed to run due to exception - %s",
                            source,
                            traceback.format_exception(task.exception()),
                        )
                        continue

                    result_set = task.result()

                    for gmr in result_set.errors:
                        logging.error(
                            "%s: Exception was thrown for %s - %s",
                            source,
                            gmr.game.full_name,
                            gmr.error,
                        )

                    game_dict: Dict[int, GameMatch] = {}

                    for gmr in result_set.successes:
                        was_user_input, match = self.get_match_from_multiple_matches(
                            gmr.game, gmr.matches, source
                        )

                        if match is not None:
                            if (
                                was_user_input
                                or match.validation_info.full_match
                                or match.validation_info.exact
                                or self.confirm_non_full_match(source, gmr.game, match)
                            ):
                                game_dict[gmr.game.id] = match

                    results[source] = game_dict

                    with open(
                        f"static/{source}-matches.json", "w", encoding="utf-8"
                    ) as file:
                        file.write(jsonpickle.encode(results[source]))

                    if any(result_set.errors):
                        with open(
                            f"static/{source}-errors.json", "w", encoding="utf-8"
                        ) as file:
                            file.write(jsonpickle.encode(result_set.errors))

                    processed.append(task)

        games_df = self.games if games_override is None else games_override

        missing_game_ids = set(games_df["Id"].unique().astype(int).tolist()).difference(
            {g for k in results.values() for g in k.keys()}
        )

        for game_id in missing_game_ids:
            row = games_df.loc[games_df["Id"] == game_id].iloc[0]
            game = self.row_to_game(row)

            print(f"{game.full_name} had no matches across all sources.")


if __name__ == "__main__":
    # Which parsers should run, empty list means all parsers
    which_parsers: Optional[List[DataSource]] = []

    # Which parsers should not run, empty list means no parsers will be excluded
    except_parsers: Optional[List[DataSource]] = [
        DataSource.GAME_FAQS,
        DataSource.MOBY_GAMES,
    ]

    parser = ExcelParser(
        set(which_parsers or list(DataSource)).difference(set(except_parsers or []))
    )

    # A DataFrame override to use instead of the entire Excel sheet, e.g. parser.games.sample(5)
    # for a random sample of 5 games. If None, then the entire sheet is used.
    g_override: Optional[pd.DataFrame] = parser.games.sample(5)

    asyncio.run(parser.match_all_games(g_override))
