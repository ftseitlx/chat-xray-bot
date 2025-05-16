#!/usr/bin/env python
"""
Test the connection between Chat X-Ray Bot and Ollama
"""
import httpx
import asyncio
import json
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_BOT_URL = "https://chat-xray-bot.onrender.com"
TEST_MESSAGE = "Hello! Test connection to Chat X-Ray Bot."

async def test_telegram_webhook(bot_url):
    """Test if the Telegram webhook is configured correctly"""
    try:
        url = f"{bot_url.rstrip('/')}/webhook-info"
        async with httpx.AsyncClient(timeout=30) as client:
            print(f"Testing webhook info endpoint: {url}")
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.text}")
                return True
            else:
                print("Failed to get webhook info")
                return False
    except Exception as e:
        print(f"Error checking webhook: {e}")
        return False

async def test_llm_connection(bot_url):
    """Test the LLM connection through a simple test endpoint"""
    try:
        url = f"{bot_url.rstrip('/')}/test-llm"
        data = {"text": TEST_MESSAGE}
        
        print(f"Testing LLM connection through: {url}")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=data)
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"Failed: {response.text}")
                return False
    except Exception as e:
        print(f"Error testing LLM connection: {e}")
        return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test connection to Chat X-Ray Bot")
    parser.add_argument("--bot-url", default=DEFAULT_BOT_URL, help="URL of the Chat X-Ray Bot")
    
    args = parser.parse_args()
    
    print(f"Testing connection to {args.bot_url}...")
    
    # Test health endpoint
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{args.bot_url.rstrip('/')}/health"
            print(f"Testing health endpoint: {url}")
            response = await client.get(url)
            print(f"Health check status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code != 200:
                print("❌ Health check failed!")
                return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    print("✅ Health check passed!")
    
    # Test webhook configuration
    webhook_ok = await test_telegram_webhook(args.bot_url)
    
    # Test LLM connection
    llm_ok = await test_llm_connection(args.bot_url)
    
    # Print summary
    print("\n=== Test Results ===")
    print(f"Health Check: ✅")
    print(f"Webhook Configuration: {'✅' if webhook_ok else '❌'}")
    print(f"LLM Connection: {'✅' if llm_ok else '❌'}")
    
    if webhook_ok and llm_ok:
        print("\n🎉 All checks passed! The bot is fully operational.")
    else:
        print("\n⚠️ Some tests failed. The bot may not be fully functional.")

if __name__ == "__main__":
    asyncio.run(main()) 