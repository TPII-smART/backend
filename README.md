# Backend - FastAPI with Gemini API, Redis, and PostgreSQL

A FastAPI service that integrates with Google's Gemini API, using Redis and PostgreSQL for response caching to minimize API calls.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **Gemini API Integration**: Calls Google's Gemini AI API with custom prompts
- **Two-Tier Caching**: 
  - Redis for fast in-memory caching
  - PostgreSQL for persistent storage
- **Pydantic Models**: Type-safe request/response validation
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
  "hash": "unique_identifier",
  "expected": "expected_value_or_context",
  "response": "Gemini API response text",
  "cached": false
}
```

## Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized setup)
- Google Gemini API key

### Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

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

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start PostgreSQL and Redis (using Docker):
```bash
docker-compose up postgres redis -d
```

3. Run the application:
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
│   ├── main.py               # FastAPI application and endpoints
│   ├── models.py             # Pydantic models for request/response
│   ├── config.py             # Configuration and settings
│   ├── database.py           # PostgreSQL database setup
│   ├── redis_client.py       # Redis client wrapper
│   └── gemini_service.py     # Gemini API integration
├── docker-compose.yml        # Docker services configuration
├── Dockerfile                # Application container definition
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment variables
└── README.md                 # This file
```

## Customizing the Gemini Prompt

To customize the prompt sent to Gemini API, edit the `generate_response` method in `app/gemini_service.py`:

```python
prompt = f"""
Your custom prompt here...
Hash: {hash_value}
Expected: {expected_value}
"""
```

## Cache Behavior

1. **First Request**: Calls Gemini API, stores response in both Redis and PostgreSQL
2. **Subsequent Requests**: 
   - Checks Redis first (fast, in-memory)
   - Falls back to PostgreSQL if not in Redis
   - Only calls Gemini API if not found in either cache

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

## License

See LICENSE file for details.