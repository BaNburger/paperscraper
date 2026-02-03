#!/bin/bash
# Paper Scraper API Entrypoint Script
# Runs migrations before starting the application

set -e

echo "========================================"
echo "Paper Scraper API Starting..."
echo "========================================"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres} -q; do
    echo "  PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! redis-cli -h ${REDIS_HOST:-redis} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1; do
    echo "  Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete!"

# Execute the main command
echo "Starting application..."
exec "$@"
