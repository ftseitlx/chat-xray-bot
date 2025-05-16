import os
import json
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Base URL to the Ollama instance. In Render we will inject environment variable OLLAMA_URL
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Model name – expect that the model is already pulled (llama2:7b-chat fits 8 GB RAM plan)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2:7b-chat")

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
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:4096]},  # truncate to keep response fast
        ],
        "temperature": 0.3,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{OLLAMA_URL}/v1/chat", json=payload)
            r.raise_for_status()
            raw_resp = r.json().get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"Ollama request failed: {e}")
        return {"error": "llama_request_failed", "details": str(e)}

    # Attempt to parse JSON strictly
    try:
        return json.loads(raw_resp)
    except json.JSONDecodeError:
        # Fallback: try to extract first JSON object
        import re
        m = re.search(r"\{.*\}", raw_resp, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        logger.warning("Failed to parse JSON from Llama response: %s", raw_resp[:200])
        return {"error": "invalid_json", "raw": raw_resp[:500]} 