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
import pickle
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Tuple, Type, Set

import jsonpickle
import pandas as pd

import clients
import clients.game_faqs
from config import Config
from game_match import DataSource, GameMatch, GameMatchResult, GameMatchResultSet
from excel_game import ExcelGame
from excel_loader import ExcelLoader
from logging_decorator import LoggingColor, LoggingDecorator
from match_validator import MatchValidator


class BatchLogger:
    source: DataSource
    batch_number: int
    total_batches: int
    batch_size: int

    def __init__(
        self, source: DataSource, batch_number: int, total_batches: int, batch_size: int
    ):
        self.source = source
        self.batch_number = batch_number
        self.total_batches = total_batches
        self.batch_size = batch_size

    def log(self, level: int, formatted_message: str):
        logging.log(
            level,
            "%s: Batch %s of %s (%s games/batch) - %s",
            LoggingDecorator.as_color(self.source, LoggingColor.BRIGHT_CYAN),
            LoggingDecorator.as_color(self.batch_number, LoggingColor.BRIGHT_BLUE),
            LoggingDecorator.as_color(self.total_batches, LoggingColor.BRIGHT_BLUE),
            LoggingDecorator.as_color(self.batch_size, LoggingColor.BRIGHT_BLUE),
            formatted_message,
        )


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
        DataSource.STEAM: clients.SteamWrapper,
        DataSource.HLTB: clients.HltbClient,
        DataSource.PRICE_CHARTING: clients.PriceChartingClient,
        DataSource.VG_CHARTZ: clients.VgChartzClient,
        DataSource.GAMEYE: clients.GameyeClient,
        DataSource.GAME_JOLT: clients.GameJoltClient,
        DataSource.COOPTIMUS: clients.CooptimusClient,
        DataSource.ARCADE_DATABASE: clients.ArcadeDatabaseClient,
    }

    config: Config
    enabled_clients: Set[DataSource]

    __running_clients: Dict[DataSource, clients.ClientBase] = {}
    __validator: MatchValidator
    __loader: ExcelLoader
    __df_cache: pd.DataFrame = None

    __processed_matches_by_source_and_type: Dict[
        DataSource,
        Dict[
            Literal["matches", "errors", "skipped"],
            Dict[str, GameMatchResult | GameMatch],
        ],
    ]

    def __init__(self, enabled_clients: Set[DataSource] = None):
        self.config = Config.create()
        self.__loader = ExcelLoader()
        self.enabled_clients = enabled_clients or set(self._ALL_CLIENTS.keys())
        self.__validator = MatchValidator()
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG,
            format="%(levelname)s %(asctime)s - %(message)s",
            datefmt="%y-%m-%d %I:%M:%S %p",
        )

        self.__processed_matches_by_source_and_type = {}

        for client in enabled_clients:
            self.__processed_matches_by_source_and_type[client] = {}

            self.__processed_matches_by_source_and_type[client]["matches"] = (
                ExcelParser.get_all_processed_hash_ids(client)
            )

            self.__processed_matches_by_source_and_type[client]["matches"].update(
                ExcelParser.get_all_processed_hash_ids(client, "no-matches")
            )

            self.__processed_matches_by_source_and_type[client]["skipped"] = (
                ExcelParser.get_all_processed_hash_ids(client, "skipped")
            )

            self.__processed_matches_by_source_and_type[client]["errors"] = (
                ExcelParser.get_all_processed_hash_ids(client, "errors")
            )

    @property
    def games(self) -> pd.DataFrame:
        if self.__df_cache is None:
            self.__df_cache = self.__loader.df
            self.__df_cache["Id"] = self.__df_cache.index + 1
        return self.__df_cache

    @staticmethod
    def get_all_processed_hash_ids(
        source: DataSource,
        output_type: Literal["matches", "errors", "skipped", "no-matches"] = "matches",
    ) -> Dict[str, GameMatchResult | GameMatch]:
        results: Dict[str, GameMatchResult | GameMatch] = {}
        source_name = source.name.lower()
        source_folder = f"output/{source_name}"

        if not os.path.exists(source_folder):
            return results

        for root, _, files in os.walk(source_folder):
            for file in files:
                if file.startswith(f"{output_type}-"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        cache_results: List[GameMatchResult] | Dict[str, GameMatch] = (
                            jsonpickle.loads(f.read())
                        )

                        if output_type == "matches":
                            results.update(cache_results)
                        else:
                            results.update({e.game.hash_id: e for e in cache_results})

        return results

    def __get_resumable_cache_file_name(
        self, source: DataSource, min_rows: int, max_rows: int
    ) -> str:
        if not os.path.isdir("output/resumable"):
            os.mkdir("output/resumable")

        return f"output/resumable/{source.name.lower()}-{min_rows}-{max_rows}-resumable.pkl"

    def __get_output_file_name(
        self,
        source: DataSource,
        min_rows: int,
        max_rows: int,
        output_type: Literal["matches", "errors", "skipped", "no-matches"] = "matches",
    ):
        source_name = source.name.lower()
        source_folder = f"output/{source_name}"

        if not os.path.isdir(source_folder):
            os.mkdir(source_folder)

        return f"{source_folder}/{output_type}-{min_rows}-{max_rows}.json"

    async def __get_matches_for_source(
        self,
        source: DataSource,
        offset: int = 0,
        batch_size: int = 500,
    ) -> Optional[GameMatchResultSet]:
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
        original_offset = offset
        results = GameMatchResultSet(offset, batch_size)
        if source not in self.enabled_clients:
            return results

        client = self.__running_clients.get(source) or self._ALL_CLIENTS[source](
            self.__validator, self.config
        )

        self.__running_clients[source] = client

        total_rows = len(self.__loader.games)

        if offset > total_rows:
            raise IndexError("Offset is out of bounds of the DataFrame")

        batch_rows = min(batch_size, total_rows)
        processed_count = 0
        start = datetime.utcnow()
        last_log = datetime.utcnow() - timedelta(seconds=5)

        batch_no = int((offset / batch_size) + 1)
        total_batches = math.ceil(float(total_rows) / batch_size)

        end_row = min(offset + batch_size - 1, total_rows)
        batch_stop = offset + batch_size

        logger = BatchLogger(source, batch_no, total_batches, batch_size)

        if os.path.exists(self.__get_output_file_name(source, offset, end_row)):
            all_matches: Set[Optional[str]] = set()

            for output_type in self.__processed_matches_by_source_and_type[source]:
                all_matches = all_matches.union(
                    set(
                        k
                        for k in self.__processed_matches_by_source_and_type[source][
                            output_type
                        ].keys()
                    )
                )

            sheet_game_hashes = set(
                g.hash_id for g in self.__loader.games[offset:batch_stop]
            )

            diff = sheet_game_hashes.difference(all_matches)

            if not any(diff):
                logger.log(logging.INFO, "Batch already exists.")
                return results

            diff_missing_str = LoggingDecorator.as_color(
                len(diff), LoggingColor.BRIGHT_BLUE
            )
            logger.log(
                logging.INFO,
                f"Batch has existing output, but {diff_missing_str} games are missing.",
            )

        resumable_cache_file_name = self.__get_resumable_cache_file_name(
            source, offset, end_row
        )

        if os.path.exists(resumable_cache_file_name):
            can_resume = False
            with open(resumable_cache_file_name, "rb") as resf:
                try:
                    cache_results: GameMatchResultSet = pickle.load(resf)

                    cache_result_hashes = (
                        set(g.game.hash_id for g in cache_results.successes)
                        .union(set(g.game.hash_id for g in cache_results.errors))
                        .union(set(g.game.hash_id for g in cache_results.skipped))
                    )

                    new_processed_count = len(cache_results) + len(
                        cache_results.skipped
                    )
                    new_offset = original_offset + new_processed_count

                    resumable_offset_hashes = set(
                        g.hash_id
                        for g in self.__loader.games[original_offset:new_offset]
                    )

                    diff = cache_result_hashes.difference(resumable_offset_hashes)

                    can_resume = not any(diff)
                except EOFError as exc:
                    can_resume = False
                    exc_str = LoggingDecorator.as_color(exc, LoggingColor.BRIGHT_RED)
                    logger.log(
                        logging.WARNING,
                        f"Batch is not able to be resumed due to an exception: {exc_str}",
                    )

                if can_resume:
                    results = cache_results
                    processed_count = new_processed_count
                    offset = new_offset
                else:
                    cache_hashes_str = LoggingDecorator.as_color(
                        len(cache_result_hashes), LoggingColor.BRIGHT_BLUE
                    )

                    resumable_hashes_str = LoggingDecorator.as_color(
                        len(resumable_offset_hashes), LoggingColor.BRIGHT_BLUE
                    )

                    diff_str = LoggingDecorator.as_color(
                        len(diff), LoggingColor.BRIGHT_BLUE
                    )

                    logger.log(
                        logging.WARNING,
                        "Batch is not able to be resumed due to mismatched hash counts: "
                        f"Resumable - {cache_hashes_str}, In-Batch - {resumable_hashes_str}, Diff - {diff_str}.",
                    )

            if can_resume:
                offset_str = LoggingDecorator.as_color(offset, LoggingColor.BRIGHT_BLUE)
                logger.log(
                    logging.INFO,
                    f"Batch is able to be resumed, starting at offset {offset_str}.",
                )

            os.remove(resumable_cache_file_name)

        offset_str = LoggingDecorator.as_color(offset, LoggingColor.BRIGHT_BLUE)

        total_str = LoggingDecorator.as_color(
            total_rows,
            LoggingColor.BRIGHT_BLUE,
        )

        progress_str = LoggingDecorator.as_color(
            f"{(float(offset) / total_rows)*100:.2f}",
            LoggingColor.BRIGHT_BLUE,
        )

        logger.log(
            logging.INFO,
            f"Beginning batch. {offset_str}/{total_str} games processed ({progress_str}%)",
        )

        try:
            for i, game in enumerate(self.__loader.games[offset:batch_stop]):
                if source in self.__processed_matches_by_source_and_type:
                    existing_gmr: Optional[GameMatchResult] = None
                    existing_gmr_type: Optional[
                        Literal["matches", "errors", "skipped"]
                    ] = None

                    if (
                        game.hash_id
                        in self.__processed_matches_by_source_and_type[source][
                            "skipped"
                        ]
                    ):
                        existing_gmr = self.__processed_matches_by_source_and_type[
                            source
                        ]["skipped"][game.hash_id]
                        if isinstance(existing_gmr, GameMatch):
                            existing_gmr = GameMatchResult(game, [existing_gmr])
                        existing_gmr_type = "skipped"
                    if (
                        game.hash_id
                        in self.__processed_matches_by_source_and_type[source][
                            "matches"
                        ]
                    ):
                        existing_gmr = self.__processed_matches_by_source_and_type[
                            source
                        ]["matches"][game.hash_id]
                        if isinstance(existing_gmr, GameMatch):
                            existing_gmr = GameMatchResult(game, [existing_gmr])
                        existing_gmr_type = "matches"

                if existing_gmr is not None:
                    if last_log <= datetime.utcnow() - timedelta(seconds=5):
                        game_str = LoggingDecorator.as_color(
                            game.full_name, LoggingColor.BRIGHT_MAGENTA
                        )

                        logger.log(
                            logging.INFO, f"Found {game_str} in existing results."
                        )

                        last_log = datetime.utcnow()
                    results.append(existing_gmr, existing_gmr_type)
                    processed_count += 1
                    continue

                try:
                    success, game_matches, exc = await client.try_match_game(game)
                except (
                    clients.ImmediatelyStopStatusError,
                    clients.ResponseNotOkError,
                ) as exc:
                    results.extend(
                        [
                            GameMatchResult(g, error=exc)
                            for g in self.__loader.games[i:]
                        ],
                        "error",
                    )
                    break

                processed_count += 1

                if success and game_matches is not None:
                    gmr = GameMatchResult(game, self.__filter_matches(game_matches))
                    results.append(gmr, "success")

                if not success:
                    results.append(GameMatchResult(game, error=exc), "error")
                    game_str = LoggingDecorator.as_color(
                        game.full_name, LoggingColor.BRIGHT_MAGENTA
                    )
                    exc_str = LoggingDecorator.as_color(exc, LoggingColor.BRIGHT_RED)
                    logger.log(
                        logging.ERROR, f"Error processing {game_str} - {exc_str}"
                    )
                    continue

                if game_matches is None:
                    # Game was skipped due to should_skip, no need to log process
                    results.append(GameMatchResult(game), "skipped")
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
                    game_str = LoggingDecorator.as_color(
                        game.full_name, LoggingColor.BRIGHT_MAGENTA
                    )

                    elapsed_str = LoggingDecorator.as_color(
                        str(elapsed), LoggingColor.BRIGHT_GREEN
                    )

                    estimated_str = LoggingDecorator.as_color(
                        str(estimated), LoggingColor.BRIGHT_RED
                    )

                    logger.log(
                        logging.INFO,
                        f"Processed {game_str} - {match_string} - {processed_count}/"
                        f"{min(batch_rows, total_rows - offset)} "
                        f"({(processed_count/batch_rows)*100:,.2f}%), Elapsed: "
                        f"{elapsed_str}, Estimated Time Remaining: {estimated_str}",
                    )

                    last_log = datetime.utcnow()
        except asyncio.CancelledError:
            with open(
                self.__get_resumable_cache_file_name(source, original_offset, end_row),
                "wb",
            ) as resf:
                pickle.dump(results, resf, pickle.HIGHEST_PROTOCOL)
            raise

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
        if games_override is not None:
            self.__loader.override_sheet(games_override)

        total_rows = len(self.__loader.games)

        tasks: List[asyncio.Task[GameMatchResultSet]] = [
            asyncio.create_task(
                self.__get_matches_for_source(source, offset, batch_size),
                name=source.name,
            )
            for source in self.enabled_clients
        ]

        results: Dict[DataSource, Dict[str, GameMatch]] = {}
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

                    batch_results: Dict[str, GameMatch] = {}
                    game_results: Dict[str, ExcelGame] = {}
                    no_matches: List[GameMatchResult] = []

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
                                batch_results[gmr.game.hash_id] = match
                                game_results[gmr.game.hash_id] = gmr.game
                            else:
                                no_matches.append(gmr)
                        else:
                            no_matches.append(gmr)

                    if source not in results:
                        results[source] = batch_results
                    else:
                        results[source].update(batch_results)

                    min_rows = result_set.offset

                    max_rows = min(
                        result_set.offset + result_set.batch_size - 1, total_rows
                    )

                    if any(batch_results):
                        if source in (DataSource.HLTB, DataSource.METACRITIC):
                            self.__report_missing_playtime_and_scores(
                                batch_results, game_results
                            )
                        if save_output:
                            with open(
                                self.__get_output_file_name(source, min_rows, max_rows),
                                "w",
                                encoding="utf-8",
                            ) as file:
                                file.write(jsonpickle.encode(batch_results))

                    if any(result_set.errors):
                        if save_output:
                            with open(
                                self.__get_output_file_name(
                                    source, min_rows, max_rows, "errors"
                                ),
                                "w",
                                encoding="utf-8",
                            ) as file:
                                file.write(jsonpickle.encode(result_set.errors))

                    if any(result_set.skipped):
                        if save_output:
                            with open(
                                self.__get_output_file_name(
                                    source, min_rows, max_rows, "skipped"
                                ),
                                "w",
                                encoding="utf-8",
                            ) as file:
                                file.write(jsonpickle.encode(result_set.skipped))

                    if any(no_matches):
                        if save_output:
                            with open(
                                self.__get_output_file_name(
                                    source, min_rows, max_rows, "no-matches"
                                ),
                                "w",
                                encoding="utf-8",
                            ) as file:
                                file.write(jsonpickle.encode(no_matches))

                    processed.append(task)
                    tasks.remove(task)

                    if result_set.offset + result_set.batch_size < total_rows:
                        tasks.append(
                            asyncio.create_task(
                                self.__get_matches_for_source(
                                    source,
                                    result_set.offset + result_set.batch_size,
                                    result_set.batch_size,
                                ),
                                name=source.name,
                            )
                        )
                    else:
                        del self.__running_clients[source]

    def __report_missing_playtime_and_scores(
        self, results: Dict[str, GameMatch], game_results: Dict[str, ExcelGame]
    ):
        for game_id, _match in results.items():
            if (
                game_results[game_id].release_date is not None
                and not game_results[game_id].completed
                and isinstance(_match.match_info, clients.HltbResult)
                and _match.match_info.playtime_main_seconds > 0
            ):
                playtime_min = _match.match_info.playtime_main_seconds // 60

                if playtime_min > 60:
                    rem = playtime_min % 60
                    playtime_min -= rem
                    playtime_min += 30 * round(rem / 30)

                playtime_str = LoggingDecorator.as_color(
                    (
                        f"{playtime_min} min"
                        if playtime_min < 60
                        else f"{playtime_min / 60:.1f} hr"
                    ),
                    LoggingColor.GREEN,
                )

                game = game_results[game_id]

                get_difference = lambda x: abs(game.estimated_playtime - (x / 60)) / (
                    (game.estimated_playtime + (x / 60)) / 2
                )

                if (
                    game.estimated_playtime is None
                    or get_difference(playtime_min) > 0.15
                ):
                    estimated_str = LoggingDecorator.as_color(
                        (
                            f"{int((game.estimated_playtime or 0) * 60)} min"
                            if (game.estimated_playtime or 0) < 1
                            else f"{game.estimated_playtime:.1f} hr"
                        ),
                        LoggingColor.RED,
                    )

                    print(
                        f"Playtime mismatch for {game.full_name}. Sheet: {estimated_str}, HLTB: {playtime_str}"
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


if __name__ == "__main__":
    # Which parsers should run, empty list means all parsers
    which_parsers: Optional[List[DataSource]] = []

    # Which parsers should not run, empty list means no parsers will be excluded
    except_parsers: Optional[List[DataSource]] = [
        DataSource.GAME_FAQS,  # IP Bans easily, has to run on its own with VPN
        DataSource.STEAM,  # Currently broken
        DataSource.PRICE_CHARTING,  # Unsubscribed from premium API
        DataSource.ROM_HACKING,  # Site taken down
    ]

    parser = ExcelParser(
        set(which_parsers or list(DataSource)).difference(set(except_parsers or []))
    )

    # A DataFrame override to use instead of the entire Excel sheet, e.g. parser.games.sample(5)
    # for a random sample of 5 games. If None, then the entire sheet is used.
    g_override: Optional[pd.DataFrame] = None

    missing_ids = []

    asyncio.run(
        parser.match_games(
            games_override=g_override, offset=0, batch_size=1000, save_output=True
        )
    )
