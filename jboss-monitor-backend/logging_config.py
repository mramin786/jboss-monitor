# logging_config.py
import os
import logging
import logging.handlers
from datetime import datetime
import shutil
import glob
from config import Config

# Default log directory (can be overridden in config.py)
DEFAULT_LOG_DIR = '/app/jbossmonit/logs'

# Create log directory if it doesn't exist
def setup_logging():
    """Set up application logging with rotation and cleanup"""
    # Get log directory from config or use default
    log_dir = getattr(Config, 'LOG_DIR', DEFAULT_LOG_DIR)
    
    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up daily rotating file handler
    log_file = os.path.join(log_dir, 'jboss_monitor.log')
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when='midnight',  # Rotate at midnight
        interval=1,       # One day
        backupCount=3,    # Keep logs for 3 days
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Custom suffix for rotated logs - include date in filename
    file_handler.suffix = "%Y-%m-%d.log"
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our file handler
    root_logger.addHandler(file_handler)
    
    # Optionally add a console handler for development
    if getattr(Config, 'DEBUG', False):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
    
    # Clean up old log files
    cleanup_old_logs(log_dir)
    
    return root_logger

def cleanup_old_logs(log_dir, max_days=3):
    """Clean up log files older than max_days"""
    try:
        current_time = datetime.now()
        # Find all log files in the directory
        for file_path in glob.glob(os.path.join(log_dir, '*.log*')):
            # Get file modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            # Calculate age in days
            age_days = (current_time - file_time).days
            
            # If file is older than max_days, delete it
            if age_days > max_days:
                os.remove(file_path)
                print(f"Deleted old log file: {file_path} (age: {age_days} days)")
    except Exception as e:
        print(f"Error cleaning up logs: {str(e)}")

# Manual cleanup function that can be called periodically
def manual_log_cleanup():
    """Manually clean up old log files"""
    log_dir = getattr(Config, 'LOG_DIR', DEFAULT_LOG_DIR)
    cleanup_old_logs(log_dir)
