#!/usr/bin/env python
"""
Script to check if Ollama is accessible through various connection methods.
"""
import httpx
import asyncio
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# List of all possible Ollama URLs to try
POTENTIAL_URLS = [
    "http://localhost:11434",
    "http://127.0.0.1:11434",
    "https://llama2-ollama.onrender.com",
    "https://llama2-ollama.onrender.com/api",
    "http://llama2-ollama:11434",
    "http://ollama:11434"
]

# API endpoints to test on each URL
API_ENDPOINTS = [
    "/api/version",
    "/v1/models",
    "/api/tags",
    "/"
]

async def check_endpoint(base_url, endpoint):
    """Check if a specific endpoint is accessible"""
    url = f"{base_url.rstrip('/')}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            logger.info(f"Testing endpoint: {url}")
            response = await client.get(url)
            if response.status_code == 200:
                logger.info(f"✅ SUCCESS: {url} - Status: {response.status_code}")
                logger.info(f"Response: {response.text[:200]}")
                return True
            else:
                logger.warning(f"❌ FAILED: {url} - Status: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ ERROR: {url} - {str(e)}")
        return False

async def main():
    """Check all potential Ollama connections"""
    logger.info("Starting Ollama connectivity check...")
    
    success_found = False
    
    for base_url in POTENTIAL_URLS:
        for endpoint in API_ENDPOINTS:
            if await check_endpoint(base_url, endpoint):
                success_found = True
                logger.info(f"✅ USABLE OLLAMA API FOUND: {base_url}{endpoint}")
    
    if success_found:
        logger.info("✅ At least one Ollama endpoint is accessible!")
    else:
        logger.error("❌ No accessible Ollama endpoints found!")
        logger.info("Recommendations:")
        logger.info(" 1. Check if Ollama is running locally or in Docker")
        logger.info(" 2. Verify network connectivity between services")
        logger.info(" 3. Check if Ollama service is properly deployed on Render")

if __name__ == "__main__":
    asyncio.run(main()) 