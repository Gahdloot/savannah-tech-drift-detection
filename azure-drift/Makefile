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

docker-build:
	docker build -t azure-drift:latest .

docker-run:
	docker run -p 8000:8000 \
		-e AZURE_TENANT_ID=$(AZURE_TENANT_ID) \
		-e AZURE_CLIENT_ID=$(AZURE_CLIENT_ID) \
		-e AZURE_CLIENT_SECRET=$(AZURE_CLIENT_SECRET) \
		-e AZURE_SUBSCRIPTION_ID=$(AZURE_SUBSCRIPTION_ID) \
		azure-drift:latest 