#!/usr/bin/env python3
import os
import requests
import sys
import time
from dotenv import load_dotenv
import subprocess
import logging
import argparse
from datetime import datetime

# Load environment variables
load_dotenv()

# Get the Render API key from environment or user input
api_key = os.environ.get("RENDER_API_KEY")
if not api_key:
    api_key = input("Enter your Render API key: ")

# The service ID for chat-xray-bot
service_id = "srv-d0i3t06mcj7s739m48r0"  # This is your service ID from previous conversations

# API endpoint for triggering a manual deploy
deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# According to Render API docs, the payload should be formatted as follows
payload = {
    "clearCache": True  # Clear cache to ensure fresh dependencies
}

print("=== Chat X-Ray Bot Redeployment Tool ===")
print("This script will:")
print("1. Delete the current webhook")
print("2. Redeploy the service on Render.com")
print("3. Set up a new webhook with drop_pending_updates=True")
print("\nStarting redeployment process...")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("redeploy")

def run_command(command, shell=True):
    """Run a shell command and return its output"""
    logger.info(f"Running command: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=shell, 
            check=True, 
            capture_output=True, 
            text=True
        )
        logger.info(f"Command output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Redeploy the bot with fixes")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating a backup before redeploying")
    parser.add_argument("--restart", action="store_true", help="Restart the bot service after redeploying")
    args = parser.parse_args()

    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Working directory: {current_dir}")

    # Create backup if needed
    if not args.no_backup:
        backup_dir = os.path.join(current_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"bot_py_backup_{timestamp}.py")
        
        logger.info(f"Creating backup of bot.py to {backup_file}")
        with open(os.path.join(current_dir, "app", "bot.py"), "r") as src, \
             open(backup_file, "w") as dst:
            dst.write(src.read())
        
        logger.info("Backup created successfully")

    # Check if we're running in a Docker container
    in_container = os.path.exists("/.dockerenv")
    
    if in_container:
        logger.info("Running in a Docker container")
        
        # Restart the bot service
        if args.restart:
            logger.info("Restarting the bot service")
            run_command("supervisorctl restart bot")
    else:
        logger.info("Running locally")
        
        # If we're running locally and restart was requested, start the bot
        if args.restart:
            logger.info("Starting the bot")
            run_command("python -m app.bot")

    logger.info("Redeployment completed successfully")

# Trigger the deploy with clear_cache=true
try:
    print(f"Triggering redeploy for service {service_id} with clear cache...")
    response = requests.post(
        deploy_url,
        headers=headers,
        json=payload
    )
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 201:
        deploy_data = response.json()
        deploy_id = deploy_data.get("id")
        print(f"✅ Successfully triggered redeploy with ID: {deploy_id}")
        print("Deployment is now in progress. This may take a few minutes.")
        print("\nNext steps:")
        print("1. Wait for the deployment to complete (check Render dashboard)")
        print("2. Run 'python check_webhook.py' to verify webhook configuration")
        print("3. Test your bot by sending a message in Telegram")
    else:
        print(f"❌ Failed to trigger redeploy: {response.status_code}")
        print(response.text)
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Check if webhook is properly set
print("\nWould you like to check the webhook status? (y/n)")
check_webhook = input("> ").lower()

if check_webhook == 'y':
    # Wait a bit for deployment to start
    print("Waiting 10 seconds before checking webhook...")
    time.sleep(10)
    
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
        print("\nWebhook information:")
        print(f"URL: {webhook_info.get('result', {}).get('url', 'Not set')}")
        print(f"Pending updates: {webhook_info.get('result', {}).get('pending_update_count', 0)}")
        
        if webhook_info.get('result', {}).get('last_error_date'):
            print(f"❌ Last error: {webhook_info.get('result', {}).get('last_error_message', 'Unknown error')}")
        else:
            print("✅ No recent webhook errors reported")
    except Exception as e:
        print(f"Error checking webhook: {e}")

print("\nRedeployment process initiated. Your bot should be operational soon.")
print("Remember to test the bot by sending a message in Telegram after deployment completes.")

if __name__ == "__main__":
    main() 