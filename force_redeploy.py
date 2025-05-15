#!/usr/bin/env python3

import os
import sys
import requests
import subprocess
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("force_redeploy")

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

def github_deploy():
    """Deploy via GitHub by committing and pushing changes"""
    logger.info("Deploying via GitHub...")
    
    # Check git status
    try:
        status = run_command("git status --porcelain")
        if status.strip():
            logger.info("Changes detected, committing...")
            
            # Add modified files
            run_command("git add app/bot.py")
            
            # Commit with a clear message
            run_command('git commit -m "Fix timeout context manager error in webhook handler [REDEPLOY]"')
            
            # Push to GitHub (assuming the branch is already set up properly)
            run_command("git push origin main")
            
            logger.info("✅ Successfully pushed changes to GitHub. A new deployment should be triggered automatically.")
            return True
        else:
            logger.info("No changes detected in git. Creating a dummy change to force deployment...")
            
            # Create a dummy change by updating a comment in bot.py
            run_command("""
                sed -i'' -e "s/TIMEOUT FIX VERSION 2025-05-14-001/TIMEOUT FIX VERSION 2025-05-14-$(date +%H%M%S)/g" app/bot.py
            """)
            
            # Add, commit and push the dummy change
            run_command("git add app/bot.py")
            run_command('git commit -m "Update version timestamp to force redeployment [REDEPLOY]"')
            run_command("git push origin main")
            
            logger.info("✅ Successfully pushed dummy change to GitHub. A new deployment should be triggered automatically.")
            return True
    except Exception as e:
        logger.error(f"❌ Error with GitHub deployment: {e}")
        return False

def force_redeploy():
    """Force a clean redeploy on Render.com using API"""
    # Get API key
    api_key = os.environ.get("RENDER_API_KEY")
    if not api_key:
        api_key = input("Enter your Render API key: ")
    
    # Get service ID
    service_id = os.environ.get("RENDER_SERVICE_ID", "srv-d0i3t06mcj7s739m48r0")
    
    # API endpoint for triggering a manual deploy
    deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Payload for clean cache deployment
    payload = {
        "clearCache": True  # Force clearing the cache to ensure fresh install
    }
    
    logger.info(f"Triggering FORCE REDEPLOY for service {service_id} with clean cache...")
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
            logger.info("\nNext steps:")
            logger.info("1. Wait for the deployment to complete (typically 2-5 minutes)")
            logger.info("2. Run 'python bot_status.py' to check if the fix is working")
            return True
        else:
            logger.error(f"❌ Failed to trigger redeploy: {response.status_code}")
            logger.error(response.text)
            return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

def fix_webhook():
    """Fix webhook configuration"""
    logger.info("Fixing webhook configuration...")
    
    try:
        # Use the existing fix_and_redeploy.py script with --webhook parameter
        run_command("python fix_and_redeploy.py --webhook")
        logger.info("✅ Successfully fixed webhook configuration")
        return True
    except Exception as e:
        logger.error(f"❌ Error fixing webhook: {e}")
        return False

if __name__ == "__main__":
    print("=======================================")
    print("  DEPLOYMENT HELPER")
    print("=======================================")
    print("1. Deploy via GitHub (commit & push changes)")
    print("2. Direct Render.com API deployment")
    print("3. Fix webhook configuration")
    print("4. All of the above in sequence")
    print("5. Exit")
    print()
    
    choice = input("Select an option (1-5): ")
    
    if choice == "1":
        github_deploy()
    elif choice == "2":
        force_redeploy()
    elif choice == "3":
        fix_webhook()
    elif choice == "4":
        github_deploy()
        force_redeploy()
        fix_webhook()
    else:
        print("Operation cancelled.") 