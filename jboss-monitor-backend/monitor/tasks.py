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
        return Config.PROD_JBOSS_USERNAME, Config.PROD_JBOSS_PASSWORD
    elif environment == 'non_production':
        return Config.NONPROD_JBOSS_USERNAME, Config.NONPROD_JBOSS_PASSWORD
    
    logger.warning(f"No system credentials found for {environment} environment")
    return None, None

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
    
    # Use ThreadPoolExecutor for parallel monitoring
    with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
        # Submit monitoring tasks
        futures = []
        for host in hosts:
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
    """Background worker that continuously monitors all environments"""
    while True:
        try:
            # Monitor production environment
            monitor_environment('production')
            
            # Monitor non-production environment
            monitor_environment('non_production')
            
            # Wait for next monitoring cycle
            logger.info(f"Monitoring cycle completed. Waiting {Config.MONITORING_INTERVAL} seconds for next cycle")
            time.sleep(Config.MONITORING_INTERVAL)
        
        except Exception as e:
            logger.error(f"Error in monitoring worker: {str(e)}")
            time.sleep(10)  # Wait a bit before retrying

def start_monitoring_worker():
    """Start the background monitoring worker"""
    logger.info("Starting background monitoring worker")
    
    # Create required directories
    os.makedirs(Config.PROD_ENV_PATH, exist_ok=True)
    os.makedirs(Config.NONPROD_ENV_PATH, exist_ok=True)
    
    # Check system credentials
    prod_creds = get_system_credentials('production')
    nonprod_creds = get_system_credentials('non_production')
    
    # Log warning if credentials are missing
    if not prod_creds[0] or not prod_creds[1]:
        logger.warning("Production JBoss CLI credentials are not set in environment variables")
    
    if not nonprod_creds[0] or not nonprod_creds[1]:
        logger.warning("Non-Production JBoss CLI credentials are not set in environment variables")
    
    # Start monitoring
    monitoring_worker()
