#!/usr/bin/env python3

import requests
import os
import json
import sys
from datetime import datetime, timedelta
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://chat-xray-bot.onrender.com")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID", "srv-d0i3t06mcj7s739m48r0")

def check_webhook_status():
    """Check the current webhook status"""
    print("Checking webhook status...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["ok"]:
            webhook_info = data["result"]
            print(f"\nWebhook URL: {webhook_info.get('url', 'Not set')}")
            print(f"Last Error Date: {webhook_info.get('last_error_date', 'None')}")
            if webhook_info.get('last_error_date'):
                error_date = datetime.fromtimestamp(webhook_info['last_error_date'])
                print(f"Last Error: {error_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Last Error Message: {webhook_info.get('last_error_message', 'None')}")
            
            print(f"Max Connections: {webhook_info.get('max_connections', 'Not set')}")
            print(f"Pending Updates: {webhook_info.get('pending_update_count', 0)}")
            
            # Check if webhook URL matches expected URL
            if webhook_info.get('url') == WEBHOOK_URL:
                print("\n✅ Webhook is correctly configured")
            else:
                print(f"\n⚠️ Webhook URL doesn't match expected URL: {WEBHOOK_URL}")
                
            # Check for recent errors (within last hour)
            if webhook_info.get('last_error_date'):
                error_time = datetime.fromtimestamp(webhook_info['last_error_date'])
                now = datetime.now()
                
                if (now - error_time) < timedelta(hours=1):
                    print(f"⚠️ Recent webhook error detected ({(now - error_time).seconds // 60} minutes ago)")
                    print(f"Error message: {webhook_info.get('last_error_message', 'Unknown error')}")
                else:
                    print("✅ No recent webhook errors")
                
            else:
                print("✅ No webhook errors reported")
                
        else:
            print(f"❌ Error checking webhook: {data.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

def check_bot_status():
    """Check if the bot is responding to the Telegram API"""
    print("\nChecking bot status with Telegram API...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["ok"]:
            bot_info = data["result"]
            print(f"✅ Bot is active and responding")
            print(f"Bot username: @{bot_info.get('username')}")
            print(f"Bot name: {bot_info.get('first_name')}")
            print(f"Bot ID: {bot_info.get('id')}")
        else:
            print(f"❌ Bot is not responding properly: {data.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

def view_local_logs():
    """View the most recent bot logs from the local log file"""
    print("\nChecking local log file...")
    log_file = "bot_log.txt"
    
    if not os.path.exists(log_file):
        print(f"❌ Log file '{log_file}' not found")
        return
        
    try:
        # Get the last 50 lines from the log file
        result = subprocess.run(
            ["tail", "-n", "50", log_file], 
            capture_output=True, 
            text=True
        )
        
        logs = result.stdout.strip()
        if not logs:
            print("No logs found or log file is empty")
            return
            
        print("\n--- Last 50 log entries ---")
        
        # Look for TIMEOUT-FIX markers and highlight them
        timeout_fix_logs = []
        for line in logs.split('\n'):
            if "[TIMEOUT-FIX]" in line:
                timeout_fix_logs.append(line)
                print(f"🔍 {line}")  # Highlight TIMEOUT-FIX logs
                
        if timeout_fix_logs:
            print(f"\n✅ Found {len(timeout_fix_logs)} entries with [TIMEOUT-FIX] markers")
            
            # Check for errors specifically related to timeout context manager
            timeout_errors = [line for line in logs.split('\n') 
                             if "Timeout context manager should be used inside a task" in line]
            
            if timeout_errors:
                print(f"⚠️ Found {len(timeout_errors)} timeout context manager errors in logs")
                for err in timeout_errors[:3]:  # Show up to 3 errors
                    print(f"  {err}")
            else:
                print("✅ No timeout context manager errors found in recent logs")
        else:
            print("\n⚠️ No [TIMEOUT-FIX] markers found in recent logs")
            print("Full log output:")
            print(logs)
            
    except Exception as e:
        print(f"❌ Exception viewing logs: {str(e)}")

def view_render_app_logs():
    """View logs from Render.com deployment"""
    if not RENDER_API_KEY:
        print("\n⚠️ RENDER_API_KEY not set in environment variables")
        return
        
    print("\nFetching logs from Render.com...")
    
    try:
        headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
        url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/logs"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch Render logs: {response.status_code}")
            print(response.text)
            return
            
        logs = response.json()
        
        # Filter for application logs
        app_logs = [log for log in logs if log.get("type") == "app"]
        
        if not app_logs:
            print("No application logs found in the response")
            return
            
        # Sort logs by timestamp (newest first)
        app_logs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Get last 20 app logs
        recent_logs = app_logs[:20]
        
        print("\n--- Last 20 application log entries from Render ---")
        for log in recent_logs:
            timestamp = datetime.fromtimestamp(log.get("timestamp", 0) / 1000)
            message = log.get("message", "")
            
            # Highlight TIMEOUT-FIX logs
            if "[TIMEOUT-FIX]" in message:
                print(f"🔍 {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {message}")
            else:
                print(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {message}")
        
        # Check for timeout errors
        timeout_errors = [log for log in app_logs 
                         if "Timeout context manager should be used inside a task" in log.get("message", "")]
        
        if timeout_errors:
            print(f"\n⚠️ Found {len(timeout_errors)} timeout context manager errors in logs")
            for err in timeout_errors[:3]:  # Show up to 3 errors
                timestamp = datetime.fromtimestamp(err.get("timestamp", 0) / 1000)
                print(f"  {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {err.get('message', '')}")
        else:
            print("\n✅ No timeout context manager errors found in recent logs")
            
    except Exception as e:
        print(f"❌ Exception fetching Render logs: {str(e)}")

def send_test_message():
    """Send a test message to the bot using Telegram API"""
    print("\nWould you like to send a test message to the bot? (y/n)")
    response = input("> ")
    
    if response.lower() != 'y':
        return
        
    print("Enter your Telegram chat ID:")
    chat_id = input("> ")
    
    if not chat_id:
        print("❌ Chat ID is required")
        return
        
    print("\nSending test message...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        payload = {
            "chat_id": chat_id,
            "text": f"Test message from bot_status.py script\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nThis message confirms the bot is operational."
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if data["ok"]:
            print("✅ Test message sent successfully")
        else:
            print(f"❌ Failed to send test message: {data.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception sending test message: {str(e)}")

def send_test_document():
    """Send a test document to the bot to test the file handling and timeout fix"""
    print("\nWould you like to send a test document to the bot? (y/n)")
    response = input("> ")
    
    if response.lower() != 'y':
        return
        
    print("Enter your Telegram chat ID:")
    chat_id = input("> ")
    
    if not chat_id:
        print("❌ Chat ID is required")
        return
        
    print("\nCreating a test document...")
    
    # Create a temporary test file
    test_file_path = "test_document.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test document to verify the timeout fix.\n")
        f.write(f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("If you're seeing this in a chat response, the document was processed successfully!\n")
        f.write("\nThe following messages should appear in logs with [TIMEOUT-FIX] markers if the fix is working:\n")
        f.write("1. Webhook handler starting\n")
        f.write("2. Document handling in task\n")
        f.write("3. Safe message sending\n")
    
    print("\nSending test document...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    
    try:
        with open(test_file_path, "rb") as document:
            files = {"document": document}
            data = {"chat_id": chat_id, "caption": "Test document to verify timeout fix"}
            
            response = requests.post(url, data=data, files=files)
            result = response.json()
            
            if result["ok"]:
                print("✅ Test document sent successfully")
                print("The bot should now process this document. Check the logs for [TIMEOUT-FIX] markers.")
                print("You can run this script again in a few minutes to check the logs.")
            else:
                print(f"❌ Failed to send test document: {result.get('description', 'Unknown error')}")
                
        # Clean up
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            
    except Exception as e:
        print(f"❌ Exception sending test document: {str(e)}")
        # Clean up
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def main():
    """Main function to coordinate all status checks"""
    print("===== BOT STATUS CHECK =====")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("===========================\n")
    
    check_webhook_status()
    check_bot_status()
    view_local_logs()
    view_render_app_logs()
    send_test_message()
    send_test_document()
    
    print("\n===== STATUS CHECK COMPLETE =====")

if __name__ == "__main__":
    main() 