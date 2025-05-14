#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the bot token
bot_token = os.getenv("BOT_TOKEN")

if not bot_token:
    print("Error: BOT_TOKEN not found in environment variables")
    sys.exit(1)

# Get the chat ID from command line or ask for it
if len(sys.argv) > 1:
    chat_id = sys.argv[1]
else:
    chat_id = input("Enter your Telegram chat ID: ")

# Path to the test file
test_file_path = "test_chat.txt"

if not os.path.exists(test_file_path):
    print(f"Error: Test file not found at {test_file_path}")
    sys.exit(1)

print(f"Sending test file to bot (chat ID: {chat_id})...")

# Send a message to the bot first
send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
message_params = {
    "chat_id": chat_id,
    "text": "Testing file upload capability. Sending a test chat file..."
}

try:
    response = requests.post(send_message_url, data=message_params)
    response.raise_for_status()
    print("✅ Test message sent successfully")
except Exception as e:
    print(f"❌ Error sending test message: {e}")
    sys.exit(1)

# Send the test file to the bot
send_document_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

try:
    with open(test_file_path, "rb") as file:
        files = {"document": file}
        params = {"chat_id": chat_id}
        response = requests.post(send_document_url, data=params, files=files)
        response.raise_for_status()
        
    print("✅ Test file sent successfully")
    print("Check your Telegram client to see if the bot responds to the file upload.")
    print("If the bot doesn't respond, there might be an issue with the file processing code.")
except Exception as e:
    print(f"❌ Error sending test file: {e}")
    sys.exit(1) 