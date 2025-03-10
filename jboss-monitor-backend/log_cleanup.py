# log_cleanup.py
import os
import time
import threading
import logging
from datetime import datetime, timedelta
import glob
from config import Config

logger = logging.getLogger(__name__)

def cleanup_old_logs():
    """Clean up log files older than Config.LOG_MAX_DAYS days"""
    log_dir = Config.LOG_DIR
    max_days = Config.LOG_MAX_DAYS
    
    try:
        if not os.path.exists(log_dir):
            logger.warning(f"Log directory {log_dir} does not exist. Skipping cleanup.")
            return
            
        current_time = datetime.now()
        deleted_count = 0
        total_size_freed = 0
        
        # Find all log files in the directory
        for file_path in glob.glob(os.path.join(log_dir, '*.log*')):
            try:
                # Get file modification time
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                # Calculate age in days
                age_days = (current_time - file_time).days
                
                # If file is older than max_days, delete it
                if age_days > max_days:
                    # Get file size before deleting
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        file_size = 0
                        
                    # Delete the file
                    os.remove(file_path)
                    deleted_count += 1
                    total_size_freed += file_size
                    logger.info(f"Deleted old log file: {file_path} (age: {age_days} days, size: {file_size/1024:.2f} KB)")
            except Exception as e:
                logger.error(f"Error processing log file {file_path}: {str(e)}")
        
        if deleted_count > 0:
            logger.info(f"Log cleanup completed: Removed {deleted_count} files, freed {total_size_freed/1024/1024:.2f} MB")
        else:
            logger.info(f"Log cleanup completed: No files needed to be removed")
            
    except Exception as e:
        logger.error(f"Error during log cleanup: {str(e)}")

def start_log_cleanup_worker():
    """Start a background thread to periodically clean up old log files"""
    
    def run_cleanup():
        logger.info("Starting log cleanup worker")
        
        while True:
            try:
                # Run cleanup
                cleanup_old_logs()
                
                # Wait for next cleanup (once per day at 2 AM)
                now = datetime.now()
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                # If it's already past 2 AM, schedule for tomorrow
                if now.hour >= 2:
                    next_run = next_run + timedelta(days=1)
                
                # Calculate seconds until next run
                sleep_seconds = (next_run - now).total_seconds()
                
                # Make sure we don't have a negative sleep time
                if sleep_seconds <= 0:
                    sleep_seconds = 86400  # 24 hours
                
                logger.info(f"Next log cleanup scheduled for {next_run} (in {sleep_seconds/3600:.2f} hours)")
                
                # Sleep until next cleanup time
                time.sleep(sleep_seconds)
                
            except Exception as e:
                logger.error(f"Error in log cleanup worker: {str(e)}")
                # If there's an error, wait 1 hour before retrying
                time.sleep(3600)
    
    # Create and start the cleanup thread
    cleanup_thread = threading.Thread(target=run_cleanup)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    return cleanup_thread
