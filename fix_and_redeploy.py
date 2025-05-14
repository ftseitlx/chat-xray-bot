#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import argparse
from datetime import datetime
import time
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("redeploy")

# Load environment variables
load_dotenv()

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

def check_webhook_status(bot_token):
    """Check and print the webhook status"""
    logger.info("Checking webhook status...")
    
    # Make a request to the Telegram API to get webhook info
    webhook_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(webhook_url)
        response.raise_for_status()
        
        webhook_info = response.json()
        logger.info("\nWebhook information:")
        logger.info(f"URL: {webhook_info.get('result', {}).get('url', 'Not set')}")
        logger.info(f"Pending updates: {webhook_info.get('result', {}).get('pending_update_count', 0)}")
        
        if webhook_info.get('result', {}).get('last_error_date'):
            logger.warning(f"❌ Last error: {webhook_info.get('result', {}).get('last_error_message', 'Unknown error')}")
        else:
            logger.info("✅ No recent webhook errors reported")
        
        return webhook_info
    except Exception as e:
        logger.error(f"Error checking webhook: {e}")
        return None

def delete_webhook(bot_token, drop_pending=True):
    """Delete the current webhook"""
    logger.info(f"Deleting webhook with drop_pending={drop_pending}...")
    
    # Make a request to delete the webhook
    delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    params = {"drop_pending_updates": "true" if drop_pending else "false"}
    
    try:
        response = requests.get(delete_url, params=params)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            logger.info("✅ Webhook deleted successfully")
            return True
        else:
            logger.error(f"❌ Failed to delete webhook: {result.get('description')}")
            return False
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return False

def set_webhook(bot_token, webhook_url, drop_pending=True):
    """Set a new webhook"""
    logger.info(f"Setting webhook to {webhook_url} with drop_pending={drop_pending}...")
    
    # Make a request to set the webhook
    set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    params = {
        "url": webhook_url,
        "drop_pending_updates": "true" if drop_pending else "false"
    }
    
    try:
        response = requests.get(set_url, params=params)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            logger.info("✅ Webhook set successfully")
            return True
        else:
            logger.error(f"❌ Failed to set webhook: {result.get('description')}")
            return False
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False

def main():
    """Main function to fix and redeploy the bot"""
    parser = argparse.ArgumentParser(description="Fix and redeploy the Telegram bot")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating a backup before redeploying")
    parser.add_argument("--restart", action="store_true", help="Restart the bot service after redeploying")
    parser.add_argument("--webhook", action="store_true", help="Fix webhook configuration")
    parser.add_argument("--render-deploy", action="store_true", help="Trigger a Render.com redeploy")
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

    # Handle webhook management if requested
    if args.webhook:
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("Error: BOT_TOKEN not found in environment variables")
            sys.exit(1)
        
        webhook_host = os.getenv("WEBHOOK_HOST")
        webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
        
        if not webhook_host:
            webhook_host = os.getenv("RENDER_EXTERNAL_URL")
            
        if not webhook_host:
            logger.error("Error: Neither WEBHOOK_HOST nor RENDER_EXTERNAL_URL found in environment variables")
            sys.exit(1)
            
        webhook_url = f"{webhook_host}{webhook_path}"
        
        # First check current webhook status
        check_webhook_status(bot_token)
        
        # Delete current webhook
        delete_webhook(bot_token, drop_pending=True)
        
        # Wait a bit before setting new webhook
        time.sleep(1)
        
        # Set new webhook
        set_webhook(bot_token, webhook_url, drop_pending=True)
        
        # Check webhook status again
        check_webhook_status(bot_token)

    # Trigger Render.com deployment if requested
    if args.render_deploy:
        # Get the Render API key from environment or user input
        api_key = os.environ.get("RENDER_API_KEY")
        if not api_key:
            api_key = input("Enter your Render API key: ")
        
        # The service ID for chat-xray-bot
        service_id = os.environ.get("RENDER_SERVICE_ID", "srv-d0i3t06mcj7s739m48r0")
        
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
        
        logger.info(f"Triggering redeploy for service {service_id} with clear cache...")
        try:
            response = requests.post(
                deploy_url,
                headers=headers,
                json=payload
            )
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 201:
                deploy_data = response.json()
                deploy_id = deploy_data.get("id")
                logger.info(f"✅ Successfully triggered redeploy with ID: {deploy_id}")
                logger.info("Deployment is now in progress. This may take a few minutes.")
            else:
                logger.error(f"❌ Failed to trigger redeploy: {response.status_code}")
                logger.error(response.text)
        except Exception as e:
            logger.error(f"❌ Error: {e}")

    # Check if we're running in a Docker container
    in_container = os.path.exists("/.dockerenv")
    
    # Restart the bot if requested
    if args.restart:
        if in_container:
            logger.info("Running in a Docker container")
            logger.info("Restarting the bot service")
            run_command("supervisorctl restart bot")
        else:
            logger.info("Running locally")
            logger.info("Starting the bot")
            run_command("python -m app.bot")

    logger.info("Fix and redeploy process completed successfully")

if __name__ == "__main__":
    main() 