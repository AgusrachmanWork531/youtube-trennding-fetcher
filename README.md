# YouTube Trending Fetcher

A production-ready Python microservice that automatically fetches trending YouTube videos daily, with support for filtering by country, category, keywords, and channels. Built with FastAPI, Redis caching, and Docker.

## Features

- Fetch top trending YouTube videos by country and category
- Search videos by keywords and channels
- Redis-based caching to reduce API calls and handle rate limits
- Automatic daily fetching with configurable scheduler (APScheduler)
- REST API with FastAPI and auto-generated documentation
- Exponential backoff retry logic for API resilience
- Structured JSON logging for observability
- Health checks and metrics endpoints
- Docker and docker-compose for easy deployment
- Comprehensive unit and integration tests
- Jenkins CI/CD pipeline ready

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Jenkins CI/CD](#jenkins-cicd)
- [Architecture](#architecture)
- [Contributing](#contributing)

## Documentation

- **Quick Start Guide**: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- **Development Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Jenkins CI/CD Setup**: [docs/JENKINS_SETUP.md](docs/JENKINS_SETUP.md)
- **Jenkins Quick Reference**: [docs/JENKINS_QUICKREF.md](docs/JENKINS_QUICKREF.md)
- **Security Notes**: [docs/SECURITY_NOTES.md](docs/SECURITY_NOTES.md)
- **Project Summary**: [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)

## Quick Start

### 1. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**
4. Create credentials (API Key)
5. Copy your API key

### 2. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd youtube-trennding-fetcher

# Copy environment template
cp .env.example .env

# Edit .env and add your YouTube API key
nano .env  # or use your preferred editor
```

### 3. Run with Docker (Recommended)

```bash
# Build and start services
make build
make up

# Or using docker-compose directly
docker-compose up --build -d
```

### 4. Access the API

- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Prerequisites

- **Docker & Docker Compose** (recommended) OR
- **Python 3.10+** (for local development)
- **YouTube Data API v3 Key** (required)
- **Redis** (optional, but highly recommended)

## Installation

### Option 1: Docker (Recommended)

```bash
# Build and run
make build
make up

# View logs
make logs
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install

# Or manually
pip install -r requirements.txt

# Run Redis (required for caching)
docker run -d -p 6379:6379 redis:7-alpine

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

All configuration is done via environment variables. Copy `.env.example` to `.env` and customize:

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `YOUTUBE_API_KEY` | Your YouTube Data API v3 key | `AIza...` |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_COUNTRY` | ISO 3166-1 alpha-2 country code | `ID` |
| `DEFAULT_CATEGORIES` | Comma-separated category list | `music,news,tech,entertainment,gaming` |
| `TREND_LIMIT` | Max videos to fetch per request | `10` |
| `SCHEDULER_CRON` | Cron expression for auto-fetch | `0 0 * * *` (daily at midnight) |
| `SCHEDULER_ENABLED` | Enable/disable scheduler | `true` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `REDIS_ENABLED` | Enable/disable caching | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Cron Expression Examples

```bash
# Daily at midnight
SCHEDULER_CRON="0 0 * * *"

# Every 6 hours
SCHEDULER_CRON="0 */6 * * *"

# Twice daily (midnight and noon)
SCHEDULER_CRON="0 0,12 * * *"

# Every weekday at 9 AM
SCHEDULER_CRON="0 9 * * 1-5"
```

## Usage

### Fetch Trending Videos

```bash
# Get top 10 trending videos in Indonesia
curl "http://localhost:8000/trending?country=ID&limit=10"

# Get trending music videos
curl "http://localhost:8000/trending?country=US&category=music&limit=10"

# Search for specific keyword
curl "http://localhost:8000/trending?keyword=lofi&limit=20"

# Get videos from specific channel
curl "http://localhost:8000/trending?channelId=UCxxxxxxxxxxxxx"

# Combined filters
curl "http://localhost:8000/trending?country=ID&category=tech&keyword=AI&limit=15"

# Filter by date
curl "http://localhost:8000/trending?date=2025-11-12&country=ID"
```

### Health Check

```bash
# Check service health
curl http://localhost:8000/health | python -m json.tool

# Using Make
make health
```

### View Metrics

```bash
# Get application metrics
curl http://localhost:8000/metrics | python -m json.tool

# Using Make
make metrics
```

## API Endpoints

### `GET /trending`

Fetch trending YouTube videos with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `country` | string | No | ISO 3166-1 alpha-2 country code (default: `ID`) |
| `category` | string | No | Category name or ID (e.g., `music`, `10`) |
| `keyword` | string | No | Search keyword to filter videos |
| `channelId` | string | No | YouTube channel ID |
| `limit` | integer | No | Max results (1-50, default: 10) |
| `date` | string | No | Date filter in YYYY-MM-DD format |

**Response Example:**

```json
{
  "meta": {
    "total": 10,
    "limit": 10,
    "page": 1,
    "fetchedAt": "2025-11-12T10:00:00Z",
    "fromCache": false
  },
  "data": [
    {
      "videoId": "abc123",
      "title": "Amazing Video Title",
      "description": "Video description...",
      "viewCount": 1234567,
      "publishedAt": "2025-11-10T12:34:56Z",
      "channelTitle": "Channel Name",
      "channelId": "UCxxxxxxx",
      "videoLink": "https://www.youtube.com/watch?v=abc123",
      "thumbnailUrl": "https://i.ytimg.com/vi/abc123/default.jpg",
      "categoryId": "10",
      "tags": ["music", "lofi"]
    }
  ]
}
```

### `GET /health`

Health check endpoint.

**Response Example:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:00:00Z",
  "redisConnected": true,
  "lastFetch": "2025-11-12T09:00:00Z",
  "youtubeApiStatus": "ok"
}
```

### `GET /metrics`

Application metrics endpoint.

**Response Example:**

```json
{
  "totalRequests": 156,
  "lastFetchTimestamp": "2025-11-12T09:00:00Z",
  "cacheHitRate": 0.7532,
  "uptimeSeconds": 86400.5
}
```

### `GET /`

Root endpoint with API information.

### `GET /docs`

Interactive API documentation (Swagger UI).

### `GET /redoc`

Alternative API documentation (ReDoc).

## Development

### Setup Development Environment

```bash
# Install dev dependencies
make dev-install

# Or manually
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test
```

### Project Structure

```
youtube-trennding-fetcher/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── youtube_client.py    # YouTube API client
│   ├── fetcher.py           # Fetching and caching logic
│   ├── scheduler.py         # Automatic scheduler
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── trending.py      # Trending endpoints
│   │   └── health.py        # Health & metrics endpoints
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # Structured logging
│       └── metrics.py       # Metrics collector
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_models.py       # Model tests
│   ├── test_fetcher.py      # Fetcher tests
│   └── test_routes.py       # API endpoint tests
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Docker Compose configuration
├── Makefile                 # Developer commands
├── requirements.txt         # Python dependencies
├── pytest.ini               # Pytest configuration
├── .env.example             # Environment template
├── .gitignore
└── README.md
```

## Testing

### Run All Tests

```bash
make test
```

### Run Specific Tests

```bash
# Test models
pytest tests/test_models.py -v

# Test fetcher service
pytest tests/test_fetcher.py -v

# Test API routes
pytest tests/test_routes.py -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=html
```

### Test Coverage

After running tests with coverage, open `htmlcov/index.html` in your browser to view detailed coverage report.

## Docker Deployment

### Using Docker Compose (Production)

```bash
# Build images
make build

# Start services
make up

# Check logs
make logs

# Stop services
make down

# Restart services
make restart

# Full cleanup (including volumes)
make clean
```

### Manual Docker Commands

```bash
# Build
docker-compose build --no-cache

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Environment Variables in Docker

Set environment variables in `.env` file. The `docker-compose.yml` automatically loads them.

Example `.env`:

```bash
YOUTUBE_API_KEY=your_api_key_here
DEFAULT_COUNTRY=ID
SCHEDULER_CRON=0 0 * * *
LOG_LEVEL=INFO
```

## Jenkins CI/CD

This project includes a complete Jenkins pipeline for automated testing, building, and deployment.

### Quick Setup

1. **Setup Jenkins Credentials** (see [docs/JENKINS_SETUP.md](docs/JENKINS_SETUP.md)):
   - `github-credentials` - GitHub access
   - `docker-hub-credentials` - Docker Hub push
   - `vps-ssh-password` - VPS deployment
   - `youtube-api-key` - YouTube Data API v3

2. **Set Global Environment Variable:**
   - `VPS_HOST` = Your VPS IP address

3. **Create Pipeline Job:**
   - New Item → Pipeline
   - SCM: Git → Repository URL
   - Script Path: `Jenkinsfile`

### Pipeline Stages

The Jenkins pipeline automatically:

1. 🧹 **Clean Workspace** - Fresh start
2. 📦 **Pull SCM** - Clone from GitHub
3. 🔐 **Docker Login** - Authenticate to registry
4. 🔍 **Environment Check** - Verify tools & permissions
5. 🧪 **Run Tests** - Execute pytest suite
6. 🔨 **Docker Build** - Build optimized image
7. 🚀 **Push to Registry** - Upload to Docker Hub
8. 🎯 **Deploy to VPS** - Deploy with Redis
9. ✅ **Verify Deployment** - Health checks

### Deployment Result

After successful deployment:

- **Application**: `http://VPS_IP:8000`
- **API Docs**: `http://VPS_IP:8000/docs`
- **Health Check**: `http://VPS_IP:8000/health`
- **Metrics**: `http://VPS_IP:8000/metrics`

### Documentation

- **Full Setup Guide**: [docs/JENKINS_SETUP.md](docs/JENKINS_SETUP.md)
- **Quick Reference**: [docs/JENKINS_QUICKREF.md](docs/JENKINS_QUICKREF.md)
- **Security Guide**: [docs/SECURITY_NOTES.md](docs/SECURITY_NOTES.md)

### Features

- ✅ Automated testing
- ✅ Multi-stage Docker build
- ✅ Zero-downtime deployment
- ✅ Redis auto-configuration
- ✅ Health check verification
- ✅ Automatic cleanup
- ✅ Rollback support

## Architecture

### Components

1. **FastAPI Application** - REST API server with async support
2. **YouTube API Client** - Handles API requests with retry logic
3. **Fetcher Service** - Business logic and caching layer
4. **Redis Cache** - Stores trending videos (24-hour TTL)
5. **APScheduler** - Automatic daily fetching
6. **Metrics Collector** - Request and cache statistics

### Data Flow

```
User Request
    ↓
FastAPI Endpoint
    ↓
Fetcher Service
    ↓
Check Redis Cache ──→ Cache Hit ──→ Return Cached Data
    ↓ Cache Miss
YouTube API Client
    ↓
YouTube Data API v3
    ↓
Parse & Store in Cache
    ↓
Return Fresh Data
```

### Caching Strategy

- Cache key format: `trending:{country}:{category}:{date}`
- TTL: 24 hours
- Fallback: On API failure, serve stale cache
- Deduplication: By `videoId` + `date`

### Error Handling

- Exponential backoff on API failures (max 3 retries)
- Graceful degradation with cached data
- Structured error logging
- HTTP 500 on unrecoverable errors

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install production dependencies |
| `make dev-install` | Install dev dependencies |
| `make build` | Build Docker images |
| `make up` | Start services |
| `make down` | Stop services |
| `make restart` | Restart services |
| `make logs` | View application logs |
| `make test` | Run tests with coverage |
| `make lint` | Run linters (flake8, mypy) |
| `make format` | Format code (black, isort) |
| `make clean` | Clean up containers and cache |
| `make run-local` | Run locally without Docker |
| `make health` | Check service health |
| `make metrics` | View application metrics |

## Troubleshooting

### YouTube API Quota Exceeded

- **Symptom**: HTTP 429 or quota errors
- **Solution**:
  - Service automatically retries with exponential backoff
  - Falls back to cached data
  - Consider reducing `TREND_LIMIT` or fetch frequency

### Redis Connection Failed

- **Symptom**: `Redis connection check failed` in logs
- **Solution**:
  - Check Redis is running: `docker ps | grep redis`
  - Verify `REDIS_URL` in `.env`
  - Set `REDIS_ENABLED=false` to disable caching (not recommended)

### Missing API Key

- **Symptom**: `YOUTUBE_API_KEY environment variable is required`
- **Solution**: Set `YOUTUBE_API_KEY` in `.env` file

### Scheduler Not Running

- **Symptom**: No automatic fetches
- **Solution**:
  - Check `SCHEDULER_ENABLED=true` in `.env`
  - Verify cron expression is valid
  - Check logs for scheduler errors

## Best Practices

1. **API Key Security**: Never commit `.env` to version control
2. **Rate Limits**: Use caching to minimize API calls
3. **Monitoring**: Regularly check `/health` and `/metrics` endpoints
4. **Logging**: Use structured JSON logs for production
5. **Testing**: Run tests before deployment
6. **Backups**: Redis data is persisted in Docker volume

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with:**
- FastAPI
- Python 3.11
- Redis
- Docker
- YouTube Data API v3
