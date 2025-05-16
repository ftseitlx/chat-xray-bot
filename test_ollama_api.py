#!/usr/bin/env python
"""
Script to test Ollama API with multiple connection options.
"""
import httpx
import asyncio
import json
import argparse
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Test prompt
TEST_PROMPT = "Привет! Как дела? Проанализируй это сообщение."

async def test_connection(base_url):
    """Test connection to Ollama API"""
    logger.info(f"Testing connection to {base_url}")
    
    endpoints = [
        "/api/version", 
        "/v1/models",
        "/api/tags"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                logger.info(f"GET {url}")
                response = await client.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ {url} - Status: {response.status_code}")
                    logger.info(f"Response: {response.text[:100]}...")
                    return True
                else:
                    logger.warning(f"❌ {url} - Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to {url}: {e}")
            
    return False

async def test_completion(base_url, model="llama3.2"):
    """Test completion API"""
    logger.info(f"Testing completion with {base_url} and model {model}")
    
    try:
        # Try chat API
        url = f"{base_url.rstrip('/')}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": TEST_PROMPT}
            ]
        }
        
        logger.info(f"Testing chat endpoint: {url}")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Chat API success! Status: {response.status_code}")
                
                # Handle Ollama's streaming JSON format
                try:
                    # Try to parse response as normal JSON first
                    json_data = response.json()
                    content = json_data.get("message", {}).get("content", "")
                except json.JSONDecodeError:
                    # If that fails, try to extract the first JSON object from potentially multiple objects
                    text = response.text
                    # Find the first complete JSON object
                    match = re.search(r'\{.*?\}', text, re.DOTALL)
                    if match:
                        try:
                            json_data = json.loads(match.group(0))
                            content = json_data.get("message", {}).get("content", "")
                        except:
                            content = f"Could not parse JSON, raw text: {text[:100]}..."
                    else:
                        content = f"Raw response: {text[:100]}..."
                
                logger.info(f"Response content: {content[:100]}...")
                return True
            else:
                logger.warning(f"❌ Chat API failed with status: {response.status_code}")
                
        # Try generate API
        url = f"{base_url.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "prompt": TEST_PROMPT
        }
        
        logger.info(f"Testing generate endpoint: {url}")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Generate API success! Status: {response.status_code}")
                
                # Handle Ollama's streaming response format
                try:
                    json_data = response.json()
                    content = json_data.get("response", "")
                except json.JSONDecodeError:
                    # Try to handle streaming format where multiple JSON objects might be present
                    text = response.text
                    match = re.search(r'\{.*?\}', text, re.DOTALL)
                    if match:
                        try:
                            json_data = json.loads(match.group(0))
                            content = json_data.get("response", "")
                        except:
                            content = f"Could not parse JSON, raw text: {text[:100]}..."
                    else:
                        content = f"Raw response: {text[:100]}..."
                
                logger.info(f"Response: {content[:100]}...")
                return True
            else:
                logger.warning(f"❌ Generate API failed with status: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error testing completion: {e}")
        logger.error(f"Response text: {response.text[:200]}")
        
    return False

async def main():
    parser = argparse.ArgumentParser(description="Test Ollama API")
    parser.add_argument("--url", default="https://llama2-ollama.onrender.com", 
                        help="Base URL for Ollama API")
    parser.add_argument("--model", default="llama3.2", 
                        help="Model to test")
    args = parser.parse_args()
    
    # Test connection
    if await test_connection(args.url):
        logger.info("Connection test passed!")
        
        # Test completion
        if await test_completion(args.url, args.model):
            logger.info("✅ All tests passed! Ollama API is working correctly.")
        else:
            logger.error("❌ Completion test failed. API connection works but completion doesn't.")
    else:
        logger.error("❌ Connection test failed. Cannot reach Ollama API.")

if __name__ == "__main__":
    asyncio.run(main()) 