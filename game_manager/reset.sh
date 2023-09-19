echo "Destroying stack."
docker compose down -v

echo "Destroying migrations."
rm -f backend/migrations/000*py