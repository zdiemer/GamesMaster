#!/bin/bash

GAMES_CSV_FILEPATH="static/games.csv"
PARSED_OUTPUT_FILEPATH="game_manager/scripts_data/parsed_games.json"

python convert_csv_to_json.py --input $GAMES_CSV_FILEPATH --output $PARSED_OUTPUT_FILEPATH
if [[ $? != 0 ]]; then
  echo "our parsing program has crashed"
  exit 1
fi

echo "parsing success, file created"

docker compose up -d

echo "starting stack"
until [ "`docker inspect -f {{.State.Health.Status}} games-master-backend-1`" = "healthy" ]
do  
    echo "Web not healthy yet."
    sleep 1;
done;

echo "stack started"

echo "making migrations"
docker compose exec backend python manage.py makemigrations

echo "applying migrations"
docker compose exec backend python manage.py migrate

echo "initializing minio"
docker compose exec backend python manage.py runscript initialize_minio --dir-policy root

echo "initializing test data"
docker compose exec backend python manage.py runscript test_data

echo "creating default superuser"
docker compose exec backend python manage.py runscript create_superuser

echo "removing parsed output file"
rm $PARSED_OUTPUT_FILEPATH
