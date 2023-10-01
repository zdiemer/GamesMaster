import csv
import uuid
import sys
from datetime import datetime
import json
import argparse
import re

# Copy of our url_slug code.
def convert_to_url_slug(slug: str) -> str:
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return re.sub(r"[^0-9a-zA-Z\-]+", "", slug)

def parse_csv(in_filepath):
    games = []
    # games_by_slug = {}
    # companies_by_slug = {}
    # franchises_by_slug = {}
    with open(in_filepath, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')

        for x, row in enumerate(reader):
            # Header row.
            if x > 1000:
                break
            if x == 0:
                continue
            game = {}
            title_raw = row["Title"]

            title_norm = title_raw.lower()

            previously_written = False
            for i, g in enumerate(games):
                # Attempt to match.
                # TODO: fuzzy match.
                # games[i] = {"title": "bar"}

                if title_norm == g["title"].lower():
                    print(f"possible duplicate game: {title_raw} & {g['title']} from index: {i}")

                    # We may have additional data to write to this row.
                    games[i]["matches"] = g["matches"] + 1



                    previously_written = True
                    break

            game["title"] = title_raw
            game["matches"] = 1
            if not previously_written:
                games.append(game)
                continue
           

            # game_slug = convert_to_url_slug(title)
            # game["title"] = title
            # game["genres"] = [row["Genre"]]
            # # franchise
            # franchise_raw = row["Franchise"]
            # franchise_slug = convert_to_url_slug(franchise_raw)
            # if franchise_slug in franchises_by_slug:
            #     if franchises_by_slug[franchise_slug] != franchise_raw:
            #         print(f"\tslug {franchise_slug} seen already, using existing: {franchises_by_slug[franchise_slug]} which != {franchise_raw}")
            #     franchise_raw = franchises_by_slug[franchise_slug]
            # else:
            #     franchises_by_slug[franchise_slug] = franchise_raw
            # game["franchises"] = [franchise_raw]

            # # developer
            # dev = row["Developer"]
            # dev_slug = convert_to_url_slug(dev)
            # if dev_slug in companies_by_slug:
            #     if companies_by_slug[dev_slug] != dev:
            #         print(f"\tslug {dev_slug} seen already, using existing: {companies_by_slug[dev_slug]} which != {dev}")
            #     dev = companies_by_slug[dev_slug]
            # else:
            #     companies_by_slug[dev_slug] = dev

            # game["developers"] = [dev]

            # if game_slug in games_by_slug:
            #     print(f"duplicate game found with slug: {game_slug}")
            #     continue
            # games_by_slug[game_slug] = game

    return {
        "games": games,
    }


def write_json(out_filepath, in_dict):
    with open(out_filepath, mode="wt+", encoding="utf-8") as f:
        json_object = json.dumps(in_dict, indent=4)
        f.write(json_object)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='csv-converter')
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()
    if not bool(args.input) or not bool(args.output):
        sys.exit(1)

    out_data = parse_csv(args.input)
    write_json(args.output, out_data)
    sys.exit(1)