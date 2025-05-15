#!/usr/bin/env python3

import os
import sys
import requests
from dotenv import load_dotenv
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("check_deployment")

# Load environment variables
load_dotenv()

def check_render_deployment():
    """Check the status of the latest deployment on Render.com"""
    api_key = os.environ.get("RENDER_API_KEY")
    if not api_key:
        api_key = input("Enter your Render API key: ")
    
    service_id = os.environ.get("RENDER_SERVICE_ID", "srv-d0i3t06mcj7s739m48r0")
    
    # API endpoint for getting deploys
    deploys_url = f"https://api.render.com/v1/services/{service_id}/deploys"
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    logger.info(f"Checking deployment status for service {service_id}...")
    try:
        response = requests.get(
            deploys_url,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get deployment status: {response.status_code}")
            logger.error(response.text)
            return False
            
        deploys = response.json()
        
        if not deploys:
            logger.info("No deployments found.")
            return False
            
        # Get the latest deployment
        latest_deploy = deploys[0]
        
        # Print status information
        logger.info(f"Latest deployment ID: {latest_deploy.get('id')}")
        
        # Convert createdAt to datetime
        created_at = datetime.fromtimestamp(latest_deploy.get('createdAt') / 1000) if latest_deploy.get('createdAt') else None
        updated_at = datetime.fromtimestamp(latest_deploy.get('updatedAt') / 1000) if latest_deploy.get('updatedAt') else None
        
        if created_at:
            logger.info(f"Created at: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if updated_at:
            logger.info(f"Last updated: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
        logger.info(f"Status: {latest_deploy.get('status')}")
        
        if latest_deploy.get('status') == 'live':
            logger.info("✅ Deployment is LIVE!")
            
            # Check if deployment is recent (within the last 10 minutes)
            if updated_at and (datetime.now() - updated_at).total_seconds() < 600:
                logger.info("✅ This is a recent deployment (within the last 10 minutes)")
            else:
                logger.info("⚠️ This deployment is not recent. You might need to trigger a new deployment.")
        elif latest_deploy.get('status') == 'build_in_progress':
            logger.info("⏳ Deployment is currently being built...")
        elif latest_deploy.get('status') == 'update_in_progress':
            logger.info("⏳ Deployment update is in progress...")
        else:
            logger.info(f"⚠️ Deployment status: {latest_deploy.get('status')}")
            
        # Check for commit information
        if latest_deploy.get('commit'):
            commit = latest_deploy.get('commit')
            logger.info(f"Commit: {commit.get('message', 'No commit message')}")
            logger.info(f"Commit ID: {commit.get('id', 'No commit ID')}")
            
        return True
    except Exception as e:
        logger.error(f"Error checking deployment status: {e}")
        return False

def check_log_for_version():
    """Check the log for the latest version marker"""
    api_key = os.environ.get("RENDER_API_KEY")
    if not api_key:
        api_key = input("Enter your Render API key: ")
    
    service_id = os.environ.get("RENDER_SERVICE_ID", "srv-d0i3t06mcj7s739m48r0")
    
    logs_url = f"https://api.render.com/v1/services/{service_id}/logs"
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    logger.info("Checking logs for version marker...")
    try:
        response = requests.get(
            logs_url,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get logs: {response.status_code}")
            logger.error(response.text)
            return False
            
        logs = response.json()
        
        # Check for the version marker
        version_logs = [log for log in logs if 'TIMEOUT FIX VERSION' in log.get('message', '')]
        
        if version_logs:
            # Sort by timestamp, most recent first
            version_logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            latest_version_log = version_logs[0]
            message = latest_version_log.get('message', '')
            
            # Extract version string
            import re
            version_match = re.search(r'TIMEOUT FIX VERSION ([^\ ]+)', message)
            if version_match:
                version = version_match.group(1)
                logger.info(f"✅ Found version marker in logs: {version}")
                
                # Check if this is the latest version (should have 001 in it)
                if '001' in version or any(c.isdigit() for c in version):
                    logger.info("✅ This appears to be the updated version!")
                else:
                    logger.info("⚠️ This might not be the latest version.")
            else:
                logger.info(f"✅ Found version marker but couldn't extract version: {message}")
            
            # Get timestamp
            timestamp = datetime.fromtimestamp(latest_version_log.get('timestamp') / 1000) if latest_version_log.get('timestamp') else None
            if timestamp:
                logger.info(f"Log timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Check if log is recent (within the last 10 minutes)
                if (datetime.now() - timestamp).total_seconds() < 600:
                    logger.info("✅ This log is recent (within the last 10 minutes)")
                else:
                    logger.info("⚠️ This log is not recent. You might need to trigger a new deployment.")
            
            # Check for timeout error logs
            timeout_logs = [log for log in logs if 'Timeout context manager should be used inside a task' in log.get('message', '')]
            
            if timeout_logs:
                # Sort by timestamp, most recent first
                timeout_logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                latest_timeout_log = timeout_logs[0]
                
                timeout_timestamp = datetime.fromtimestamp(latest_timeout_log.get('timestamp') / 1000) if latest_timeout_log.get('timestamp') else None
                
                if timeout_timestamp:
                    logger.info(f"⚠️ Found timeout error in logs at: {timeout_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Check if timeout is more recent than our version marker
                    if timestamp and timeout_timestamp > timestamp:
                        logger.info("❌ ALERT: Timeout error is MORE RECENT than our version marker!")
                        logger.info("This might indicate the fix has not been properly deployed.")
                    else:
                        logger.info("✅ Timeout error is OLDER than our version marker. Fix should be working!")
            else:
                logger.info("✅ No recent timeout errors found in logs!")
                
            return True
        else:
            logger.info("❌ No version marker found in logs. The new version might not be deployed yet.")
            return False
    except Exception as e:
        logger.error(f"Error checking logs: {e}")
        return False

def main():
    """Main function to check deployment status"""
    print("=======================================")
    print("  DEPLOYMENT STATUS CHECKER")
    print("=======================================")
    
    if not os.environ.get("RENDER_API_KEY"):
        api_key = input("Enter your Render API key: ")
        os.environ["RENDER_API_KEY"] = api_key
    
    print("\nChecking deployment status...")
    check_render_deployment()
    
    print("\nChecking logs for version marker...")
    check_log_for_version()
    
    print("\nDeployment status check complete.")
    print("If the deployment is not yet complete, you can wait a few minutes and run this script again.")
    print("You can also run test_document_upload.py to test if the fix is working.")

if __name__ == "__main__":
    main() 