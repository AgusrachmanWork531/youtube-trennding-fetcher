.PHONY: help install dev-install build up down restart logs test lint format clean dev-setup dev-start dev-stop dev-redis dev-logs

# Default target
help:
	@echo "YouTube Trending Fetcher - Available Commands:"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start services with docker-compose"
	@echo "  make down         - Stop services"
	@echo "  make restart      - Restart services"
	@echo "  make logs         - View application logs"
	@echo ""
	@echo "Development Commands (without Docker):"
	@echo "  make dev-setup    - Setup development environment (venv + install deps)"
	@echo "  make dev-redis    - Start Redis for local development"
	@echo "  make dev-start    - Start application in development mode"
	@echo "  make dev-stop     - Stop Redis and application"
	@echo "  make dev-logs     - View application logs (local)"
	@echo "  make run-local    - Run app locally (manual, requires Redis running)"
	@echo ""
	@echo "Dependencies:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run code linters"
	@echo "  make format       - Format code with black and isort"
	@echo ""
	@echo "Utilities:"
	@echo "  make health       - Check service health"
	@echo "  make metrics      - View application metrics"
	@echo "  make clean        - Clean up containers, volumes, and cache"
	@echo ""

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies (includes test tools)
dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# Build Docker images
build:
	docker-compose build --no-cache

# Start services
up:
	docker-compose up -d
	@echo "Services started! API available at http://localhost:8000"
	@echo "View docs at http://localhost:8000/docs"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f app

# Run tests
test:
	pytest tests/ -v --cov=app --cov-report=term-missing

# Run linters
lint:
	@echo "Running flake8..."
	flake8 app/ tests/ --max-line-length=100 --exclude=__pycache__
	@echo "Running mypy..."
	mypy app/ --ignore-missing-imports

# Format code
format:
	@echo "Running black..."
	black app/ tests/ --line-length=100
	@echo "Running isort..."
	isort app/ tests/ --profile black

# Clean up
clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete!"

# ==================== Development Commands (No Docker) ====================

# Setup development environment
dev-setup:
	@echo "Setting up development environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Activating virtual environment and installing dependencies..."
	@bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
	@echo ""
	@echo "✅ Development environment setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and add your YOUTUBE_API_KEY"
	@echo "2. Run 'make dev-redis' to start Redis"
	@echo "3. Run 'make dev-start' to start the application"
	@echo ""

# Create .env from .env.example if not exists
dev-env:
	@if [ ! -f ".env" ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env and add your YOUTUBE_API_KEY"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Start Redis for local development
dev-redis:
	@echo "Starting Redis for local development..."
	@if pgrep -x redis-server > /dev/null; then \
		echo "✅ Redis is already running"; \
	else \
		redis-server --daemonize yes --port 6379; \
		echo "✅ Redis started on port 6379"; \
	fi

# Start application in development mode
dev-start: dev-env dev-redis
	@echo "Starting application in development mode..."
	@echo "Activating virtual environment..."
	@bash -c "source venv/bin/activate && \
		export REDIS_URL=redis://localhost:6379/0 && \
		uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Stop Redis and application
dev-stop:
	@echo "Stopping local development services..."
	@pkill -f "uvicorn app.main:app" || echo "Uvicorn not running"
	@pkill redis-server || echo "Redis not running"
	@echo "✅ Development services stopped"

# View application logs (for background process)
dev-logs:
	@echo "Viewing application logs..."
	@tail -f logs/app.log 2>/dev/null || echo "No log file found. Run in foreground or check console output."

# Run locally without Docker (requires Redis running separately)
run-local:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first."; \
		exit 1; \
	fi
	@bash -c "source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# ==================== Utility Commands ====================

# Check service health
health:
	@curl -s http://localhost:8000/health | python3 -m json.tool

# View metrics
metrics:
	@curl -s http://localhost:8000/metrics | python3 -m json.tool
