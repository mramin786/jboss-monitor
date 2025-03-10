# reports/cleanup.py
import os
import time
import threading
import logging
from datetime import datetime, timedelta
from config import Config
from reports.utils import rotate_reports

logger = logging.getLogger(__name__)

def cleanup_old_reports():
    """Clean up old reports to maintain storage limits"""
    try:
        # Rotate reports for all environments
        deleted_count = rotate_reports(environment=None, max_reports=Config.MAX_REPORTS_PER_ENV)
        logger.info(f"Reports cleanup completed: Removed {deleted_count} reports")
    except Exception as e:
        logger.error(f"Error during reports cleanup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def start_reports_cleanup_worker():
    """Start a background thread to periodically clean up old reports"""
    
    def run_cleanup():
        logger.info("Starting reports cleanup worker")
        
        while True:
            try:
                # Run cleanup
                cleanup_old_reports()
                
                # Wait for next cleanup (once per day at 3 AM)
                now = datetime.now()
                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
                
                # If it's already past 3 AM, schedule for tomorrow
                if now.hour >= 3:
                    next_run = next_run + timedelta(days=1)
                
                # Calculate seconds until next run
                sleep_seconds = (next_run - now).total_seconds()
                
                # Make sure we don't have a negative sleep time
                if sleep_seconds <= 0:
                    sleep_seconds = 86400  # 24 hours
                
                logger.info(f"Next reports cleanup scheduled for {next_run} (in {sleep_seconds/3600:.2f} hours)")
                
                # Sleep until next cleanup time
                time.sleep(sleep_seconds)
                
            except Exception as e:
                logger.error(f"Error in reports cleanup worker: {str(e)}")
                # If there's an error, wait 1 hour before retrying
                time.sleep(3600)
    
    # Create and start the cleanup thread
    cleanup_thread = threading.Thread(target=run_cleanup)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    return cleanup_thread
