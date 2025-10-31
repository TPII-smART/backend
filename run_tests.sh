#!/bin/bash
# Script to run tests with Docker Compose test databases

set -e

echo "Starting test databases..."
docker compose -f docker-compose-tests.yml up -d

echo "Waiting for databases to be ready..."
sleep 10

# Wait for PostgreSQL to be ready
until docker compose -f docker-compose-tests.yml exec -T postgres-test pg_isready -U postgres_test > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Wait for Redis to be ready
until docker compose -f docker-compose-tests.yml exec -T redis-test redis-cli ping > /dev/null 2>&1; do
  echo "Waiting for Redis..."
  sleep 2
done

echo "Databases are ready!"
echo "Running tests..."

# Run pytest with Poetry
poetry run pytest -v --tb=short

TEST_EXIT_CODE=$?

echo "Stopping test databases..."
docker compose -f docker-compose-tests.yml down

exit $TEST_EXIT_CODE
