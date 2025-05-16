#!/bin/bash
set -e

echo "Fixing Ollama service deployment on Render..."

# Check if render-cli is installed
if ! command -v render &> /dev/null; then
    echo "render-cli not found. Installing..."
    npm install -g @render/cli
fi

# Log in to Render (you'll need to provide credentials)
echo "Please log in to your Render account..."
render login

# Deploy updated Ollama service
echo "Deploying Ollama service..."
render deploy --serviceId llama2-ollama

# Optionally restart the bot service for good measure
echo "Restarting Chat X-Ray Bot service..."
render restart --serviceId chat-xray-bot

echo "Deployment complete!"
echo "Wait a few minutes for services to fully initialize."
echo "You can check services status with: render services list" 