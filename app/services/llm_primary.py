import json
import logging
import time
import asyncio
import os
from typing import List, Dict, Any, Callable, Awaitable, Optional

import openai
from openai import AsyncOpenAI

from app.config import settings

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

async def process_chunk(chunk: List[Dict[str, Any]], max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    Process a single chunk of messages using GPT-3.5-turbo.
    
    Args:
        chunk: List of message dictionaries
        max_retries: Maximum number of retries on rate limit errors
        
    Returns:
        List of processed message dictionaries with analysis
    """
    # Format the chat log for the model
    chat_log = "\n\n".join([f"{msg['raw']}" for msg in chunk])
    
    retry_count = 0
    backoff_time = 1  # Start with 1 second backoff
    
    while retry_count <= max_retries:
        try:
            # Call the OpenAI API
            response = await client.chat.completions.create(
                model=settings.PRIMARY_MODEL,
                messages=[
                    {"role": "system", "content": PRIMARY_PROMPT},
                    {"role": "user", "content": f"Проанализируйте этот сегмент чата на русском языке:\n\n{chat_log}"}
                ],
                temperature=0.5,
                max_tokens=4000,
                n=1,
                response_format={"type": "json_object"}
            )
            
            # Extract the response content
            result_text = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                result_json = json.loads(result_text)
                
                # Check if we got a list as expected
                if "messages" in result_json:
                    return result_json["messages"]
                elif isinstance(result_json, list):
                    return result_json
                else:
                    # Try to adapt the format if it's not as expected
                    return [result_json]
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from GPT-3.5 response: {e}")
                logger.debug(f"Raw response: {result_text}")
                
                # Try a more forgiving approach - use regex to extract JSON objects
                import re
                json_objects = re.findall(r'\{[^{}]*\}', result_text)
                if json_objects:
                    try:
                        return [json.loads(obj) for obj in json_objects]
                    except:
                        pass
                
                # Return a basic structure if JSON parsing fails
                return [{"error": "Failed to parse model output", "raw_input": msg["raw"]} for msg in chunk]
        
        except openai.RateLimitError as e:
            retry_count += 1
            logger.warning(f"Rate limit exceeded (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count <= max_retries:
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached. Returning error structure.")
                return [{"error": str(e), "raw_input": msg["raw"]} for msg in chunk]
                
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            # Return an error object
            return [{"error": str(e), "raw_input": msg["raw"]} for msg in chunk]


async def process_chunks(
    chunks: List[List[Dict[str, Any]]],
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
) -> List[Dict[str, Any]]:
    """
    Process all chunks of messages in parallel and combine the results.
    
    Args:
        chunks: List of chunks, where each chunk is a list of message dictionaries
        progress_callback: Optional callback function to report progress
        
    Returns:
        List of all processed message dictionaries with analysis
    """
    # Use concurrency limit from settings
    concurrency_limit = settings.OPENAI_CONCURRENCY_LIMIT
    
    # Use a semaphore to limit concurrent API calls
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    async def process_with_semaphore(i, chunk):
        """Process a chunk with semaphore to limit concurrency"""
        async with semaphore:
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            result = await process_chunk(chunk)
            # Report progress if callback provided
            if progress_callback:
                try:
                    await progress_callback(i + 1, len(chunks))
                except Exception as cb_err:
                    logger.warning(f"Progress callback error: {cb_err}")
            return result
    
    # Create tasks for all chunks
    tasks = [process_with_semaphore(i, chunk) for i, chunk in enumerate(chunks)]
    
    # Process all chunks in parallel and wait for all results
    logger.info(f"Processing {len(chunks)} chunks with max concurrency of {concurrency_limit}")
    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results, handling any exceptions that occurred
    results = []
    for i, result in enumerate(chunk_results):
        if isinstance(result, Exception):
            logger.error(f"Error processing chunk {i+1}: {result}")
            # Add error placeholders for this chunk
            results.extend([{"error": str(result), "raw_input": msg["raw"]} for msg in chunks[i]])
        else:
            results.extend(result)
    
    return results 