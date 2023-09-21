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

echo "initializing test data"
docker compose exec backend python manage.py runscript test_data

echo "creating default superuser"
docker compose exec backend python manage.py runscript create_superuser
