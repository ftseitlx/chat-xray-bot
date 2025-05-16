#!/usr/bin/env python
"""
Script to test the Chat X-Ray Bot and Ollama service after deployment.
"""
import requests
import json
import argparse
import time
import sys

def test_ollama_service(base_url):
    """Test if the Ollama service is responding"""
    print(f"\n=== Testing Ollama Service: {base_url} ===")
    
    endpoints = [
        "/api/version",
        "/v1/models",
        "/api/tags",
        "/"
    ]
    
    success = False
    
    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}{endpoint}"
        try:
            print(f"Testing: {url}...")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! Status code: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                success = True
                break
            else:
                print(f"❌ FAILED. Status code: {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    if success:
        print("\nOllama service is available! ✅")
    else:
        print("\nOllama service is not responding. ❌")
    
    return success

def test_chat_xray_bot(base_url):
    """Test if the Chat X-Ray Bot is responding"""
    print(f"\n=== Testing Chat X-Ray Bot: {base_url} ===")
    
    health_url = f"{base_url.rstrip('/')}/health"
    
    try:
        print(f"Testing health endpoint: {health_url}...")
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print("\nChat X-Ray Bot is running! ✅")
            return True
        else:
            print(f"❌ FAILED. Status code: {response.status_code}")
            print("\nChat X-Ray Bot is not responding properly. ❌")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("\nChat X-Ray Bot is not accessible. ❌")
        return False

def main():
    """Main function to test deployed services"""
    parser = argparse.ArgumentParser(description="Test deployed services")
    parser.add_argument("--ollama-url", default="https://llama2-ollama.onrender.com", 
                        help="Base URL for Ollama service")
    parser.add_argument("--bot-url", default="https://chat-xray-bot.onrender.com",
                        help="Base URL for Chat X-Ray Bot")
    parser.add_argument("--wait", type=int, default=0,
                        help="Wait time in seconds before testing (for newly deployed services)")
    
    args = parser.parse_args()
    
    # Wait if specified
    if args.wait > 0:
        print(f"Waiting {args.wait} seconds for services to initialize...")
        time.sleep(args.wait)
    
    # Test both services
    ollama_success = test_ollama_service(args.ollama_url)
    bot_success = test_chat_xray_bot(args.bot_url)
    
    # Print final results
    print("\n=== TEST RESULTS ===")
    print(f"Ollama Service: {'✅ OPERATIONAL' if ollama_success else '❌ NOT RESPONDING'}")
    print(f"Chat X-Ray Bot: {'✅ OPERATIONAL' if bot_success else '❌ NOT RESPONDING'}")
    
    if ollama_success and bot_success:
        print("\n🎉 All services are operational!")
        return 0
    else:
        print("\n⚠️ Some services are not responding. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 