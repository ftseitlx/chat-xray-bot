#!/usr/bin/env python3
import os
import sys
import json
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

print("Testing OpenAI API connection...")

# Initialize the OpenAI client
client = openai.OpenAI(api_key=api_key)

try:
    # Make a simple request to check if the API key is valid
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'OpenAI API is working!' if you can read this."}
        ],
        max_tokens=20
    )
    
    print("✅ OpenAI API connection successful!")
    print(f"Response: {response.choices[0].message.content.strip()}")
    print("\nAPI key is valid and working properly.")
    
except Exception as e:
    print(f"❌ Error connecting to OpenAI API: {e}")
    print("\nPlease check your API key and make sure it's valid.")
    sys.exit(1) 