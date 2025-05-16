#!/usr/bin/env python
"""
Test local LLM integration with the Chat X-Ray Bot application.
"""
import asyncio
import json
from app.services.local_llm import analyse_chunk_with_llama, LocalLLM

# Test text for analysis
TEST_TEXT = """
Привет, как дела?
- Хорошо! А у тебя?
Отлично! Что делаешь?
- Просто отдыхаю, а ты?
Я работаю над новым проектом.
- Звучит интересно! Расскажи подробнее.
Это бот для анализа сообщений!
"""

async def test_llama_analysis():
    """Test the main Llama analysis function"""
    print("\n===== Testing analyse_chunk_with_llama =====")
    
    result = await analyse_chunk_with_llama(TEST_TEXT)
    print(f"Result type: {type(result)}")
    print("Analysis result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return isinstance(result, dict) and not result.get("error")

def test_local_llm_class():
    """Test the LocalLLM class"""
    print("\n===== Testing LocalLLM class =====")
    
    llm = LocalLLM()
    print(f"Testing availability: {llm.is_available()}")
    
    if llm.is_available():
        print("Testing generate function...")
        response = llm.generate("Привет, как тебя зовут?")
        print(f"Response: {response[:100]}...")
        return True
    
    return False

async def main():
    """Run all tests"""
    print("Starting local LLM integration tests...\n")
    
    # Test Llama analysis
    analysis_success = await test_llama_analysis()
    
    # Test LocalLLM class
    llm_class_success = test_local_llm_class()
    
    # Print final results
    print("\n===== Results =====")
    print(f"analyse_chunk_with_llama: {'✅ SUCCESS' if analysis_success else '❌ FAILED'}")
    print(f"LocalLLM class: {'✅ SUCCESS' if llm_class_success else '❌ FAILED'}")
    
    if analysis_success and llm_class_success:
        print("\nAll tests passed! Local LLM integration is working correctly.")
    else:
        print("\nSome tests failed. Check the output for details.")

if __name__ == "__main__":
    asyncio.run(main()) 