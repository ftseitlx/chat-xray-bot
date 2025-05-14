#!/usr/bin/env python3
import os
import sys
import json
import requests
import time
from datetime import datetime

# Get the Render API key from environment or user input
api_key = os.environ.get("RENDER_API_KEY")
if not api_key:
    api_key = input("Enter your Render API key: ")

# The service ID for chat-xray-bot
service_id = "srv-d0i3t06mcj7s739m48r0"

# API endpoint for getting service logs
logs_url = f"https://api.render.com/v1/services/{service_id}/events"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {api_key}"
}

print(f"Fetching application logs for service {service_id}...")

try:
    response = requests.get(
        logs_url,
        headers=headers,
        params={"limit": 100}
    )
    
    if response.status_code == 200:
        logs_data = response.json()
        print(f"Successfully fetched logs. Found {len(logs_data)} entries.")
        
        # Process and display logs
        for log in logs_data:
            # Convert timestamp to readable format
            timestamp = log.get("createdAt", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = timestamp
            else:
                formatted_time = "Unknown time"
            
            # Get the event type and details
            event = log.get("event", {})
            event_type = event.get("type", "unknown")
            details = event.get("details", {})
            
            # Format the output
            print(f"{formatted_time} - {event_type}")
            if details:
                print(f"  Details: {json.dumps(details)}")
            
            # Add a separator between log entries
            print("-" * 50)
    else:
        print(f"Failed to fetch logs: {response.status_code}")
        print(response.text)
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

# Now try to get the actual application logs
print("\nTrying to get application stdout/stderr logs...")
logs_url = f"https://api.render.com/v1/services/{service_id}/logs"

try:
    response = requests.get(
        logs_url,
        headers=headers
    )
    
    if response.status_code == 200:
        print("Application logs:")
        print(response.text)
    else:
        print(f"Failed to fetch application logs: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error fetching application logs: {e}")

# Try one more endpoint for logs
print("\nTrying alternative logs endpoint...")
logs_url = f"https://api.render.com/v1/services/{service_id}/instances"

try:
    response = requests.get(
        logs_url,
        headers=headers
    )
    
    if response.status_code == 200:
        instances = response.json()
        if instances:
            instance_id = instances[0].get("id")
            if instance_id:
                instance_logs_url = f"https://api.render.com/v1/services/{service_id}/instances/{instance_id}/logs"
                logs_response = requests.get(
                    instance_logs_url,
                    headers=headers
                )
                if logs_response.status_code == 200:
                    print("Instance logs:")
                    print(logs_response.text)
                else:
                    print(f"Failed to fetch instance logs: {logs_response.status_code}")
                    print(logs_response.text)
        else:
            print("No instances found for this service")
    else:
        print(f"Failed to fetch instances: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error fetching instances: {e}") 