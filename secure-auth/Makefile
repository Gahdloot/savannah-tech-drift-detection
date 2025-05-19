.PHONY: install test lint format clean run docker-build docker-run help

# Variables
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
ISORT := $(VENV)/bin/isort
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy

help:
	@echo "Available commands:"
	@echo "  make install    - Create virtual environment and install dependencies"
	@echo "  make test      - Run tests with coverage"
	@echo "  make lint      - Run linting checks"
	@echo "  make format    - Format code with black and isort"
	@echo "  make clean     - Remove virtual environment and cache files"
	@echo "  make run       - Run the application"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make migrate   - Run database migrations"
	@echo "  make seed      - Seed the database with initial data"

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

test:
	$(PYTEST) tests/ --cov=src --cov-report=term-missing

lint:
	$(FLAKE8) src/ tests/
	$(MYPY) src/ tests/

format:
	$(BLACK) src/ tests/
	$(ISORT) src/ tests/

clean:
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

run:
	$(PYTHON) -m src.main

migrate:
	$(PYTHON) -m src.database.migrations

seed:
	$(PYTHON) -m src.database.seed

docker-build:
	docker build -t secure-auth:latest .

docker-run:
	docker run -p 8000:8000 \
		-e DATABASE_URL=$(DATABASE_URL) \
		-e JWT_SECRET_KEY=$(JWT_SECRET_KEY) \
		-e REDIS_URL=$(REDIS_URL) \
		secure-auth:latest 