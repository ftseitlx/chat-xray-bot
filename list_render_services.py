#!/usr/bin/env python
"""
Script to list Render services.
"""
import os
import requests
import json
import sys

def list_services(api_key):
    """List all services on Render"""
    url = "https://api.render.com/v1/services"
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        services = response.json()
        print("\n=== Render Services ===")
        print(f"Found {len(services)} services\n")
        
        for service in services:
            print(f"Name: {service.get('name')}")
            print(f"ID: {service.get('id')}")
            print(f"Type: {service.get('type')}")
            print(f"Status: {service.get('suspended')}")
            print(f"URL: {service.get('url')}")
            print("-" * 40)
        
        return services
    else:
        print(f"Failed to list services: {response.status_code}")
        print(response.text)
        return None

def main():
    """Main function to list services"""
    # Get API key from environment or user input
    api_key = os.environ.get("RENDER_API_KEY")
    
    if not api_key:
        api_key = input("Enter your Render API Key: ")
    
    services = list_services(api_key)
    
    # Find Ollama service specifically
    if services:
        ollama_services = [s for s in services if 'ollama' in s.get('name', '').lower()]
        if ollama_services:
            print("\n=== Ollama Services ===")
            for service in ollama_services:
                print(f"Name: {service.get('name')}")
                print(f"ID: {service.get('id')}")
                print(f"Type: {service.get('type')}")
                print("-" * 40)
        else:
            print("\nNo Ollama services found.")

if __name__ == "__main__":
    main() 