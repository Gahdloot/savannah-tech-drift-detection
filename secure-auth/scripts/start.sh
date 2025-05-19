#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check for required environment variables
required_vars=(
    "DATABASE_URL"
    "JWT_SECRET_KEY"
    "REDIS_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set"
        exit 1
    fi
done

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations
echo "Running database migrations..."
python -m src.database.migrations

# Seed the database if needed
if [ "$SEED_DATABASE" = "true" ]; then
    echo "Seeding database..."
    python -m src.database.seed
fi

# Run linting
echo "Running linting checks..."
flake8 src/ tests/
mypy src/ tests/

# Run tests
echo "Running tests..."
pytest tests/ --cov=src --cov-report=term-missing

# Start the application
echo "Starting Secure Authentication Service..."
python -m src.main 