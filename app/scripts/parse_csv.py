import csv
import uuid

games = []

with open('static/games.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    for row in reader:
        games.append({"game_id": str(uuid.uuid4()), "title": row["Title"]})

games.sort(key=lambda game: game["title"])

with open('db/03_parsed_data.sql', mode="wt") as f:
    for game in games:
        f.write('INSERT INTO games VALUES ("%s","%s");\n' % (game["game_id"], game["title"]))