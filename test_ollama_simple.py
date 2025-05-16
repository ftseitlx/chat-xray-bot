#!/usr/bin/env python
"""
Simple test for Ollama API without app dependencies
"""
import httpx
import asyncio
import json
import logging
import re
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# Simple Russian system prompt
SYSTEM_PROMPT = (
    "Ты психолог-аналитик. На входе тебе приходит фрагмент переписки. "
    "Верни ТОЛЬКО валидный JSON c ключами: sentiment_score, toxicity, manipulation, "
    "empathy, assertiveness, emotion_intensity, communication_pattern, gottman_horsemen, key_quotes. "
    "Числовые поля – float от 0 до 1 (или -1…1 где уместно). key_quotes – массив до 3 строк."
)

TEST_TEXT = """
Привет, как дела?
- Хорошо! А у тебя?
Отлично! Что делаешь?
- Просто отдыхаю, а ты?
Я работаю над новым проектом.
- Звучит интересно! Расскажи подробнее.
Это бот для анализа сообщений!
"""

async def test_ollama_chat_streaming():
    """Test the Ollama chat endpoint with streaming response"""
    print(f"Testing Ollama chat endpoint with model {OLLAMA_MODEL} (streaming)")
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": TEST_TEXT[:4096]},
        ],
        "temperature": 0.3,
        "stream": True
    }
    
    try:
        url = f"{OLLAMA_URL}/api/chat"
        print(f"Sending streaming request to: {url}")
        
        async with httpx.AsyncClient(timeout=60) as client:
            print("Starting streaming request...")
            
            full_content = ""
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code == 200:
                    print("Stream started successfully!")
                    async for chunk in response.aiter_text():
                        # Each chunk is a JSON object
                        try:
                            chunk_data = json.loads(chunk)
                            content = chunk_data.get("message", {}).get("content", "")
                            full_content += content
                            print(".", end="", flush=True)
                        except json.JSONDecodeError:
                            print(f"Failed to parse chunk: {chunk[:50]}...")
                else:
                    print(f"Stream failed with status: {response.status_code}")
                    return None
            
            print("\nStreaming complete!")
            print(f"Full content length: {len(full_content)}")
            
            # Try to extract JSON from the full content
            json_pattern = r'```json\s*(.*?)\s*```|```\s*(.*?)\s*```|\{.*\}'
            match = re.search(json_pattern, full_content, re.DOTALL)
            
            if match:
                json_str = match.group(1) or match.group(2) or match.group(0)
                json_str = json_str.strip()
                
                # If it's wrapped in backticks without json specifier, remove them
                if json_str.startswith('```') and json_str.endswith('```'):
                    json_str = json_str[3:-3].strip()
                
                try:
                    result = json.loads(json_str)
                    print("\nFinal parsed result:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    return result
                except json.JSONDecodeError as e:
                    print(f"Failed to parse extracted JSON: {e}")
                    print(f"JSON string: {json_str[:200]}...")
            else:
                print("No JSON found in response")
                print(f"Full content: {full_content[:500]}...")
                
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    """Run all tests"""
    print("Starting simple Ollama streaming test...")
    
    result = await test_ollama_chat_streaming()
    
    if result:
        print("\n✅ Test successful! Ollama streaming is working correctly.")
    else:
        print("\n❌ Test failed. Check the output for details.")

if __name__ == "__main__":
    asyncio.run(main()) 