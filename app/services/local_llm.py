import json
import httpx
import logging
import asyncio
from typing import Dict, Any, Optional, List

from app.config import settings

logger = logging.getLogger(__name__)

# System prompt that forces the model to output strict JSON we expect downstream
SYSTEM_PROMPT = (
    "Ты психолог-аналитик. На входе тебе приходит фрагмент переписки. "
    "Верни ТОЛЬКО валидный JSON c ключами: sentiment_score, toxicity, manipulation, "
    "empathy, assertiveness, emotion_intensity, communication_pattern, gottman_horsemen, key_quotes. "
    "Числовые поля – float от 0 до 1 (или -1…1 где уместно). key_quotes – массив до 3 строк."
)

async def analyse_chunk_with_llama(text: str, timeout: int = 60) -> Dict[str, Any]:
    """Send the chunk to a local Ollama Llama2 chat model and parse JSON reply.
    Will attempt different API endpoints and fall back to OpenAI if needed."""
    payload_chat = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:4096]},  # truncate to keep response fast
        ],
        "temperature": 0.3,
    }
    
    payload_generate = {
        "model": settings.OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nВходящий текст: {text[:4096]}",
        "temperature": 0.3,
    }
    
    # Try different potential base URLs
    base_urls = [
        settings.OLLAMA_URL,                                # Default from settings
        settings.OLLAMA_URL.rstrip('/api'),                 # Remove /api if present
        f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}",  # Construct from host/port
        "http://llama2-ollama:11434",                      # Docker service name
        "http://ollama:11434",                             # Docker compose service name
        "https://llama2-ollama.onrender.com",              # Direct Render URL
        "https://llama2-ollama.onrender.com/api"           # Render URL with /api
    ]
    
    # Try different endpoints for each base URL
    endpoints = [
        ("/api/chat", payload_chat, lambda r: r.json().get("message", {}).get("content", "")),
        ("/v1/chat/completions", payload_chat, lambda r: r.json().get("choices", [{}])[0].get("message", {}).get("content", "")),
        ("/api/generate", payload_generate, lambda r: r.json().get("response", "")),
        ("/v1/completions", payload_generate, lambda r: r.json().get("choices", [{}])[0].get("text", ""))
    ]
    
    errors = []
    
    # Try all base URL + endpoint combinations
    for base_url in base_urls:
        base_url = base_url.rstrip('/')  # Normalize URL
        logger.info(f"Trying base URL: {base_url}")
        
        for endpoint, payload, response_extractor in endpoints:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    url = f"{base_url}{endpoint}"
                    logger.info(f"Trying Ollama endpoint {url}")
                    r = await client.post(url, json=payload)
                    r.raise_for_status()
                    raw_resp = response_extractor(r)
                    
                    if raw_resp:
                        logger.debug(f"Received response from Ollama: {raw_resp[:200]}...")
                        
                        # Try to parse JSON
                        try:
                            result = json.loads(raw_resp)
                            logger.info(f"Successfully parsed JSON response from Ollama via {url}")
                            return result
                        except json.JSONDecodeError:
                            # Fallback: try to extract first JSON object
                            import re
                            m = re.search(r"\{.*\}", raw_resp, re.S)
                            if m:
                                try:
                                    result = json.loads(m.group(0))
                                    logger.info(f"Successfully extracted and parsed JSON from response via {url}")
                                    return result
                                except Exception as e:
                                    logger.error(f"Failed to parse extracted JSON: {e}")
                    
                    logger.warning(f"Failed to get usable response from {url}")
                    
            except httpx.ConnectError as e:
                logger.error(f"Failed to connect to Ollama at {url}: {e}")
                errors.append(f"Connection error ({url}): {str(e)}")
            except httpx.TimeoutException as e:
                logger.error(f"Request to Ollama at {url} timed out after {timeout}s: {e}")
                errors.append(f"Timeout error ({url}): {str(e)}")
            except httpx.HTTPError as e:
                logger.error(f"HTTP error from Ollama ({url}): {e}")
                errors.append(f"HTTP error ({url}): {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error during Ollama request ({url}): {e}")
                errors.append(f"Unexpected error ({url}): {str(e)}")
    
    # All Ollama endpoints failed, fallback to OpenAI if available
    if settings.OPENAI_API_KEY:
        logger.warning("All Ollama endpoints failed. Falling back to OpenAI.")
        try:
            import openai
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text[:4096]}
                ],
                temperature=0.3,
            )
            
            raw_resp = response.choices[0].message.content
            
            try:
                result = json.loads(raw_resp)
                logger.info("Successfully parsed JSON response from OpenAI")
                return result
            except json.JSONDecodeError:
                # Fallback: try to extract first JSON object
                import re
                m = re.search(r"\{.*\}", raw_resp, re.S)
                if m:
                    try:
                        result = json.loads(m.group(0))
                        logger.info("Successfully extracted and parsed JSON from OpenAI response")
                        return result
                    except Exception as e:
                        logger.error(f"Failed to parse extracted JSON from OpenAI: {e}")
            
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}")
            errors.append(f"OpenAI fallback error: {str(e)}")
        
    logger.warning(f"All LLM attempts failed. Errors: {', '.join(errors)}")
    return {"error": "all_endpoints_failed", "details": errors}

