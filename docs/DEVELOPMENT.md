# Development Guide

Panduan untuk menjalankan aplikasi secara lokal tanpa Docker untuk keperluan development.

## Prerequisites

- Python 3.10+ (sudah terinstall)
- Redis (sudah terinstall via Homebrew)
- YouTube API Key

## Quick Start Development

### 1. Setup Environment (Pertama Kali)

```bash
# Setup virtual environment dan install dependencies
make dev-setup
```

Perintah ini akan:
- Membuat virtual environment di folder `venv/`
- Install semua dependencies dari `requirements.txt`
- Memberikan instruksi langkah selanjutnya

### 2. Configure API Key

```bash
# Copy .env.example ke .env (jika belum ada)
cp .env.example .env

# Edit .env dan tambahkan YouTube API Key
nano .env
```

Set `YOUTUBE_API_KEY` dengan API key Anda:
```bash
YOUTUBE_API_KEY=your_actual_api_key_here
```

### 3. Start Development Server

```bash
# Start Redis + Application (auto-reload enabled)
make dev-start
```

Aplikasi akan berjalan di: http://localhost:8000

Perintah ini akan:
- Check/create .env file
- Start Redis jika belum running
- Start aplikasi dengan hot-reload (auto-restart saat code berubah)

### 4. Access the Application

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Available Development Commands

```bash
# Setup & Start
make dev-setup      # Setup environment (first time only)
make dev-start      # Start Redis + Application
make dev-redis      # Start Redis only
make dev-stop       # Stop all local services

# Manual Control
make run-local      # Run app only (requires Redis running)

# Testing & Quality
make test           # Run tests
make lint           # Run linters
make format         # Format code

# Monitoring
make health         # Check service health
make metrics        # View metrics
make dev-logs       # View logs (if running in background)
```

## Development Workflow

### Typical Daily Workflow

```bash
# 1. Start development
make dev-start

# 2. Code, test, repeat...
# File changes will auto-reload the server

# 3. When done
make dev-stop
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
make test

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Or manually
source venv/bin/activate
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

## Manual Setup (Alternative)

Jika tidak ingin menggunakan Makefile:

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Setup Environment

```bash
cp .env.example .env
# Edit .env dan tambahkan YOUTUBE_API_KEY
```

### 4. Start Redis

```bash
# Start Redis as daemon
redis-server --daemonize yes --port 6379

# Or run in foreground
redis-server
```

### 5. Run Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Set Redis URL
export REDIS_URL=redis://localhost:6379/0

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Environment Variables for Development

Edit `.env` file:

```bash
# Required
YOUTUBE_API_KEY=your_api_key_here

# Optional (defaults shown)
DEFAULT_COUNTRY=ID
DEFAULT_CATEGORIES=music,news,tech,entertainment,gaming
TREND_LIMIT=10
SCHEDULER_CRON=0 0 * * *
SCHEDULER_ENABLED=true

# Local Redis
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# Logging
LOG_LEVEL=DEBUG  # Use DEBUG for development
```

## Hot Reload

Uvicorn dengan flag `--reload` akan otomatis restart server saat file Python berubah.

**Perubahan yang trigger reload:**
- Edit file `.py` di folder `app/`
- Tambah/hapus file Python
- Edit `models.py`, `routes/`, dll

**Tidak trigger reload:**
- Edit file `.env` (harus restart manual)
- Edit `requirements.txt`

## Debugging

### Using Print Statements

```python
# In your code
print(f"Debug: video_id = {video_id}")
```

Output akan muncul di terminal.

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or with ipdb (install: pip install ipdb)
import ipdb; ipdb.set_trace()
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
      ],
      "jinja": true,
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

## Testing API Endpoints

### Using curl

```bash
# Trending videos
curl "http://localhost:8000/trending?country=ID&limit=5"

# Health check
curl "http://localhost:8000/health"

# With jq for pretty output
curl -s "http://localhost:8000/trending?country=ID" | jq .
```

### Using HTTPie

```bash
# Install
pip install httpie

# Use
http GET http://localhost:8000/trending country==ID limit==5
```

### Using Swagger UI

Open browser: http://localhost:8000/docs

- Interactive testing
- Try out endpoints
- View request/response models

## Common Issues

### Port 8000 Already in Use

```bash
# Find process using port 8000
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)

# Or use different port
uvicorn app.main:app --port 8001 --reload
```

### Redis Connection Failed

```bash
# Check if Redis is running
pgrep redis-server

# Start Redis
make dev-redis

# Or manually
redis-server --daemonize yes
```

### Missing Dependencies

```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### YouTube API Key Not Working

```bash
# Check .env file
cat .env | grep YOUTUBE_API_KEY

# Make sure no quotes around the key
# ❌ Wrong: YOUTUBE_API_KEY="AIza..."
# ✅ Correct: YOUTUBE_API_KEY=AIza...
```

## Performance Tips

1. **Use Redis**: Significant performance boost with caching
2. **Adjust LOG_LEVEL**: Use `INFO` or `WARNING` in development to reduce noise
3. **Disable Scheduler**: Set `SCHEDULER_ENABLED=false` if not testing scheduled tasks
4. **Limit Results**: Use small `limit` values during testing

## Project Structure Reference

```
youtube-trennding-fetcher/
├── venv/                    # Virtual environment (gitignored)
├── app/
│   ├── main.py             # Entry point
│   ├── config.py           # Settings
│   ├── models.py           # Data models
│   ├── youtube_client.py   # YouTube API
│   ├── fetcher.py          # Business logic
│   ├── scheduler.py        # APScheduler
│   ├── routes/             # API endpoints
│   └── utils/              # Utilities
├── tests/                  # Test suite
├── .env                    # Your config (gitignored)
├── .env.example            # Config template
└── Makefile               # Development commands
```

## Next Steps

- Read [README.md](README.md) for complete documentation
- Check [QUICKSTART.md](QUICKSTART.md) for quick setup
- Explore `/docs` for interactive API testing
- Run tests with `make test`

## Support

Untuk issues atau questions:
- Check logs di terminal
- Lihat `/health` endpoint
- Review error messages di console
