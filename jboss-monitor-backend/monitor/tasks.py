# monitor/tasks.py
import os
import json
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from hosts.routes import load_hosts, get_environment_path
from monitor.cli_executor import JBossCliExecutor
from monitor.routes import monitor_host, load_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_system_credentials(environment):
    """Get system monitoring credentials for the environment"""
    if environment == 'production':
        username = Config.PROD_JBOSS_USERNAME
        password = Config.PROD_JBOSS_PASSWORD
    elif environment == 'non_production':
        username = Config.NONPROD_JBOSS_USERNAME
        password = Config.NONPROD_JBOSS_PASSWORD
    else:
        logger.warning(f"Unknown environment: {environment}")
        return None, None
    
    if not username or not password:
        logger.warning(f"No system credentials found for {environment} environment")
    else:
        logger.info(f"Credentials found for {environment} environment")
    
    return username, password

def monitor_environment(environment):
    """Monitor all hosts in an environment"""
    logger.info(f"Starting monitoring for {environment} environment")
    
    # Get system credentials
    username, password = get_system_credentials(environment)
    if not username or not password:
        logger.warning(f"No system credentials found for {environment} environment")
        return
    
    # Get all hosts
    hosts = load_hosts(environment)
    if not hosts:
        logger.info(f"No hosts found for {environment} environment")
        return
    
    logger.info(f"Found {len(hosts)} hosts for {environment} environment")
    
    # Use ThreadPoolExecutor for parallel monitoring
    with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
        # Submit monitoring tasks
        futures = []
        for host in hosts:
            logger.info(f"Submitting monitoring task for {host['host']}:{host['port']}")
            futures.append(
                executor.submit(monitor_host, environment, host, username, password)
            )
        
        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in monitoring task: {str(e)}")

def monitoring_worker():
    """Background worker that continuously monitors all environments with better error handling"""
    logger.info("Monitoring worker started")
    
    while True:
        try:
            start_time = time.time()
            logger.info("Starting monitoring cycle")
            
            # Monitor production environment
            try:
                monitor_environment('production')
            except Exception as e:
                logger.error(f"Error monitoring production environment: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Monitor non-production environment
            try:
                monitor_environment('non_production')
            except Exception as e:
                logger.error(f"Error monitoring non-production environment: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Calculate elapsed time
            elapsed = time.time() - start_time
            logger.info(f"Monitoring cycle completed in {elapsed:.2f} seconds")
            
            # Calculate wait time (ensure we don't wait negative time)
            wait_time = max(1, Config.MONITORING_INTERVAL - elapsed)
            logger.info(f"Waiting {wait_time:.2f} seconds for next cycle")
            
            # Wait for next monitoring cycle
            time.sleep(wait_time)
        
        except Exception as e:
            logger.error(f"Error in monitoring worker: {str(e)}")
            # Add stack trace for debugging
            import traceback
            logger.error(traceback.format_exc())
            time.sleep(10)  # Wait a bit before retrying
def start_monitoring_worker():
    """Start the background monitoring worker"""
    logger.info("Starting background monitoring worker")
    
    # Create required directories
    os.makedirs(Config.PROD_ENV_PATH, exist_ok=True)
    os.makedirs(Config.NONPROD_ENV_PATH, exist_ok=True)
    
    # Check system credentials
    prod_username, prod_password = get_system_credentials('production')
    nonprod_username, nonprod_password = get_system_credentials('non_production')
    
    # Log warning if credentials are missing
    if not prod_username or not prod_password:
        logger.warning("Production JBoss CLI credentials are not set in environment variables")
    
    if not nonprod_username or not nonprod_password:
        logger.warning("Non-Production JBoss CLI credentials are not set in environment variables")
    
    # Start monitoring in a separate thread to avoid blocking app startup
    def run_monitoring():
        try:
            logger.info("Running monitoring worker in background thread")
            monitoring_worker()
        except Exception as e:
            logger.error(f"Fatal error in monitoring worker thread: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Create and start the thread
    monitoring_thread = threading.Thread(target=run_monitoring)
    monitoring_thread.daemon = True  # Make thread a daemon so it exits when main thread exits
    monitoring_thread.start()
    logger.info("Monitoring worker thread started")
