#!/usr/bin/env python3
import os
import requests
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the bot token
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    print("Error: BOT_TOKEN not found in environment variables")
    sys.exit(1)

# Telegram API base URL
api_base = f"https://api.telegram.org/bot{bot_token}"

# Webhook URL from environment or Render
webhook_host = os.environ.get("WEBHOOK_HOST") or os.environ.get("RENDER_EXTERNAL_URL")
webhook_path = os.environ.get("WEBHOOK_PATH", "/webhook")

if not webhook_host:
    print("Error: WEBHOOK_HOST or RENDER_EXTERNAL_URL not found in environment variables")
    print("Please set one of these variables to your service URL")
    sys.exit(1)

webhook_url = f"{webhook_host}{webhook_path}"

print("=== Telegram Bot Webhook Reset Tool ===")
print(f"Bot Token: {bot_token[:5]}...{bot_token[-5:]}")
print(f"Webhook URL: {webhook_url}")

# First, check current webhook status
print("\n1. Checking current webhook status...")
try:
    response = requests.get(f"{api_base}/getWebhookInfo")
    response.raise_for_status()
    webhook_info = response.json()
    
    if webhook_info.get("ok"):
        current_url = webhook_info.get("result", {}).get("url", "Not set")
        pending_updates = webhook_info.get("result", {}).get("pending_update_count", 0)
        
        print(f"Current webhook URL: {current_url}")
        print(f"Pending updates: {pending_updates}")
        
        if webhook_info.get("result", {}).get("last_error_date"):
            last_error = webhook_info.get("result", {}).get("last_error_message", "Unknown error")
            print(f"Last error: {last_error}")
    else:
        print("Failed to get webhook info")
        print(webhook_info)
except Exception as e:
    print(f"Error checking webhook: {e}")
    sys.exit(1)

# Ask for confirmation
print("\nDo you want to reset the webhook? This will:")
print("1. Delete the current webhook (drop all pending updates)")
print("2. Set a new webhook to the URL specified above")
print("\nContinue? (y/n)")
confirm = input("> ").lower()

if confirm != "y":
    print("Operation cancelled")
    sys.exit(0)

# Step 1: Delete the current webhook
print("\n2. Deleting current webhook...")
try:
    response = requests.post(f"{api_base}/deleteWebhook", json={"drop_pending_updates": True})
    response.raise_for_status()
    delete_result = response.json()
    
    if delete_result.get("ok"):
        print("✅ Webhook deleted successfully")
    else:
        print(f"❌ Failed to delete webhook: {delete_result}")
        sys.exit(1)
except Exception as e:
    print(f"Error deleting webhook: {e}")
    sys.exit(1)

# Wait a moment
print("Waiting 2 seconds...")
time.sleep(2)

# Step 2: Set a new webhook
print("\n3. Setting new webhook...")
try:
    # Set allowed updates to only message to reduce load
    allowed_updates = ["message"]
    
    response = requests.post(
        f"{api_base}/setWebhook",
        json={
            "url": webhook_url,
            "allowed_updates": allowed_updates,
            "drop_pending_updates": True,
            "max_connections": 40
        }
    )
    response.raise_for_status()
    set_result = response.json()
    
    if set_result.get("ok"):
        print(f"✅ Webhook set successfully to: {webhook_url}")
        print(f"Allowed updates: {allowed_updates}")
    else:
        print(f"❌ Failed to set webhook: {set_result}")
        sys.exit(1)
except Exception as e:
    print(f"Error setting webhook: {e}")
    sys.exit(1)

# Final check
print("\n4. Verifying new webhook configuration...")
try:
    response = requests.get(f"{api_base}/getWebhookInfo")
    response.raise_for_status()
    webhook_info = response.json()
    
    if webhook_info.get("ok"):
        current_url = webhook_info.get("result", {}).get("url", "Not set")
        allowed_updates = webhook_info.get("result", {}).get("allowed_updates", [])
        
        print(f"Current webhook URL: {current_url}")
        print(f"Allowed updates: {allowed_updates}")
        
        if current_url == webhook_url:
            print("\n✅ Webhook reset successful!")
        else:
            print("\n❌ Webhook URL mismatch. Please check configuration.")
    else:
        print("Failed to get webhook info")
        print(webhook_info)
except Exception as e:
    print(f"Error checking webhook: {e}")

print("\nWebhook reset complete. Your bot should now be able to receive messages.")
print("Test your bot by sending a message in Telegram.") 