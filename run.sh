#!/bin/bash

# Chat X-Ray Bot startup script

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if poetry is installed
if ! command_exists poetry; then
    echo "Poetry is not installed. Installing..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your API keys and configuration"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Create required directories
mkdir -p uploads reports

# Run tests
echo "Running tests..."
poetry run pytest

# Start the bot
echo "Starting Chat X-Ray Bot..."
poetry run python -m app.bot 