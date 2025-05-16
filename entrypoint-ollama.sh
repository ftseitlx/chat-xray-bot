#!/bin/bash
set -e

echo "Ollama Entrypoint: Starting initial setup..."

# Start Ollama server in the background to allow pulling
ollama serve &
SERVER_PID=$!

echo "Waiting for Ollama server to be ready for model pull..."
MAX_WAIT=60 # Wait for 60 * 2 = 120 seconds max for server to start
COUNT=0
while ! curl -sf http://localhost:11434/api/version > /dev/null; do
    if [ $COUNT -ge $MAX_WAIT ]; then
        echo "Ollama server failed to start for model pull after $MAX_WAIT attempts."
        # Attempt to capture server logs if possible before exiting
        echo "---- Ollama server logs (if any) ----"
        # This log path might vary, adjust if necessary or remove if too noisy/problematic
        # cat /root/.ollama/logs/server.log || echo "No server log found or cat failed."
        echo "------------------------------------"
        kill $SERVER_PID
        exit 1
    fi
    echo "Ollama server not ready for pull, waiting... (attempt $((COUNT+1))/$MAX_WAIT)"
    sleep 2
    COUNT=$((COUNT+1))
done
echo "Ollama server is ready for model pull."

echo "Pulling llama2:7b-chat model (if not already present)..."
if ollama pull llama2:7b-chat; then
    echo "Model llama2:7b-chat pulled successfully."
else
    echo "Failed to pull llama2:7b-chat model. Continuing without it, but it might cause issues."
    # Depending on strictness, you might want to 'exit 1' here
fi

echo "Model pull phase complete. Stopping temporary server to hand over to CMD..."
# Gracefully stop the server
kill $SERVER_PID
# Wait for the process to actually terminate
timeout 30s wait $SERVER_PID || echo "Ollama temporary server did not stop gracefully, proceeding..."


echo "Ollama Entrypoint: Setup complete. Executing CMD: $@"
exec "$@" 