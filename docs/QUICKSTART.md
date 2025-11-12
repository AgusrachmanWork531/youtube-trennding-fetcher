# Quick Start Guide

## 1. Get YouTube API Key (5 minutes)

1. Visit: https://console.cloud.google.com/
2. Create/select project
3. Enable "YouTube Data API v3"
4. Create API Key
5. Copy the key

## 2. Setup (2 minutes)

```bash
# Copy environment template
cp .env.example .env

# Edit and add your API key
nano .env
# Set: YOUTUBE_API_KEY=your_actual_api_key_here
```

## 3. Run (1 minute)

```bash
# Start everything with Docker
make build
make up
```

## 4. Test (1 minute)

```bash
# Open in browser
open http://localhost:8000/docs

# Or use curl
curl "http://localhost:8000/trending?country=ID&limit=5"
```

## Example API Calls

```bash
# Trending videos in Indonesia
curl "http://localhost:8000/trending?country=ID&limit=10"

# Music category
curl "http://localhost:8000/trending?category=music&limit=10"

# Search by keyword
curl "http://localhost:8000/trending?keyword=tutorial&limit=10"

# Multiple filters
curl "http://localhost:8000/trending?country=US&category=tech&keyword=AI"

# Health check
curl "http://localhost:8000/health"
```

## Useful Commands

```bash
# View logs
make logs

# Stop services
make down

# Run tests
make test

# Check health
make health
```

## Endpoints

- **API Docs**: http://localhost:8000/docs
- **Trending**: http://localhost:8000/trending
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## Troubleshooting

**Problem**: API key error
```bash
# Check .env file has YOUTUBE_API_KEY set
cat .env | grep YOUTUBE_API_KEY
```

**Problem**: Redis not connecting
```bash
# Check Redis is running
docker ps | grep redis

# Restart services
make restart
```

**Problem**: Port 8000 already in use
```bash
# Edit docker-compose.yml, change:
ports:
  - "8001:8000"  # Use 8001 instead
```

## Next Steps

1. Read full [README.md](README.md) for details
2. Customize [.env](.env) settings
3. Check [/docs](http://localhost:8000/docs) for interactive API testing
4. View scheduler logs to see automatic fetching
