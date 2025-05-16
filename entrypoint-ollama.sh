#!/bin/bash
set -e

echo "[$(date)] Ollama Entrypoint: Starting initial setup..."

# Function to log with timestamp
log() {
    echo "[$(date)] $1"
}

log "System info:"
free -m | grep -v total
df -h | grep -v tmpfs

# Clean up any previous run that might have left resources behind
log "Cleaning up any previous processes..."
pkill -f ollama || true
sleep 2

# Start Ollama server in the background to allow pulling
log "Starting Ollama server for model preparation..."
ollama serve &
SERVER_PID=$!

# Verify server process is running
ps -p $SERVER_PID || {
    log "ERROR: Ollama server process not found after attempted start"
    exit 1
}

log "Waiting for Ollama server to be ready for model pull..."
MAX_WAIT=120 # Wait for 120 * 2 = 240 seconds (4 minutes) max for server to start
COUNT=0
while ! curl -sf http://localhost:11434/api/version > /dev/null; do
    if [ $COUNT -ge $MAX_WAIT ]; then
        log "ERROR: Ollama server failed to start for model pull after $MAX_WAIT attempts."
        log "---- Ollama process info ----"
        ps -ef | grep ollama
        log "---- Network info ----"
        netstat -tulpn | grep LISTEN
        kill $SERVER_PID || true
        exit 1
    fi
    log "Ollama server not ready for pull, waiting... (attempt $((COUNT+1))/$MAX_WAIT)"
    sleep 2
    COUNT=$((COUNT+1))
done
log "Ollama server is ready for model pull."

log "Listing available models..."
ollama list || log "WARNING: Could not list models"

log "Pulling llama2:7b-chat model (if not already present)..."
if ollama pull llama2:7b-chat; then
    log "Model llama2:7b-chat pulled successfully."
else
    log "ERROR: Failed to pull llama2:7b-chat model."
    log "Will try smaller model llama2:latest as fallback..."
    if ollama pull llama2; then
        log "Model llama2 pulled successfully as fallback."
    else
        log "ERROR: Failed to pull any model. Service may not work properly."
        # Smaller model is required for minimum functionality
        log "Trying to create minimal model placeholder..."
        echo '{"name":"llama2:7b-chat","description":"placeholder model"}' > /tmp/modelfile
        ollama create llama2:7b-chat -f /tmp/modelfile || true
    fi
fi

log "Listing available models after pull..."
ollama list || log "WARNING: Could not list models"

log "Model pull phase complete. Stopping temporary server..."
# Gracefully stop the server
log "Sending SIGTERM to Ollama server PID $SERVER_PID"
kill $SERVER_PID || log "WARNING: Could not kill server, it may have already exited"

# Wait for the process to actually terminate
log "Waiting for server to terminate..."
timeout 30s sh -c "while kill -0 $SERVER_PID 2>/dev/null; do sleep 1; done" || {
    log "WARNING: Ollama server did not terminate gracefully, forcing stop"
    kill -9 $SERVER_PID 2>/dev/null || true
}
sleep 2

log "Ollama Entrypoint: Setup complete. Executing: $@"
exec "$@" 