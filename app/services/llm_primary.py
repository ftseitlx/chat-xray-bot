import json
import logging
import time
import asyncio
import os
from typing import List, Dict, Any, Callable, Awaitable, Optional, Tuple
from pathlib import Path

import openai
from openai import AsyncOpenAI

from app.config import settings

# Import local Llama wrapper if enabled
if settings.USE_LOCAL_LLM:
    from app.services.local_llm import analyse_chunk_with_llama

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Primary analysis prompt
PRIMARY_PROMPT = """
Вы эксперт-психолог, специализирующийся на анализе отношений. Для каждого сообщения проанализируйте и верните на русском языке:
{
  "author": "автор_сообщения",
  "timestamp": "временная_метка",
  "sentiment": "позитивный/негативный/нейтральный с кратким объяснением на русском",
  "sentiment_score": число от -1.0 до 1.0, где -1 очень негативно, а 1 очень позитивно,
  "emotion": "основная эмоция в сообщении (радость/грусть/гнев/страх/удивление/отвращение/стыд/вина)",
  "emotion_intensity": число от 0 до 1, отражающее интенсивность эмоции,
  "toxicity": 0-1 (числовая оценка токсичности),
  "manipulation": 0-1 (числовая оценка манипулятивности),
  "empathy": 0-1 (числовая оценка эмпатии в сообщении),
  "assertiveness": 0-1 (числовая оценка ассертивности в сообщении),
  "vulnerability": 0-1 (числовая оценка уязвимости и открытости),
  "attachment_style": "надежный/тревожный/избегающий/дезорганизованный по теории Габора Мате",
  "attachment_intensity": 0-1 (числовая оценка проявления стиля привязанности),
  "communication_pattern": "ассертивный/пассивный/агрессивный/пассивно-агрессивный",
  "gottman_horsemen": {
    "criticism": 0-1 (степень присутствия критики),
    "contempt": 0-1 (степень присутствия презрения),
    "defensiveness": 0-1 (степень присутствия защиты),
    "stonewalling": 0-1 (степень присутствия игнорирования)
  },
  "gottman_positive_interactions": {
    "appreciation": 0-1 (выражение признательности),
    "interest": 0-1 (проявление интереса),
    "affection": 0-1 (проявление привязанности),
    "repair_attempts": 0-1 (попытки восстановления отношений)
  },
  "transactional_state": "родитель/взрослый/ребенок по теории Эрика Берна",
  "transactional_intensity": 0-1 (интенсивность проявления эго-состояния),
  "psychological_needs": "ключевые потребности выраженные или неудовлетворенные, по Маслоу и Габору Мате",
  "needs_intensity": 0-1 (интенсивность выражения потребностей),
  "boundary_setting": -1 до 1 (отрицательные значения - нарушение границ, положительные - установка здоровых границ),
  "power_dynamics": -1 до 1 (отрицательные значения - подчинение, положительные - доминирование),
  "relational_bid": "запрос на внимание/поворот к партнеру/поворот от партнера/против партнера по теории Готтмана",
  "relationship_threat_level": 0-1 (общий уровень угрозы отношениям в данном сообщении),
  "key_quotes": ["до двух важных цитат из сообщения"]
}

ОСОБОЕ ВНИМАНИЕ УДЕЛИТЕ КЛЮЧЕВЫМ ЦИТАТАМ:
1. Выбирайте наиболее эмоционально значимые и психологически важные цитаты
2. Предпочитайте цитаты, которые отражают:
   - Сильные эмоциональные реакции
   - Ключевые моменты в отношениях
   - Проявления стилей привязанности
   - Наличие "четырех всадников" Готтмана
   - Выражение глубинных психологических потребностей
3. Включайте цитаты дословно из оригинального сообщения
4. Если сообщение короткое, но значимое - включите его целиком
5. Для каждого сообщения старайтесь извлечь хотя бы одну значимую цитату

Выведите результат в формате JSON. Обязательно анализируйте количественные параметры максимально точно, так как они будут использованы для создания графиков и визуализаций.
"""

async def process_chunk(chunk: List[Dict[str, Any]], max_retries: int = 3) -> Tuple[List[Dict[str, Any]], int]:
    """
    Process a single chunk of messages using local Llama for analysis.
    
    Args:
        chunk: List of message dictionaries
        max_retries: Maximum number of retries on rate limit errors
        
    Returns:
        Tuple containing the list of processed message dictionaries with analysis and the number of tokens used
    """
    # Route chunk to Ollama for analysis
    try:
        chunk_text = "\n\n".join(m["raw"] for m in chunk)
        logger.info(f"Processing chunk with local Llama model: {settings.OLLAMA_MODEL}")
        llama_result = await analyse_chunk_with_llama(chunk_text)
        
        if "error" in llama_result:
            logger.error(f"Local Llama analysis failed: {llama_result['error']}")
            if "details" in llama_result:
                logger.error(f"Error details: {llama_result['details']}")
            return [{"error": llama_result["error"], "raw_input": msg["raw"]} for msg in chunk], 0
            
        # Normalize to list-of-dicts shape expected downstream
        if isinstance(llama_result, list):
            return llama_result, 0
        else:
            return [llama_result], 0
                
    except Exception as le:
        logger.error(f"Local Llama analysis failed with exception: {le}")
        return [{"error": str(le), "raw_input": msg["raw"]} for msg in chunk], 0


async def process_chunks(
    chunks: List[List[Dict[str, Any]]],
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Process all chunks of messages in parallel and combine the results.
    
    Args:
        chunks: List of chunks, where each chunk is a list of message dictionaries
        progress_callback: Optional callback function to report progress
        
    Returns:
        Tuple containing the list of all processed message dictionaries with analysis and the total number of tokens used
    """
    # Use concurrency limit from settings
    concurrency_limit = settings.OPENAI_CONCURRENCY_LIMIT
    
    # Use a semaphore to limit concurrent API calls
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    async def process_with_semaphore(i, chunk):
        """Process a chunk with semaphore to limit concurrency"""
        async with semaphore:
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            result, tokens_used = await process_chunk(chunk)
            # Report progress if callback provided
            if progress_callback:
                try:
                    await progress_callback(i + 1, len(chunks))
                except Exception as cb_err:
                    logger.warning(f"Progress callback error: {cb_err}")
            return result, tokens_used
    
    # Create tasks for all chunks
    tasks = [process_with_semaphore(i, chunk) for i, chunk in enumerate(chunks)]
    
    # Process all chunks in parallel and wait for all results
    logger.info(f"Processing {len(chunks)} chunks with max concurrency of {concurrency_limit}")
    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results, handling any exceptions that occurred
    results = []
    total_tokens = 0
    for i, res in enumerate(chunk_results):
        if isinstance(res, Exception):
            logger.error(f"Error processing chunk {i+1}: {res}")
            # Add error placeholders for this chunk
            results.extend([{"error": str(res), "raw_input": msg["raw"]} for msg in chunks[i]])
        else:
            chunk_result, tokens_used = res
            results.extend(chunk_result)
            total_tokens += tokens_used
    
    return results, total_tokens

def extract_messages_from_text(file_path: Path) -> List[Dict[str, Any]]:
    logger.info(f"→ START extract_messages_from_text ({file_path})")
    start_ts = time.time()
    try:
        ...
        logger.info(f"extract_messages_from_text: finished patterns, got {len(messages)} msgs")
        ...
        logger.info(f"← END extract_messages_from_text — {len(messages)} msgs, elapsed {time.time()-start_ts:.1f}s")
        return messages
    except Exception as e:
        logger.exception("extract_messages_from_text FAILED")
        raise 