#!/bin/bash

# Check if RENDER_API_KEY is set
if [ -z "$RENDER_API_KEY" ]; then
  echo "Error: RENDER_API_KEY environment variable is not set"
  echo "Please run: export RENDER_API_KEY=your_api_key"
  exit 1
fi

# Service ID for chat-xray-bot
SERVICE_ID="srv-d0i3t06mcj7s739m48r0"

echo "Triggering redeploy for service $SERVICE_ID with clear cache..."

# Trigger a manual deploy with clear cache option
response=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -d '{"clearCache": true}' \
  "https://api.render.com/v1/services/$SERVICE_ID/deploys")

# Extract the HTTP status code
http_code=$(echo "$response" | tail -n1)
# Extract the response body
body=$(echo "$response" | sed '$d')

echo "Response status code: $http_code"
echo "Response body: $body"

if [ "$http_code" -eq 201 ]; then
  echo "✅ Successfully triggered redeploy"
  echo "Check the status of your deployment at https://dashboard.render.com/"
  echo "You can also use ./fetch_render_logs.py to monitor the deployment progress."
else
  echo "❌ Failed to trigger redeploy: $http_code"
  exit 1
fi 