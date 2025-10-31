.PHONY: help install install-poetry venv dev test test-watch clean build run docker-up docker-down docker-test lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  make install-poetry  - Install Poetry in a virtual environment"
	@echo "  make install         - Install project dependencies with Poetry"
	@echo "  make venv            - Create and activate virtual environment"
	@echo "  make dev             - Run development server with hot reload"
	@echo "  make run             - Run production server"
	@echo "  make test            - Run tests with Poetry"
	@echo "  make test-watch      - Run tests in watch mode"
	@echo "  make docker-up       - Start Docker services"
	@echo "  make docker-down     - Stop Docker services"
	@echo "  make docker-test     - Run tests with test databases"
	@echo "  make lint            - Run linters (ruff, black check)"
	@echo "  make format          - Format code with black and isort"
	@echo "  make clean           - Clean up generated files"
	@echo "  make build           - Build the project with Poetry"

# Install Poetry in a virtual environment
install-poetry:
	@echo "Creating virtual environment for Poetry..."
	python3 -m venv .venv
	@echo "Installing Poetry..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install poetry
	@echo "Poetry installed! Use '.venv/bin/poetry' or add to PATH"
	@echo "Or run: source .venv/bin/activate && poetry --version"

# Create virtual environment and install dependencies
install:
	@echo "Installing dependencies with Poetry..."
	poetry install --with dev
	@echo "Dependencies installed successfully!"

# Create and show virtual environment info
venv:
	@echo "Creating Poetry virtual environment..."
	poetry install
	@echo ""
	@echo "To activate the virtual environment, run:"
	@echo "  poetry shell"
	@echo ""
	@echo "Or prefix commands with 'poetry run', e.g.:"
	@echo "  poetry run python -m app.main"

# Run development server with hot reload
dev:
	@echo "Starting development server..."
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run production server
run:
	@echo "Starting production server..."
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run tests with Poetry
test:
	@echo "Running tests with Poetry..."
	docker compose -f docker-compose-tests.yml up -d
	@echo "Waiting for databases to be ready..."
	@sleep 10
	poetry run pytest -v --tb=short
	docker compose -f docker-compose-tests.yml down

# Run tests in watch mode
test-watch:
	@echo "Running tests in watch mode..."
	docker compose -f docker-compose-tests.yml up -d
	@echo "Waiting for databases to be ready..."
	@sleep 10
	poetry run pytest-watch
	docker compose -f docker-compose-tests.yml down

# Start Docker services (PostgreSQL, Redis)
docker-up:
	@echo "Starting Docker services..."
	docker compose up -d

# Stop Docker services
docker-down:
	@echo "Stopping Docker services..."
	docker compose down

# Run tests with Docker test databases
docker-test:
	@echo "Running tests with test databases..."
	./run_tests.sh

# Run linters
lint:
	@echo "Running linters..."
	poetry run ruff check app/ tests/
	poetry run black --check app/ tests/

# Format code
format:
	@echo "Formatting code..."
	poetry run black app/ tests/
	poetry run isort app/ tests/

# Build the project
build:
	@echo "Building project with Poetry..."
	poetry build

# Clean up generated files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf dist/ build/ .coverage htmlcov/
	@echo "Cleanup complete!"
