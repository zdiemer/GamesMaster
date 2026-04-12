import os
from typing import Dict, List, Optional, Set

import jsonpickle

from game_match import DataSource, GameMatch, GameMatchResult


def merge_matches(source: Optional[DataSource] = None):
    source_folder = f"output\\{source.name.lower()}" if source is not None else None

    source_to_matches: Dict[
        str, Dict[str, Dict[str, GameMatch] | List[GameMatchResult] | List[str]]
    ] = {}

    for root, _, files in os.walk("output"):
        for file in files:
            if source is not None and root != source_folder:
                continue
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                if file.startswith("matches-"):
                    if root not in source_to_matches:
                        source_to_matches[root] = {
                            "matches": jsonpickle.decode(f.read())
                        }
                    elif "matches" not in source_to_matches[root]:
                        source_to_matches[root]["matches"] = jsonpickle.decode(f.read())
                    else:
                        source_to_matches[root]["matches"].update(
                            jsonpickle.decode(f.read())
                        )
                elif file.startswith("errors-"):
                    if root not in source_to_matches:
                        source_to_matches[root] = {
                            "errors": jsonpickle.decode(f.read())
                        }
                    elif "errors" not in source_to_matches[root]:
                        source_to_matches[root]["errors"] = jsonpickle.decode(f.read())
                    else:
                        source_to_matches[root]["errors"].extend(
                            jsonpickle.decode(f.read())
                        )
                elif file.startswith("skipped-"):
                    output: List[GameMatchResult] = jsonpickle.decode(f.read())
                    hash_ids = [gmr.game.hash_id for gmr in output]

                    if root not in source_to_matches:
                        source_to_matches[root] = {"skipped": hash_ids}
                    elif "skipped" not in source_to_matches[root]:
                        source_to_matches[root]["skipped"] = hash_ids
                    else:
                        source_to_matches[root]["skipped"].extend(hash_ids)
                elif file.startswith("no-matches-"):
                    output: List[GameMatchResult] = jsonpickle.decode(f.read())
                    hash_ids = [gmr.game.hash_id for gmr in output]

                    if root not in source_to_matches:
                        source_to_matches[root] = {"no-matches": hash_ids}
                    elif "no-matches" not in source_to_matches[root]:
                        source_to_matches[root]["no-matches"] = hash_ids
                    else:
                        source_to_matches[root]["no-matches"].extend(hash_ids)

    for root, outputs in source_to_matches.items():
        for output_type, output in outputs.items():
            with open(
                os.path.join(root, f"{output_type}.json"), "w", encoding="utf-8"
            ) as f:
                f.write(jsonpickle.encode(output))

    assert validate_matches(source)


def validate_matches(source: Optional[DataSource] = None) -> bool:
    source_folder = f"output\\{source.name.lower()}" if source is not None else None

    source_to_hash_ids: Dict[DataSource, Dict[str, Set[str]]] = {}

    for root, _, files in os.walk("output"):
        for file in files:
            if source is not None and root != source_folder:
                continue

            try:
                cur_source = DataSource[root.replace("output\\", "").upper()]
            except KeyError:
                continue

            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                if file.startswith("matches-"):
                    match_output: Dict[str, GameMatch] = jsonpickle.decode(f.read())

                    if cur_source not in source_to_hash_ids:
                        source_to_hash_ids[cur_source] = {
                            "matches": set(match_output.keys())
                        }
                    elif "matches" not in source_to_hash_ids[cur_source]:
                        source_to_hash_ids[cur_source]["matches"] = set(
                            match_output.keys()
                        )
                    else:
                        source_to_hash_ids[cur_source]["matches"] = source_to_hash_ids[
                            cur_source
                        ]["matches"].union(set(match_output.keys()))
                elif file.startswith("errors-"):
                    output: List[GameMatchResult] = jsonpickle.decode(f.read())
                    hash_ids = set(gmr.game.hash_id for gmr in output)

                    if cur_source not in source_to_hash_ids:
                        source_to_hash_ids[cur_source] = {"errors": hash_ids}
                    elif "errors" not in source_to_hash_ids[cur_source]:
                        source_to_hash_ids[cur_source]["errors"] = hash_ids
                    else:
                        source_to_hash_ids[cur_source]["errors"] = source_to_hash_ids[
                            cur_source
                        ]["errors"].union(hash_ids)
                elif file.startswith("skipped-"):
                    output: List[GameMatchResult] = jsonpickle.decode(f.read())
                    hash_ids = set(gmr.game.hash_id for gmr in output)

                    if cur_source not in source_to_hash_ids:
                        source_to_hash_ids[cur_source] = {"skipped": hash_ids}
                    elif "skipped" not in source_to_hash_ids[cur_source]:
                        source_to_hash_ids[cur_source]["skipped"] = hash_ids
                    else:
                        source_to_hash_ids[cur_source]["skipped"] = source_to_hash_ids[
                            cur_source
                        ]["skipped"].union(hash_ids)
                elif file.startswith("no-matches-"):
                    output: List[GameMatchResult] = jsonpickle.decode(f.read())
                    hash_ids = set(gmr.game.hash_id for gmr in output)

                    if cur_source not in source_to_hash_ids:
                        source_to_hash_ids[cur_source] = {"no-matches": hash_ids}
                    elif "no-matches" not in source_to_hash_ids[cur_source]:
                        source_to_hash_ids[cur_source]["no-matches"] = hash_ids
                    else:
                        source_to_hash_ids[cur_source]["no-matches"] = (
                            source_to_hash_ids[cur_source]["no-matches"].union(hash_ids)
                        )

    for dsource, outputs in source_to_hash_ids.items():
        for output_type, hashes in outputs.items():
            with open(
                os.path.join(f"output\\{dsource.name.lower()}", f"{output_type}.json"),
                "r",
                encoding="utf-8",
            ) as f:
                if output_type == "matches":
                    match_output: Dict[str, GameMatch] = jsonpickle.decode(f.read())
                    hash_ids = set(match_output.keys())
                elif output_type == "errors":
                    error_output: List[GameMatchResult] = jsonpickle.decode(f.read())
                    hash_ids = set(gmr.game.hash_id for gmr in error_output)
                else:
                    output: List[str] = jsonpickle.decode(f.read())
                    hash_ids = set(output)

                if any(hashes.difference(hash_ids)):
                    print(
                        f"Found mismatch for output type {output_type} and source {dsource}"
                    )
                    return False

    return True
