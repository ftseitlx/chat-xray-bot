#!/usr/bin/env python3
import os
import requests
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the bot token
bot_token = os.getenv("BOT_TOKEN")

if not bot_token:
    print("Error: BOT_TOKEN not found in environment variables")
    sys.exit(1)

# Make a request to the Telegram API to get webhook info
webhook_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"

try:
    response = requests.get(webhook_url)
    response.raise_for_status()
    
    webhook_info = response.json()
    print("Webhook information:")
    print(json.dumps(webhook_info, indent=2))
    
    # Check if webhook is set
    if webhook_info.get("ok") and webhook_info.get("result", {}).get("url"):
        print("\n✅ Webhook is set up correctly")
        webhook_url = webhook_info["result"]["url"]
        print(f"Current webhook URL: {webhook_url}")
        
        # Check if the webhook URL points to our Render service
        if "chat-xray-bot.onrender.com" in webhook_url:
            print("✅ Webhook points to the correct Render service")
        else:
            print("❌ Webhook does not point to chat-xray-bot.onrender.com")
            
        # Check for pending updates
        pending_updates = webhook_info["result"].get("pending_update_count", 0)
        print(f"Pending updates: {pending_updates}")
        
        # Check for errors
        if webhook_info["result"].get("last_error_date"):
            last_error_date = webhook_info["result"]["last_error_date"]
            last_error_message = webhook_info["result"].get("last_error_message", "Unknown error")
            print(f"❌ Last webhook error: {last_error_message}")
            print(f"   Error occurred at: {last_error_date}")
        else:
            print("✅ No recent webhook errors reported")
    else:
        print("\n❌ Webhook is not set up")
        
except Exception as e:
    print(f"Error checking webhook: {e}")
    sys.exit(1) 