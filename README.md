# Backend - FastAPI with Gemini API, Redis, and PostgreSQL

A FastAPI service that integrates with Google's Gemini API, using Redis and PostgreSQL for response caching to minimize API calls.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **Gemini API Integration**: Calls Google's Gemini AI API with custom prompts
- **Two-Tier Caching**: 
  - Redis for fast in-memory caching
  - PostgreSQL for persistent storage
- **Pydantic Models**: Type-safe request/response validation
- **CORS Support**: Configurable via environment variables for cross-origin requests
- **Swagger Documentation**: Auto-generated API documentation at `/docs`
- **Docker Support**: Easy deployment with Docker Compose

## API Endpoint

### POST /gemini

Calls the Gemini API with a custom prompt. Responses are cached to avoid overcalling the API.

**Request Body:**
```json
{
  "hash": "unique_identifier",
  "expected": "expected_value_or_context"
}
```

**Response:**
```json
{
  "badge": "TRUSTED",
  "details": "Detailed analysis from Gemini API"
}
```

**Response Fields:**
- `badge`: Trust classification, one of:
  - `TRUSTED`: The data is classified as trusted
  - `UNTRUSTED`: The data is classified as untrusted
  - `UNKNOWN`: Unable to determine trust level
- `details`: Detailed analysis and reasoning from Gemini API

## Setup

### Prerequisites

- Python 3.11+
- Poetry (for dependency management) or pip
- Docker and Docker Compose (for containerized setup)
- Google Gemini API key

### Installation

#### Quick Start with Makefile

```bash
# Install Poetry in a virtual environment
make install-poetry

# Install dependencies
make install

# Run development server
make dev

# Run tests
make test
```

#### Option 1: Using Poetry (Recommended)

1. Install Poetry if not already installed:
```bash
curl -sSL https://install.python-poetry.org | python3 -
# Or use Makefile: make install-poetry
```

2. Install dependencies:
```bash
poetry install
# Or use Makefile: make install
```

3. Activate the virtual environment:
```bash
poetry shell
```

#### Option 2: Using pip

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Makefile Commands

The project includes a Makefile for common tasks:

```bash
make help            # Show available commands
make install-poetry  # Install Poetry in a virtual environment
make install         # Install dependencies with Poetry
make dev             # Run development server with hot reload
make run             # Run production server
make test            # Run tests with test databases
make lint            # Run linters (ruff, black)
make format          # Format code with black and isort
make docker-up       # Start Docker services
make docker-down     # Stop Docker services
make clean           # Clean up generated files
make build           # Build project with Poetry
```

### Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and configure the application:
```env
# Required: Add your Gemini API key
GEMINI_API_KEY=your_actual_api_key_here

# Optional: Configure CORS (default allows all origins)
CORS_ENABLED=true
CORS_ORIGINS=*
CORS_CREDENTIALS=true
CORS_METHODS=*
CORS_HEADERS=*

# Optional: Configure Database Connection Pool
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
```

**CORS Configuration Options:**
- `CORS_ENABLED`: Enable/disable CORS (true/false)
- `CORS_ORIGINS`: Allowed origins. Use `*` for all, or comma-separated list: `http://localhost:3000,https://example.com`
- `CORS_CREDENTIALS`: Allow credentials (true/false)
- `CORS_METHODS`: Allowed HTTP methods. Use `*` for all, or comma-separated list: `GET,POST,PUT`
- `CORS_HEADERS`: Allowed headers. Use `*` for all, or comma-separated list

**Database Pool Configuration Options:**
- `DB_POOL_SIZE`: Number of connections to maintain in the pool (default: 5)
- `DB_MAX_OVERFLOW`: Maximum number of connections that can be created beyond pool_size (default: 10)
- `DB_POOL_TIMEOUT`: Seconds to wait before giving up on getting a connection from the pool (default: 30)
- `DB_POOL_RECYCLE`: Seconds after which a connection is automatically recycled (default: 3600)
- `DB_POOL_PRE_PING`: Enable connection health checks before using (default: true)

### Option 1: Docker Compose (Recommended)

