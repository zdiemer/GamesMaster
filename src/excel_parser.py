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
import math
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Type, Set

import jsonpickle
import pandas as pd
from howlongtobeatpy import HowLongToBeat, HowLongToBeatEntry
from steam import Steam

import clients
import clients.game_faqs
from config import Config
from game_match import DataSource, GameMatch, GameMatchResult, GameMatchResultSet
from excel_game import (
    ExcelGame,
    ExcelRegion as Region,
    Playability,
    PlayingStatus,
    TranslationStatus,
)
from logging_decorator import LoggingColor, LoggingDecorator
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
        results: Optional[List[Any]] = []

        while should_retry and retries < max_retries:
            try:
                results = await self._rate_limiter.request("steam", do_search)
                should_retry = False
            except Exception:  # pylint: disable=broad-except
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
            except Exception:  # pylint: disable=broad-except
                retries += 1
                should_retry = True

        if results is None or retries == max_retries:
            return []

        matches: List[GameMatch] = []

        for res in results:
            match = self.validator.validate(
                game,
                res.game_name,
                res.profile_platforms,
                [res.release_world],
                developers=[res.profile_dev],
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
        DataSource.VG_CHARTZ: clients.VgChartzClient,
        DataSource.GAMEYE: clients.GameyeClient,
        DataSource.GAME_JOLT: clients.GameJoltClient,
    }

    config: Config
    games: pd.DataFrame
    enabled_clients: Set[DataSource]

    __running_clients: Dict[DataSource, clients.ClientBase] = {}
    __validator: MatchValidator

    def __init__(self, enabled_clients: Set[DataSource] = None):
        self.config = Config.create()
        self.games = self.__parse_excel()
        self.games["Id"] = self.games.index + 1
        self.enabled_clients = enabled_clients or set(self._ALL_CLIENTS.keys())
        self.__validator = MatchValidator()
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.WARN,
            format="%(levelname)s %(asctime)s - %(message)s",
            datefmt="%y-%m-%d %I:%M:%S %p",
        )

    def __parse_excel(self, sheet: str = "Games") -> pd.DataFrame:
        """Internal method for parsing Excel to a pandas.DataFrame"""
        return pd.read_excel(
            "static/games.xlsx", sheet_name=sheet, keep_default_na=False
        )

    def __row_to_game(self, row: pd.Series) -> ExcelGame:
        """Converts a Pandas row into an ExcelGame object.

        Given a row from the base spreadsheet, converts into a Python object.

        Args:
            row: A Pandas series representing a row in the spreadsheet

        Returns:
            An ExcelGame object representation of the given row
        """
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
            row["Estimated Time"],
            row["Completed"],
            row["Priority"],
            row["Metacritic Rating"],
            row["GameFAQs User Rating"],
            row["DLC"],
            row["Owned"],
            (
                TranslationStatus(row["English"])
                if row["English"] is not None and str(row["English"]).strip() != ""
                else None
            ),
            row["VR"],
            (
                PlayingStatus(row["Playing Status"])
                if row["Playing Status"] is not None
                and str(row["Playing Status"]).strip() != ""
                else None
            ),
            (
                row["Date Purchased"]
                if str(row["Date Purchased"]).strip() != ""
                else None
            ),
            row["Purchase Price"],
            row["Rating"],
            Playability(row["Playable"]),
            row["Completion Time"],
        )

    async def __get_matches_for_source(
        self,
        source: DataSource,
        games_override: Optional[pd.DataFrame] = None,
        offset: int = 0,
        batch_size: int = 500,
    ) -> GameMatchResultSet:
        """Fetches matches for the games property for a given source.

        This method will loop through all the rows of the games object and
        match it against a given external source.

        Args:
            source: A DataSource to fetch matches for
            games_override: An optional DataFrame to override the internal games
            offset: A starting index to begin iteration at
            batch_size: The number of games to process in this iteration

        Returns:
            A dictionary mapping of game ID (from the pandas.DataFrame) to a list of GameMatches
        """
        results = GameMatchResultSet(offset, batch_size)
        if source not in self.enabled_clients:
            return results

        client = self.__running_clients.get(source) or self._ALL_CLIENTS[source](
            self.__validator, self.config
        )

        self.__running_clients[source] = client

        games = games_override if games_override is not None else self.games
        total_rows, _ = games.shape

        if offset > total_rows:
            raise IndexError("Offset is out of bounds of the DataFrame")

        batch_rows = min(batch_size, total_rows)
        processed_count = 0
        start = datetime.utcnow()
        last_log = datetime.utcnow() - timedelta(seconds=5)

        batch_no = int((offset / batch_size) + 1)
        total_batches = math.ceil(float(total_rows) / batch_size)

        logging.info(
            "%s: Beginning batch %s of %s (%s games/batch) - %s/%s games processed (%s%%)",
            LoggingDecorator.as_color(source, LoggingColor.BRIGHT_CYAN),
            LoggingDecorator.as_color(batch_no, LoggingColor.BRIGHT_BLUE),
            LoggingDecorator.as_color(total_batches, LoggingColor.BRIGHT_BLUE),
            LoggingDecorator.as_color(batch_size, LoggingColor.BRIGHT_BLUE),
            LoggingDecorator.as_color(offset, LoggingColor.BRIGHT_BLUE),
            LoggingDecorator.as_color(
                total_rows,
                LoggingColor.BRIGHT_BLUE,
            ),
            LoggingDecorator.as_color(
                f"{(float(offset) / total_rows)*100:.2f}",
                LoggingColor.BRIGHT_BLUE,
            ),
        )

        for i, row in games.iloc[offset : offset + batch_size].iterrows():
            game = self.__row_to_game(row)

            try:
                success, game_matches, exc = await client.try_match_game(game)
            except (
                clients.ImmediatelyStopStatusError,
                clients.ResponseNotOkError,
            ) as exc:
                results.errors.extend(
                    [
                        GameMatchResult(self.__row_to_game(r[1]), error=exc)
                        for r in games.iloc[i:].iterrows()
                    ]
                )
                break

            processed_count += 1

            if success and game_matches is not None:
                gmr = GameMatchResult(game, self.__filter_matches(game_matches))
                results.successes.append(gmr)

            if not success:
                results.errors.append(GameMatchResult(game, error=exc))
                logging.error(
                    ("%s (batch %s/%s): Error processing %s - %s"),
                    LoggingDecorator.as_color(source, LoggingColor.BRIGHT_CYAN),
                    LoggingDecorator.as_color(batch_no, LoggingColor.BRIGHT_CYAN),
                    LoggingDecorator.as_color(total_batches, LoggingColor.BRIGHT_CYAN),
                    LoggingDecorator.as_color(
                        game.full_name, LoggingColor.BRIGHT_MAGENTA
                    ),
                    LoggingDecorator.as_color(exc, LoggingColor.BRIGHT_RED),
                )
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
            estimated_s = (batch_rows - processed_count) * (
                elapsed.total_seconds() / processed_count
            )
            estimated = timedelta(seconds=estimated_s)

            if last_log <= datetime.utcnow() - timedelta(seconds=5):
                logging.info(
                    (
                        "%s (batch %s/%s): Processed %s - %s - %s/%s (%s%%), "
                        "Elapsed: %s, Estimated Time Remaining: %s"
                    ),
                    LoggingDecorator.as_color(source, LoggingColor.BRIGHT_CYAN),
                    LoggingDecorator.as_color(batch_no, LoggingColor.BRIGHT_CYAN),
                    LoggingDecorator.as_color(total_batches, LoggingColor.BRIGHT_CYAN),
                    LoggingDecorator.as_color(
                        game.full_name, LoggingColor.BRIGHT_MAGENTA
                    ),
                    match_string,
                    processed_count,
                    min(batch_rows, total_rows - offset),
                    f"{(processed_count/batch_rows)*100:,.2f}",
                    LoggingDecorator.as_color(str(elapsed), LoggingColor.BRIGHT_GREEN),
                    LoggingDecorator.as_color(str(estimated), LoggingColor.BRIGHT_RED),
                )

        logging.info(
            "%s: Finished processing all rows for batch %s, Batch Elapsed: %s",
            LoggingDecorator.as_color(source, LoggingColor.BRIGHT_CYAN),
            LoggingDecorator.as_color(batch_no, LoggingColor.BRIGHT_BLUE),
            LoggingDecorator.as_color(
                str(datetime.utcnow() - start), LoggingColor.BRIGHT_GREEN
            ),
        )

        return results

    def __filter_matches(
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

    def __get_match_option_selection(
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

    def __get_match_from_multiple_matches(
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
            selection = self.__get_match_option_selection(
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

    def __confirm_non_full_match(
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

    async def match_games(
        self,
        games_override: Optional[pd.DataFrame] = None,
        offset: int = 0,
        batch_size: int = 500,
        save_output: bool = False,
    ):
        """Matches all games against all sources.

        This method kicks off an asyncio.Task for each DataSource that's currently
        enabled which matches all games against the source. That is, this method
        matches all games for all enabled sources.

        Args:
            games_override: Overrides the games property for the class
            batch_size: The number of games to process per source in one batch

        Returns:
            A dictionary mapping Excel game IDs to GameMatches
        """
        games_df = self.games if games_override is None else games_override
        total_rows, _ = games_df.shape

        tasks: List[asyncio.Task[GameMatchResultSet]] = [
            asyncio.create_task(
                self.__get_matches_for_source(
                    source, games_override, offset, batch_size
                ),
                name=source.name,
            )
            for source in self.enabled_clients
        ]

        results: Dict[DataSource, Dict[int, GameMatch]] = {}
        processed: List[asyncio.Task[GameMatchResultSet]] = []

        while any(tasks):
            await asyncio.sleep(0)
            for task in tasks:
                if task.done() and task not in processed:
                    source = DataSource[task.get_name()]
                    if task.exception() is not None:
                        processed.append(task)
                        tasks.remove(task)
                        del self.__running_clients[source]

                        logging.warning(
                            "%s: Failed to run due to exception - %s",
                            LoggingDecorator.as_color(source, LoggingColor.BRIGHT_CYAN),
                            LoggingDecorator.as_color(
                                traceback.format_exception(task.exception()),
                                LoggingColor.RED,
                            ),
                        )
                        continue

                    result_set = task.result()

                    batch_results: Dict[int, GameMatch] = {}
                    game_results: Dict[int, ExcelGame] = {}

                    for gmr in result_set.successes:
                        was_user_input, match = self.__get_match_from_multiple_matches(
                            gmr.game, gmr.matches, source
                        )

                        if match is not None:
                            if (
                                was_user_input
                                or match.validation_info.full_match
                                or match.validation_info.exact
                                or self.__confirm_non_full_match(
                                    source, gmr.game, match
                                )
                            ):
                                batch_results[gmr.game.id] = match
                                game_results[gmr.game.id] = gmr.game

                    if source not in results:
                        results[source] = batch_results
                    else:
                        results[source].update(batch_results)

                    min_rows = result_set.offset

                    max_rows = min(
                        result_set.offset + result_set.batch_size - 1, total_rows
                    )

                    if any(batch_results):
                        self.__report_missing_playtime_and_scores(
                            batch_results, game_results
                        )
                        if save_output:
                            with open(
                                f"output/{source.name.lower()}_matches-{min_rows}-{max_rows}.json",
                                "w",
                                encoding="utf-8",
                            ) as file:
                                file.write(jsonpickle.encode(batch_results))

                    if any(result_set.errors):
                        if save_output:
                            with open(
                                f"output/{source.name.lower()}_errors-{min_rows}-{max_rows}.json",
                                "w",
                                encoding="utf-8",
                            ) as file:
                                file.write(jsonpickle.encode(result_set.errors))

                    processed.append(task)
                    tasks.remove(task)

                    if result_set.offset + result_set.batch_size < total_rows:
                        tasks.append(
                            asyncio.create_task(
                                self.__get_matches_for_source(
                                    source,
                                    games_override,
                                    result_set.offset + result_set.batch_size,
                                    result_set.batch_size,
                                ),
                                name=source.name,
                            )
                        )
                    else:
                        del self.__running_clients[source]

        missing_game_ids = set(games_df["Id"].unique().astype(int).tolist()).difference(
            {g for k in results.values() for g in k.keys()}
        )

        missing_games: Dict[int, ExcelGame] = {}

        for game_id in missing_game_ids:
            row = games_df.loc[games_df["Id"] == game_id].iloc[0]
            game = self.__row_to_game(row)
            missing_games[game_id] = game

        if any(missing_games):
            if save_output:
                with open(
                    f"output/missing_{datetime.utcnow().strftime('%Y-%m-%d')}.json",
                    "w",
                    encoding="utf-8",
                ) as file:
                    file.write(jsonpickle.encode(missing_games))

    def __report_missing_playtime_and_scores(
        self, results: Dict[int, GameMatch], game_results: Dict[int, ExcelGame]
    ):
        for game_id, _match in results.items():
            if (
                game_results[game_id].estimated_playtime is None
                and game_results[game_id].release_date is not None
                and not game_results[game_id].completed
                and isinstance(_match.match_info, HowLongToBeatEntry)
                and _match.match_info.main_story > 0
            ):
                print(
                    f"Playtime missing for {game_results[game_id].full_name}. HLTB: {_match.match_info.main_story}"
                )
            if (
                game_results[game_id].metacritic_rating is None
                and game_results[game_id].release_date is not None
                and isinstance(_match.match_info, dict)
                and _match.match_info.get("critics") is not None
            ):
                print(
                    f"Metacritic score missing for {game_results[game_id].full_name}. MC: {_match.match_info['critics']['score']}%"
                )
            if (
                game_results[game_id].gamefaqs_rating is None
                and game_results[game_id].release_date is not None
                and isinstance(_match.match_info, clients.game_faqs.GameFaqsGame)
                and _match.match_info.user_rating is not None
                and _match.match_info.user_rating > 0
                and (_match.match_info.user_rating_count or 0) > 1
            ):
                print(
                    f"GameFAQs score missing for {game_results[game_id].full_name}. MC: {(_match.match_info.user_rating / 5) * 100:.2f}%"
                )

    def find_missing_ids_from_outputs(
        self,
        games_override: Optional[pd.DataFrame] = None,
        output_file_name: str = "manual",
        output_to_file: bool = True,
        output_to_stdout: bool = False,
        sources: Set[DataSource] = None,
    ) -> Dict[int, ExcelGame]:
        found_ids = set()
        sources = sources or set(DataSource)

        for root, _, files in os.walk("output/"):
            for name in list(
                filter(
                    lambda f: "_matches-" in f
                    and DataSource[f.split("-")[0].replace("_matches", "").upper()]
                    in sources,
                    files,
                )
            ):
                with open(f"{os.path.join(root, name)}", "r", encoding="utf-8") as file:
                    file_matches: Dict[int, GameMatch] = jsonpickle.decode(file.read())

                    found_ids = found_ids.union(
                        set(int(k) for k in file_matches.keys())
                    )

        games_df = self.games if games_override is None else games_override

        missing_game_ids: Set[int] = set(
            games_df["Id"].unique().astype(int).tolist()
        ).difference(found_ids)

        missing_games: Dict[int, ExcelGame] = {}

        for game_id in sorted(missing_game_ids):
            row = games_df.loc[games_df["Id"] == game_id].iloc[0]
            game = self.__row_to_game(row)
            missing_games[game_id] = game

            if output_to_stdout:
                print(
                    f"Missing game ID {game_id}: {game.title} ({game.platform}) [{game.release_year or 'Early Access'}]"
                )

        if any(missing_games) and output_to_file:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
            with open(
                f"output/missing-{output_file_name}_{timestamp}.json",
                "w",
                encoding="utf-8",
            ) as file:
                file.write(jsonpickle.encode(missing_games))

        if output_to_stdout:
            print(
                f"Total Missing Games: {len(missing_games)} ({len(missing_games) / games_df.shape[0]*100:.2f}%)"
            )

        return missing_games


if __name__ == "__main__":
    # Which parsers should run, empty list means all parsers
    which_parsers: Optional[List[DataSource]] = [DataSource.HLTB, DataSource.METACRITIC]

    # Which parsers should not run, empty list means no parsers will be excluded
    except_parsers: Optional[List[DataSource]] = []

    parser = ExcelParser(
        set(which_parsers or list(DataSource)).difference(set(except_parsers or []))
    )

    # global_missing_games = parser.find_missing_ids_from_outputs(
    #     output_to_file=False,
    #     sources=set(
    #         [
    #             DataSource.IGDB,
    #         ]
    #     ),
    # )
    # global_missing_game_ids = list(global_missing_games.keys())

    # A DataFrame override to use instead of the entire Excel sheet, e.g. parser.games.sample(5)
    # for a random sample of 5 games. If None, then the entire sheet is used.
    g_override: Optional[pd.DataFrame] = parser.games[
        (
            (parser.games["Estimated Time"] == "")
            | (parser.games["Metacritic Rating"] == "")
        )
        & (parser.games["Completed"] == 0)
    ]

    print(g_override.shape)

    missing_ids = []

    asyncio.run(parser.match_games(g_override, offset=0, batch_size=1000))
