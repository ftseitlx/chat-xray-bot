import json
import httpx
import logging
import asyncio
from typing import Dict, Any, Optional, List
import openai
from openai import AsyncOpenAI

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
    """
    Process text chunks using OpenAI GPT-3.5-turbo model.
    This function no longer uses Ollama/Llama2 but uses OpenAI API directly.
    """
    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        logger.info(f"Processing chunk with GPT-3.5-turbo, text length: {len(text[:100])}...")
        
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
            
            logger.error("Failed to parse JSON response")
            return {"error": "json_parse_error", "raw_response": raw_resp[:200]}
            
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {"error": "openai_api_error", "details": str(e)}

# Keep LocalLLM class for compatibility with existing code
class LocalLLM:
    """
    Compatibility class that now uses OpenAI instead of Ollama/Llama
    """
    
    def __init__(self):
        self.model = "gpt-3.5-turbo"
    
    def is_available(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Just check if we have an API key
            if not settings.OPENAI_API_KEY:
                logger.error("OpenAI API key is not set")
                return False
                
            logger.info("OpenAI integration is available")
            return True
        except Exception as e:
            logger.error(f"OpenAI service check failed: {e}")
            return False
    
    def generate(self, prompt: str) -> str:
        """Send a completion request to OpenAI"""
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=150
            )
            return response.choices[0].text
        except Exception as e:
            logger.error(f"OpenAI generate error: {e}")
            return f"Error: OpenAI API error - {str(e)}"
    
    async def generate_async(self, prompt: str) -> str:
        """Send an async completion request to OpenAI"""
        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=150
            )
            return response.choices[0].text
        except Exception as e:
            logger.error(f"Async OpenAI generate error: {e}")
            return f"Error: OpenAI API error - {str(e)}" 