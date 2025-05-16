#!/usr/bin/env python
"""
Script to manually deploy to Render using their API.
"""
import os
import requests
import json
import time
import argparse

# Service ID for the main Chat X-Ray Bot
CHAT_XRAY_SERVICE_ID = "srv-d0i3t06mcj7s739m48r0"  # This appears to be correct

def deploy_service(service_id, api_key):
    """Deploy a service to Render using their API"""
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Get the clear build option from user input
    clear_cache = input("Do you want to clear the build cache? (y/n): ").lower() == 'y'
    
    data = {
        "clearCache": "clear" if clear_cache else "do_not_clear"
    }
    
    print(f"Deploying service {service_id}...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in (200, 201):
        print(f"Deployment triggered successfully for {service_id}")
        deploy_data = response.json()
        print(f"Deploy ID: {deploy_data.get('id')}")
        print(f"Status: {deploy_data.get('status')}")
        return deploy_data
    else:
        print(f"Deployment failed for {service_id} with status code {response.status_code}")
        print(response.text)
        return None

def check_deploy_status(service_id, deploy_id, api_key):
    """Check the status of a deployment"""
    url = f"https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        deploy_data = response.json()
        return deploy_data.get("status")
    else:
        print(f"Failed to check deployment status: {response.status_code}")
        return None

def main():
    """Main function to deploy services"""
    parser = argparse.ArgumentParser(description="Deploy to Render")
    parser.add_argument("--api-key", help="Render API Key")
    parser.add_argument("--service-id", help="Service ID to deploy", default=CHAT_XRAY_SERVICE_ID)
    
    args = parser.parse_args()
    
    # Get API key from argument or environment
    api_key = args.api_key or os.environ.get("RENDER_API_KEY")
    
    if not api_key:
        api_key = input("Enter your Render API Key: ")
    
    # Get service ID
    service_id = args.service_id
    
    # Deploy Chat X-Ray Bot service
    print("\n=== Deploying to Render ===")
    deploy_data = deploy_service(service_id, api_key)
    
    if deploy_data:
        print("\nDeployment has been triggered successfully.")
        print("Deployment can take several minutes to complete.")
        print("You can check status on the Render dashboard.")
        
        # Optionally check status after a minute
        deploy_id = deploy_data.get("id")
        print("\nWaiting 60 seconds to check status...")
        time.sleep(60)
        
        status = check_deploy_status(service_id, deploy_id, api_key)
        if status:
            print(f"Current deployment status: {status}")
        
        print("\nDeployment will continue in the background.")
        print("Visit the Render dashboard to monitor progress.")
        print(f"https://dashboard.render.com/web/{service_id}")

if __name__ == "__main__":
    main() 