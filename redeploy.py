#!/usr/bin/env python3
import os
import requests
import sys
import time

# Get the Render API key from environment or user input
api_key = os.environ.get("RENDER_API_KEY")
if not api_key:
    api_key = input("Enter your Render API key: ")

# The service ID for chat-xray-bot
service_id = "srv-d0i3t06mcj7s739m48r0"

# API endpoint for triggering a manual deploy
deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# According to Render API docs, the payload should be formatted as follows
payload = {
    "clearCache": True
}

print(f"Triggering redeploy for service {service_id} with clear cache...")

# Trigger the deploy with clear_cache=true to ensure fresh dependencies
try:
    response = requests.post(
        deploy_url,
        headers=headers,
        json=payload
    )
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text[:200]}")  # Print first 200 chars to avoid overwhelming output
    
    if response.status_code == 201:
        deploy_data = response.json()
        deploy_id = deploy_data.get("id")
        print(f"✅ Successfully triggered redeploy with ID: {deploy_id}")
        print("Check the status of your deployment at https://dashboard.render.com/")
        print("You can also use ./fetch_render_logs.py to monitor the deployment progress.")
    else:
        print(f"❌ Failed to trigger redeploy: {response.status_code}")
        print(response.text)
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1) 