Start all services (API, PostgreSQL, Redis):
```bash
docker-compose up -d
```

The API will be available at http://localhost:8000

View logs:
```bash
docker-compose logs -f api
```

Stop services:
```bash
docker-compose down
```

### Option 2: Local Development

1. Start PostgreSQL and Redis (using Docker):
```bash
docker-compose up postgres redis -d
```

2. Run the application:

**Using Poetry:**
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Or use the Poetry script
poetry run dev
```

**Using pip/venv:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py           # Package marker
│   ├── main.py               # FastAPI application setup
│   ├── controllers.py        # API endpoint controllers
│   ├── models.py             # Pydantic models for request/response
│   ├── config.py             # Configuration and settings
│   ├── database.py           # PostgreSQL database setup
│   ├── redis_client.py       # Redis client wrapper
│   └── gemini_service.py     # Gemini API integration
├── tests/                    # Test suite
│   ├── conftest.py           # Test fixtures
│   ├── test_controllers.py   # API endpoint tests
│   ├── test_database.py      # Database tests
│   └── test_models.py        # Model validation tests
├── docker-compose.yml        # Docker services configuration
├── docker-compose-tests.yml  # Test databases configuration
├── Dockerfile                # Application container definition
├── pyproject.toml            # Poetry configuration and dependencies
├── requirements.txt          # Python dependencies (pip)
├── pytest.ini                # Pytest configuration
├── .env.example              # Example environment variables
└── README.md                 # This file
```

## Customizing the Gemini Prompt

The Gemini API is configured to perform security analysis and classify data as TRUSTED, UNTRUSTED, or UNKNOWN.

To customize the prompt sent to Gemini API, edit the `generate_response` method in `app/gemini_service.py`:

```python
prompt = f"""
Your custom security analysis prompt here...
Hash: {hash_value}
Expected: {expected_value}

Format your response as:
CLASSIFICATION: [TRUSTED/UNTRUSTED/UNKNOWN]
DETAILS: [Your detailed analysis]
"""
```

## Cache Behavior

1. **First Request**: Calls Gemini API, stores badge and details in both Redis and PostgreSQL
2. **Subsequent Requests**: 
   - Checks Redis first (fast, in-memory)
   - Falls back to PostgreSQL if not in Redis
   - Only calls Gemini API if not found in either cache
3. **Cached responses** return the same badge and details as the original API call

## Testing the API

Using curl:
```bash
curl -X POST http://localhost:8000/gemini \
  -H "Content-Type: application/json" \
  -d '{"hash": "test123", "expected": "test value"}'
```

Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/gemini",
    json={"hash": "test123", "expected": "test value"}
)
print(response.json())
```

## Running Tests

The project includes comprehensive tests with mocked Gemini API responses and real test databases.

### Prerequisites

Install test dependencies:

**Using Poetry:**
```bash
poetry install --with dev
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### Running Tests with Test Databases

Use the provided script that manages test databases:
```bash
./run_tests.sh
```

Or manually:

1. Start test databases:
```bash
docker compose -f docker-compose-tests.yml up -d
```

2. Run tests:

**Using Poetry:**
```bash
poetry run pytest -v
```

**Using pip/venv:**
```bash
pytest -v
```

3. Stop test databases:
```bash
docker compose -f docker-compose-tests.yml down
```

### Test Structure

```
tests/
├── conftest.py          # Test fixtures and configuration
├── test_controllers.py  # API endpoint tests with mocked Gemini
├── test_database.py     # Database operations tests
└── test_models.py       # Pydantic model validation tests
```

**Key Features:**
- **Mocked Gemini API**: Tests don't call the real Gemini API
- **Real Databases**: Uses PostgreSQL and Redis test instances via Docker
- **Isolated Tests**: Each test gets a fresh database session
- **Comprehensive Coverage**: Tests for all endpoints, models, and database operations

### Test Databases

The test suite uses separate database instances:
- **PostgreSQL**: Port 5433 (vs 5432 for dev)
- **Redis**: Port 6380 (vs 6379 for dev)

Configuration is in `docker-compose-tests.yml`.

## License

See LICENSE file for details.