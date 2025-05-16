#!/bin/bash
set -e

echo "Starting Chat X-Ray Bot with local Ollama..."

# Make sure Docker is running
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Neither docker-compose nor docker compose is available. Please install docker-compose."
    exit 1
fi

# Create necessary directories
mkdir -p uploads reports
chmod 777 uploads reports

echo "Building and starting services..."
$COMPOSE_CMD up --build -d

echo "Waiting for Ollama to pull the model..."
sleep 30

echo "Services are running!"
echo "App is available at: http://localhost:8000"
echo "Ollama API is available at: http://localhost:11434"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down" 