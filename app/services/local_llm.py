import json
import httpx
import logging
from typing import Dict, Any

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
    """Send the chunk to a local Ollama Llama2 chat model and parse JSON reply."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:4096]},  # truncate to keep response fast
        ],
        "temperature": 0.3,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"Sending request to Ollama at {settings.OLLAMA_URL}")
            r = await client.post(f"{settings.OLLAMA_URL}/v1/chat", json=payload)
            r.raise_for_status()
            raw_resp = r.json().get("message", {}).get("content", "")
            logger.debug(f"Received response from Ollama: {raw_resp[:200]}...")
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to Ollama at {settings.OLLAMA_URL}: {e}")
        return {"error": "connection_failed", "details": str(e)}
    except httpx.TimeoutException as e:
        logger.error(f"Request to Ollama timed out after {timeout}s: {e}")
        return {"error": "timeout", "details": str(e)}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error from Ollama: {e}")
        return {"error": "http_error", "details": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during Ollama request: {e}")
        return {"error": "unexpected_error", "details": str(e)}

    # Attempt to parse JSON strictly
    try:
        result = json.loads(raw_resp)
        logger.info("Successfully parsed JSON response from Ollama")
        return result
    except json.JSONDecodeError:
        # Fallback: try to extract first JSON object
        import re
        m = re.search(r"\{.*\}", raw_resp, re.S)
        if m:
            try:
                result = json.loads(m.group(0))
                logger.info("Successfully extracted and parsed JSON from response")
                return result
            except Exception as e:
                logger.error(f"Failed to parse extracted JSON: {e}")
        
        logger.warning("Failed to parse JSON from Llama response: %s", raw_resp[:200])
        return {"error": "invalid_json", "raw": raw_resp[:500]} 