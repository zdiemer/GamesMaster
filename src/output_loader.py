import datetime
import math
import os
from enum import Enum
from typing import Dict, List, Optional, Set

import jsonpickle

from excel_loader import ExcelLoader
from game_match import DataSource, GameMatch, GameMatchResult


class OutputType(Enum):
    MATCH = "matches"
    ERROR = "errors"
    SKIPPED = "skipped"
    NO_MATCH = "no-matches"
    MANUAL = "manual"


class OutputLoader:
    @staticmethod
    def get_source_folder(source: DataSource) -> str:
        source_name = source.name.lower()
        return os.path.join("output", source_name)

    @staticmethod
    def get_output_file_name(
        min_rows: int, max_rows: int, output_type: OutputType
    ) -> str:
        datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{output_type.value}-{min_rows}-{max_rows}_{datetime_str}.json"

    @staticmethod
    def get_output_file_path(
        source: DataSource, min_rows: int, max_rows: int, output_type: OutputType
    ) -> str:
        source_folder = OutputLoader.get_source_folder(source)

        if not os.path.isdir(source_folder):
            os.mkdir(source_folder)

        file_name = OutputLoader.get_output_file_name(min_rows, max_rows, output_type)

        return os.path.join(source_folder, file_name)

    @staticmethod
    def write_output(
        source: DataSource,
        min_rows: int,
        max_rows: int,
        output_type: OutputType,
        data: List[GameMatchResult] | Dict[str, GameMatch],
    ) -> str:
        file_path = OutputLoader.get_output_file_path(
            source, min_rows, max_rows, output_type
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(jsonpickle.encode(data))

        return file_path

    @staticmethod
    def write_output_batched(
        source: DataSource,
        output_type: OutputType,
        data: List[GameMatchResult] | Dict[str, GameMatch],
        batch_size: int = 1000,
    ):
        created_file_paths = []

        if output_type == OutputType.MATCH:
            data_items = list(data.items())
            for i in range(0, len(data_items), batch_size):
                batch_max = min(i + batch_size - 1, len(data_items) - 1)
                created_file_paths.append(
                    OutputLoader.write_output(
                        source,
                        i,
                        batch_max,
                        output_type,
                        dict(data_items[i : i + batch_size]),
                    )
                )
        else:
            for i in range(0, len(data), batch_size):
                batch_max = min(i + batch_size - 1, len(data) - 1)
                created_file_paths.append(
                    OutputLoader.write_output(
                        source,
                        i,
                        batch_max,
                        output_type,
                        data[i : i + batch_size],
                    )
                )

        if any(data) and not any(created_file_paths):
            raise RuntimeError(
                f"Failed to create output files for {output_type.value} with batch size {batch_size} (expected {math.ceil(len(data) / batch_size)} files)"
            )

        return created_file_paths

    @staticmethod
    def merge_output_by_type(
        source: DataSource, output_type: OutputType, batch_size: int = 1000
    ) -> None:
        print(f"Loading {output_type.value} output for source {source.name}")
        output = OutputLoader.get_output_by_type(source, output_type)
        print(f"Merging {output_type.value} output for source {source.name}")
        created_file_paths = OutputLoader.write_output_batched(
            source, output_type, output, batch_size
        )

        source_folder = OutputLoader.get_source_folder(source)

        print(f"Removing old {output_type.value} output for source {source.name}")
        for root, _, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if (
                    file.startswith(output_type.value)
                    and file_path not in created_file_paths
                ):
                    os.remove(file_path)

    @staticmethod
    def merge_output(source: DataSource) -> None:
        OutputLoader.merge_output_by_type(source, OutputType.MATCH)
        OutputLoader.merge_output_by_type(source, OutputType.ERROR)
        OutputLoader.merge_output_by_type(source, OutputType.NO_MATCH)

    @staticmethod
    def cleanup_output(
        source: DataSource, loader: Optional[ExcelLoader] = None
    ) -> None:
        print(f"Cleaning up output for source: {source.name}")
        OutputLoader.merge_output(source)
        loader = loader or ExcelLoader()
        sheet_hashes = set(g.hash_id for g in loader.games)

        print(f"De-duplicating output for: {source.name}")
        matches = OutputLoader.get_matches(source)
        errors = {e.game.hash_id: e for e in OutputLoader.get_errors(source)}
        no_matches = {nm.game.hash_id: nm for nm in OutputLoader.get_no_matches(source)}

        matches = {k: v for k, v in matches.items() if k in sheet_hashes}

        no_matches_output = [
            nm
            for nm_hash, nm in no_matches.items()
            if nm_hash in sheet_hashes and nm_hash not in matches
        ]

        errors_output = [
            e
            for e_hash, e in errors.items()
            if e_hash in sheet_hashes
            and e_hash not in matches
            and e_hash not in no_matches
        ]

        print(f"Writing cleaned up output for source: {source.name}")
        for root, _, files in os.walk(OutputLoader.get_source_folder(source)):
            for file in files:
                os.remove(os.path.join(root, file))

        OutputLoader.write_output_batched(source, OutputType.MATCH, matches)
        OutputLoader.write_output_batched(source, OutputType.ERROR, errors_output)
        OutputLoader.write_output_batched(
            source, OutputType.NO_MATCH, no_matches_output
        )

    @staticmethod
    def get_output_by_type(
        source: DataSource, output_type: OutputType
    ) -> List[GameMatchResult] | Dict[str, GameMatch]:
        if output_type == OutputType.MATCH:
            return OutputLoader.get_matches(source)
        if output_type == OutputType.ERROR:
            return OutputLoader.get_errors(source)
        if output_type == OutputType.SKIPPED:
            return OutputLoader.get_skipped(source)
        if output_type == OutputType.NO_MATCH:
            return OutputLoader.get_no_matches(source)

        raise NotImplementedError

    @staticmethod
    def get_matches(source: DataSource) -> Dict[str, GameMatch]:
        source_folder = OutputLoader.get_source_folder(source)

        if not os.path.exists(source_folder):
            return {}

        matches: Dict[str, GameMatch] = {}

        for root, _, files in list(os.walk(source_folder)):
            for file in sorted(files):
                if file.startswith(OutputType.MATCH.value):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        matches.update(jsonpickle.decode(f.read()))

        return matches

    @staticmethod
    def get_errors(source: DataSource) -> List[GameMatchResult]:
        return OutputLoader.__get_gmr_list(source, OutputType.ERROR)

    @staticmethod
    def get_skipped(source: DataSource) -> List[GameMatchResult]:
        return OutputLoader.__get_gmr_list(source, OutputType.SKIPPED)

    @staticmethod
    def get_no_matches(source: DataSource) -> List[GameMatchResult]:
        return OutputLoader.__get_gmr_list(source, OutputType.NO_MATCH)

    @staticmethod
    def __get_gmr_list(
        source: DataSource, output_type: OutputType
    ) -> List[GameMatchResult]:
        source_folder = OutputLoader.get_source_folder(source)

        if not os.path.exists(source_folder):
            return {}

        gmr_set: Set[GameMatchResult] = set()

        for root, _, files in os.walk(source_folder):
            for file in sorted(files):
                if file.startswith(output_type.value):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        gmr_set.update(set(jsonpickle.decode(f.read())))

        return list(gmr_set)

    @staticmethod
    def get_all_processed_hash_ids(
        source: DataSource,
        output_type: OutputType = OutputType.MATCH,
    ) -> Dict[str, GameMatchResult | GameMatch]:
        results: Dict[str, GameMatchResult | GameMatch] = {}
        source_folder = OutputLoader.get_source_folder(source)

        if not os.path.exists(source_folder):
            return results

        for root, _, files in os.walk(source_folder):
            for file in files:
                if file.startswith(f"{output_type.value}-"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        cache_results: List[GameMatchResult] | Dict[str, GameMatch] = (
                            jsonpickle.decode(f.read())
                        )

                        if output_type == OutputType.MATCH:
                            results.update(cache_results)
                        else:
                            results.update({e.game.hash_id: e for e in cache_results})

        return results
