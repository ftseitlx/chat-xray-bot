import logging
import os
import time
from datetime import datetime
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


async def clean_old_uploads(hours: int = 1):
    """
    Delete upload files older than the specified number of hours.
    
    Args:
        hours: Number of hours after which files should be deleted
    """
    logger.info(f"Running cleanup of uploads older than {hours} hours")
    
    try:
        current_time = time.time()
        upload_dir = settings.UPLOAD_DIR
        count_deleted = 0
        
        # Walk through upload directory
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            
            # Check if it's a file (not a directory)
            if os.path.isfile(file_path):
                # Check for metadata file
                meta_file = f"{file_path}.meta"
                
                try:
                    if os.path.exists(meta_file):
                        # Read the expiration timestamp from metadata
                        with open(meta_file, "r") as f:
                            expiration_time = float(f.read().strip())
                        
                        # Delete if expired
                        if current_time > expiration_time:
                            os.unlink(file_path)
                            os.unlink(meta_file)
                            count_deleted += 1
                    else:
                        # If no metadata, use file creation time
                        file_age_hours = (current_time - os.path.getctime(file_path)) / 3600
                        
                        if file_age_hours > hours:
                            os.unlink(file_path)
                            count_deleted += 1
                
                except (ValueError, OSError) as e:
                    logger.error(f"Error processing file {file_path}: {e}")
        
        logger.info(f"Cleanup complete. Deleted {count_deleted} files from uploads directory.")
    
    except Exception as e:
        logger.exception(f"Error during uploads cleanup: {e}")


async def clean_old_reports(hours: int = 72):
    """
    Delete report files older than the specified number of hours.
    
    Args:
        hours: Number of hours after which files should be deleted
    """
    logger.info(f"Running cleanup of reports older than {hours} hours")
    
    try:
        current_time = time.time()
        report_dir = settings.REPORT_DIR
        count_deleted = 0
        
        # Walk through reports directory
        for filename in os.listdir(report_dir):
            file_path = os.path.join(report_dir, filename)
            
            # Skip metadata files, we'll delete them with their main files
            if filename.endswith('.meta'):
                continue
                
            # Check if it's a file (not a directory)
            if os.path.isfile(file_path):
                # Check for metadata file
                meta_file = f"{file_path}.meta"
                
                try:
                    if os.path.exists(meta_file):
                        # Read the expiration timestamp from metadata
                        with open(meta_file, "r") as f:
                            expiration_time = float(f.read().strip())
                        
                        # Delete if expired
                        if current_time > expiration_time:
                            os.unlink(file_path)
                            os.unlink(meta_file)
                            count_deleted += 1
                            
                            # Also delete the corresponding HTML file if PDF
                            if file_path.endswith('.pdf'):
                                html_path = file_path.replace('.pdf', '.html')
                                if os.path.exists(html_path):
                                    os.unlink(html_path)
                    else:
                        # If no metadata, use file creation time
                        file_age_hours = (current_time - os.path.getctime(file_path)) / 3600
                        
                        if file_age_hours > hours:
                            os.unlink(file_path)
                            count_deleted += 1
                            
                            # Also delete the corresponding HTML file if PDF
                            if file_path.endswith('.pdf'):
                                html_path = file_path.replace('.pdf', '.html')
                                if os.path.exists(html_path):
                                    os.unlink(html_path)
                
                except (ValueError, OSError) as e:
                    logger.error(f"Error processing file {file_path}: {e}")
        
        logger.info(f"Cleanup complete. Deleted {count_deleted} files from reports directory.")
    
    except Exception as e:
        logger.exception(f"Error during reports cleanup: {e}")


if __name__ == "__main__":
    # This allows the script to be run directly for manual cleanup
    import asyncio
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run both cleanup functions
    asyncio.run(clean_old_uploads(hours=settings.UPLOAD_RETENTION_HOURS))
    asyncio.run(clean_old_reports(hours=settings.REPORT_RETENTION_HOURS)) 