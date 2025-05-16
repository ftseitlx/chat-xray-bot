#!/bin/bash
set -e

echo "Starting Ollama server to install models..."
ollama serve &
SERVER_PID=$!

echo "Waiting for Ollama to start..."
MAX_ATTEMPTS=30
for i in $(seq 1 $MAX_ATTEMPTS); do
  echo "Checking server (attempt $i/$MAX_ATTEMPTS)..."
  if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "Server is up!"
    break
  fi
  
  if [ $i -eq $MAX_ATTEMPTS ]; then
    echo "Failed to start server after $MAX_ATTEMPTS attempts"
    exit 1
  fi
  
  sleep 2
done

echo "Pulling llama2:7b-chat model..."
ollama pull llama2:7b-chat

echo "Model installed successfully. Stopping temporary server..."
kill $SERVER_PID
sleep 2

echo "Done!" 