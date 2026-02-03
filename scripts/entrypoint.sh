#!/bin/bash
# Paper Scraper API Entrypoint Script
# Runs migrations before starting the application

set -e

# Configuration
MAX_RETRIES=${MAX_RETRIES:-30}
RETRY_INTERVAL=${RETRY_INTERVAL:-2}

echo "========================================"
echo "Paper Scraper API Starting..."
echo "========================================"
echo "Environment: ${APP_ENV:-development}"
echo "Debug: ${DEBUG:-false}"
echo "========================================"

# Function to wait for a service with timeout
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local retries=0

    echo "Waiting for ${service_name}..."

    while ! eval "$check_command" > /dev/null 2>&1; do
        retries=$((retries + 1))
        if [ $retries -ge $MAX_RETRIES ]; then
            echo "ERROR: ${service_name} did not become available after ${MAX_RETRIES} attempts"
            exit 1
        fi
        echo "  ${service_name} is unavailable (attempt ${retries}/${MAX_RETRIES}) - sleeping ${RETRY_INTERVAL}s"
        sleep $RETRY_INTERVAL
    done

    echo "${service_name} is ready!"
}

# Wait for PostgreSQL to be ready
wait_for_service "PostgreSQL" "pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres} -q"

# Wait for Redis to be ready (optional - don't fail if not available)
echo "Checking Redis connection..."
if redis-cli -h ${REDIS_HOST:-redis} -p ${REDIS_PORT:-6379} ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} ping > /dev/null 2>&1; then
    echo "Redis is ready!"
else
    echo "WARNING: Redis is not available. Rate limiting and caching may not work."
    echo "Continuing without Redis..."
fi

# Run database migrations with error handling
echo "========================================"
echo "Running database migrations..."
echo "========================================"

if ! alembic upgrade head; then
    echo "========================================"
    echo "ERROR: Database migration failed!"
    echo "========================================"
    echo "Possible causes:"
    echo "  - Database schema conflicts"
    echo "  - Missing migration files"
    echo "  - Database connection issues"
    echo ""
    echo "To debug, try running:"
    echo "  alembic history --verbose"
    echo "  alembic current"
    echo "========================================"
    exit 1
fi

echo "========================================"
echo "Migrations complete!"
echo "========================================"

# Execute the main command
echo "Starting application..."
echo "Command: $@"
echo "========================================"
exec "$@"
