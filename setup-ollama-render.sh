#!/bin/bash
set -e

echo "Setting up Ollama on Render..."

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Make sure Ollama directory exists with proper permissions
mkdir -p /root/.ollama
chmod 755 /root/.ollama

# Start Ollama server
echo "Starting Ollama server..."
ollama serve &

# Wait for Ollama to start
echo "Waiting for Ollama server to initialize..."
sleep 10

# Pull the required model
echo "Pulling Llama3.2 model..."
ollama pull llama3.2

echo "Ollama setup complete!"
echo "Testing Ollama API..."

# Test the API
curl -s http://localhost:11434/api/version

echo ""
echo "Ollama is now running and ready to serve requests."

# Keep the server running
tail -f /dev/null 