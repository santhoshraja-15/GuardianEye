.PHONY: help install test lint format up down clean build run-backend run-worker migrate

help:
	@echo "GuardianEye Build and Management Automation"
	@echo "  make install      - Install backend and AI dependencies"
	@echo "  make up           - Start infrastructure containers (PostgreSQL, Redis, MinIO)"
	@echo "  make down         - Stop infrastructure containers"
	@echo "  make test         - Run pytest test suite"
	@echo "  make lint         - Run ruff/flake8 code formatting check"
	@echo "  make format       - Auto-format Python code"
	@echo "  make run-backend  - Start FastAPI development server"
	@echo "  make run-worker   - Start Celery AI processing worker"
	@echo "  make migrate      - Run Alembic database migrations"
	@echo "  make clean        - Remove temporary Python caches and logs"

install:
	pip install -r backend/requirements.txt

up:
	docker compose up -d postgres redis minio

down:
	docker compose down

test:
	pytest tests/ -v --cov=backend --cov=ai

lint:
	ruff check backend/ ai/ tests/

format:
	ruff format backend/ ai/ tests/

run-backend:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	celery -A backend.workers.celery_app worker --loglevel=info

migrate:
	alembic -c backend/alembic.ini upgrade head

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
