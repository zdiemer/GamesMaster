echo "Destroying stack."
docker compose down -v

echo "Destroying migrations."
rm -f game_manager/backend/migrations/000*py