# Add LocalLLM class for tests
class LocalLLM:
    """A simple class-based client for Ollama used in tests"""
    
    def __init__(self):
        self.base_urls = [
            settings.OLLAMA_URL,                                # Default from settings
            settings.OLLAMA_URL.rstrip('/api'),                 # Remove /api if present
            f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}",  # Construct from host/port
            "http://llama2-ollama:11434",                      # Docker service name
            "http://ollama:11434",                             # Docker compose service name
            "https://llama2-ollama.onrender.com",              # Direct Render URL
            "https://llama2-ollama.onrender.com/api"           # Render URL with /api
        ]
        self.model = settings.OLLAMA_MODEL
    
    def is_available(self) -> bool:
        """Check if Ollama is available by querying its API version endpoint"""
        try:
            # Try several endpoints to see if any respond
            for base_url in self.base_urls:
                base_url = base_url.rstrip('/')
                for endpoint in ['/api/version', '/v1/models', '/']:
                    try:
                        response = httpx.get(f"{base_url}{endpoint}", timeout=5)
                        if response.status_code == 200:
                            logger.info(f"Ollama is available via {base_url}{endpoint}")
                            return True
                    except:
                        continue
            
            logger.error("All Ollama API endpoints failed")
            return False
        except Exception as e:
            logger.error(f"Ollama service check failed: {e}")
            return False
    
    def generate(self, prompt: str) -> str:
        """Send a completion request to Ollama"""
        for base_url in self.base_urls:
            base_url = base_url.rstrip('/')
            endpoints = [
                ('/api/generate', lambda r: r.json().get("response", "")),
                ('/v1/completions', lambda r: r.json().get("choices", [{}])[0].get("text", ""))
            ]
            
            for endpoint, response_extractor in endpoints:
                try:
                    response = httpx.post(
                        f"{base_url}{endpoint}",
                        json={"model": self.model, "prompt": prompt},
                        timeout=30
                    )
                    response.raise_for_status()
                    result = response_extractor(response)
                    if result:
                        return result
                except:
                    continue
                
        # Fallback to OpenAI if available
        if settings.OPENAI_API_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    max_tokens=150
                )
                return response.choices[0].text
            except Exception as e:
                logger.error(f"OpenAI fallback failed: {e}")
                
        return "Error: All LLM endpoints failed"
    
    async def generate_async(self, prompt: str) -> str:
        """Send an async completion request to Ollama"""
        for base_url in self.base_urls:
            base_url = base_url.rstrip('/')
            endpoints = [
                ('/api/generate', lambda r: r.json().get("response", "")),
                ('/v1/completions', lambda r: r.json().get("choices", [{}])[0].get("text", ""))
            ]
            
            for endpoint, response_extractor in endpoints:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        response = await client.post(
                            f"{base_url}{endpoint}",
                            json={"model": self.model, "prompt": prompt}
                        )
                        response.raise_for_status()
                        result = response_extractor(response)
                        if result:
                            return result
                except:
                    continue
                
        # Fallback to OpenAI if available
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                response = await client.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    max_tokens=150
                )
                return response.choices[0].text
            except Exception as e:
                logger.error(f"Async OpenAI fallback failed: {e}")
                
        return "Error: All async LLM endpoints failed" 