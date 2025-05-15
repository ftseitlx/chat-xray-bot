#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv
import tempfile
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Get bot token from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in environment variables")
    exit(1)

def create_test_document():
    """Creates a test document file for uploading to the bot"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write("This is a test document to verify the timeout fix.\n\n")
            f.write(f"Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam in dui mauris.\n")
            f.write("Vivamus hendrerit arcu sed erat molestie vehicula. Sed auctor neque eu tellus\n")
            f.write("rhoncus ut eleifend nibh porttitor. Ut in nulla enim. Phasellus molestie magna.\n")
            # Add more sample text to make it look like a chat
            f.write("\n[2025-05-13 12:00:15] User 1: Hello, how are you today?\n")
            f.write("[2025-05-13 12:01:23] User 2: I'm doing well, thanks for asking! How about you?\n")
            f.write("[2025-05-13 12:03:05] User 1: Great! I've been meaning to talk to you about our project.\n")
            f.write("[2025-05-13 12:05:42] User 2: Sure, what's on your mind?\n")
            # Add more lines to simulate a chat history
            for i in range(1, 30):
                f.write(f"[2025-05-13 {12+i//10}:{i%10*5}:00] User {i%2+1}: This is line {i} of the test chat history.\n")
            
        return path
    except Exception as e:
        print(f"Error creating test document: {e}")
        os.unlink(path)
        return None

def send_test_document(chat_id, document_path):
    """Sends a test document to the specified chat ID"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    
    try:
        with open(document_path, 'rb') as doc:
            files = {'document': doc}
            data = {
                'chat_id': chat_id,
                'caption': 'Test document for timeout fix verification',
                'parse_mode': 'HTML'
            }
            
            print(f"Sending document to chat ID {chat_id}...")
            response = requests.post(url, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Document sent successfully!")
                    print("Now watch for the bot's response...")
                    return True
                else:
                    print(f"❌ API Error: {result.get('description')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return False

def main():
    print("=======================================")
    print("  DOCUMENT UPLOAD TEST SCRIPT")
    print("=======================================")
    print("This script will send a test document to your Telegram bot")
    print("to verify that the timeout fix is working correctly.")
    print()
    
    # Get chat ID from user
    chat_id = input("Enter your Telegram chat ID: ")
    if not chat_id:
        print("Chat ID is required.")
        return
    
    # Create test document
    print("Creating test document...")
    document_path = create_test_document()
    if not document_path:
        print("Failed to create test document.")
        return
    
    print(f"Test document created at: {document_path}")
    
    try:
        # Send document
        success = send_test_document(chat_id, document_path)
        
        if success:
            print("\nDocument sent successfully!")
            print("\nWatch for the bot's response. If the timeout fix is working,")
            print("the bot should acknowledge receipt of the document and start processing it.")
            print("\nIf you see an error message or no response, the fix might not be deployed yet.")
            print("\nRemember that it can take several minutes for GitHub deployments to complete on Render.")
            
            # Wait to see if the bot responds
            print("\nWaiting 30 seconds for response...")
            for i in range(30, 0, -5):
                print(f"{i} seconds remaining...")
                time.sleep(5)
                
            print("\nCheck your Telegram chat to see if the bot responded.")
            print("If it did, the timeout fix is working correctly! 🎉")
    finally:
        # Clean up
        if document_path and os.path.exists(document_path):
            os.unlink(document_path)
            print(f"Removed temporary file: {document_path}")

if __name__ == "__main__":
    main() 