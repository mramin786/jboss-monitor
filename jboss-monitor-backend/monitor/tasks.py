# monitor/tasks.py
import os
import json
import time
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from hosts.routes import load_hosts
from monitor.cli_executor import JBossCliExecutor
from monitor.utils import parse_datasources, parse_deployments, load_status, save_status, get_jboss_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _datasource_status_changed(old_datasources, new_datasources):
    """
    Check if datasource status has changed
    Returns True if any datasource status has changed, added, or removed
    """
    # Create dictionaries for quick lookup
    old_status = {d['name']: d['status'] for d in old_datasources}
    new_status = {d['name']: d['status'] for d in new_datasources}
    
    # Check for any status changes
    for name, status in new_status.items():
        if name in old_status and old_status[name] != status:
            # Status changed for an existing datasource
            logger.info(f"Datasource '{name}' status changed from {old_status[name]} to {status}")
            return True
    
    # Check for added or removed datasources
    if set(old_status.keys()) != set(new_status.keys()):
        added = set(new_status.keys()) - set(old_status.keys())
        removed = set(old_status.keys()) - set(new_status.keys())
        if added:
            logger.info(f"New datasources detected: {added}")
        if removed:
            logger.info(f"Datasources removed: {removed}")
        return True
    
    return False

def _deployment_status_changed(old_deployments, new_deployments):
    """
    Check if deployment status has changed
    Returns True if any deployment status has changed, added, or removed
    """
    # Create dictionaries for quick lookup
    old_status = {d['name']: d['status'] for d in old_deployments}
    new_status = {d['name']: d['status'] for d in new_deployments}
    
    # Check for any status changes
    for name, status in new_status.items():
        if name in old_status and old_status[name] != status:
            # Status changed for an existing deployment
            logger.info(f"Deployment '{name}' status changed from {old_status[name]} to {status}")
            return True
    
    # Check for added or removed deployments
    if set(old_status.keys()) != set(new_status.keys()):
        added = set(new_status.keys()) - set(old_status.keys())
        removed = set(old_status.keys()) - set(new_status.keys())
        if added:
            logger.info(f"New deployments detected: {added}")
        if removed:
            logger.info(f"Deployments removed: {removed}")
        return True
    
    return False

def _instance_status_changed(old_status, new_status):
    """Check if the overall instance status has changed"""
    return old_status != new_status

def monitor_host_worker(host, username, password):
    """Worker function to monitor a single host and return its status (without saving to file)"""
    host_id = host['id']
    logger.info(f"Starting monitoring for host: {host['host']}:{host['port']}")
    
    # Initialize status for this host
    status = {
        'instance_status': 'unknown',
        'datasources': [],
        'deployments': [],
        'last_check': datetime.now().isoformat(),
        'status_changed': False  # Flag to indicate if any status has changed
    }
    
    try:
        # Create CLI executor
        cli = JBossCliExecutor(
            host=host['host'],
            port=host['port'],
            username=username,
            password=password
        )
        
        # Check server status
        server_result = cli.check_server_status()
        logger.info(f"Server status result: {server_result}")
        
        if not server_result['success']:
            logger.warning(f"Server check failed for {host['host']}:{host['port']}")
            status['instance_status'] = 'down'
            return status
        
        # Server is up, update status
        status['instance_status'] = 'up'
        
        # Get datasources
        datasources_result = cli.get_datasources()
        logger.info(f"Datasource check result success: {datasources_result['success']}")
        
        if datasources_result['success'] and 'result' in datasources_result:
            # Parse datasources
            datasources = parse_datasources(datasources_result['result'])
            logger.info(f"Parsed {len(datasources)} datasources")
            
            # Check for datasource status changes
            old_datasources = status.get('datasources', [])
            if _datasource_status_changed(old_datasources, datasources):
                logger.info(f"Datasource status change detected for host {host['host']}:{host['port']}")
                status['status_changed'] = True
                status['datasources_changed_at'] = datetime.now().isoformat()
            
            status['datasources'] = datasources
        
        # Get deployments
        deployments_result = cli.get_deployments()
        logger.info(f"Deployment check result success: {deployments_result['success']}")
        
        if deployments_result['success'] and 'result' in deployments_result:
            # Parse deployments
            deployments = parse_deployments(deployments_result['result'])
            logger.info(f"Parsed {len(deployments)} deployments")
            
            # Check for deployment status changes
            old_deployments = status.get('deployments', [])
            if _deployment_status_changed(old_deployments, deployments):
                logger.info(f"Deployment status change detected for host {host['host']}:{host['port']}")
                status['status_changed'] = True
                status['deployments_changed_at'] = datetime.now().isoformat()
            
            status['deployments'] = deployments
        
        # Update last check timestamp
        status['last_check'] = datetime.now().isoformat()
        
        logger.info(f"Completed monitoring for host: {host['host']}:{host['port']}")
        return status
    except Exception as e:
        logger.error(f"Error in monitor_host_worker for {host['host']}:{host['port']}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        status['instance_status'] = 'error'
        status['error'] = str(e)
        status['status_changed'] = True  # Consider errors as status changes
        return status

def monitor_environment(environment):
    """Monitor all hosts in an environment with true parallelism"""
    logger.info(f"Starting monitoring for {environment} environment")
    
    # Get system credentials
    username, password = get_jboss_credentials(environment)
    if not username or not password:
        logger.warning(f"No system credentials found for {environment} environment")
        return
    
    # Get all hosts
    hosts = load_hosts(environment)
    if not hosts:
        logger.info(f"No hosts found for {environment} environment")
        return
    
    logger.info(f"Found {len(hosts)} hosts for {environment} environment")
    
    # Load current status to avoid race conditions with multiple threads updating the same file
    current_status = load_status(environment)
    
    # Create a dict to hold all individual host statuses
    host_statuses = {}
    
    # Track if any status changed during this monitoring run
    status_changed = False
    
    # Calculate effective max workers based on config
    max_workers = Config.MAX_WORKERS
    if hasattr(Config, 'MAX_CONCURRENT_HOSTS') and Config.MAX_CONCURRENT_HOSTS > 0:
        max_workers = min(max_workers, Config.MAX_CONCURRENT_HOSTS)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor for parallel monitoring
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a dict mapping futures to their host IDs
        future_to_host = {
            executor.submit(monitor_host_worker, host, username, password): host['id']
            for host in hosts
        }
        
        # Process results as they complete
        for future in as_completed(future_to_host):
            host_id = future_to_host[future]
            try:
                # Get the result (host status) from the completed future
                host_status = future.result()
                
                if host_status:
                    # Check if previous status exists
                    previous_status = current_status.get(host_id, {})
                    
                    # Check if overall instance status changed
                    prev_instance_status = previous_status.get('instance_status')
                    if prev_instance_status and _instance_status_changed(prev_instance_status, host_status['instance_status']):
                        logger.info(f"Instance status changed for host {host_id} from {prev_instance_status} to {host_status['instance_status']}")
                        host_status['status_changed'] = True
                    
                    # If any host status changed, mark the overall status as changed
                    if host_status.get('status_changed', False):
                        status_changed = True
                    
                    # Store the host status
                    host_statuses[host_id] = host_status
                    logger.info(f"Successfully processed host ID: {host_id}")
            except Exception as e:
                logger.error(f"Error monitoring host {host_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # Still add failed hosts to the status with error state
                host_statuses[host_id] = {
                    'instance_status': 'error',
                    'datasources': [],
                    'deployments': [],
                    'last_check': datetime.now().isoformat(),
                    'error': str(e),
                    'status_changed': True  # Consider errors as status changes
                }
                status_changed = True
    
    # Update the status file with all the individual host statuses
    if host_statuses:
        # Add global timestamp for this monitoring run
        current_status['_last_check'] = datetime.now().isoformat()
        
        # If any status changed, add a change timestamp to force ETag updates
        if status_changed:
            current_status['_status_changed_at'] = datetime.now().isoformat()
            logger.info(f"Status changed detected in {environment} environment")
        
        # Merge with current status to update only changed hosts
        for host_id, status in host_statuses.items():
            current_status[host_id] = status
        
        # Save the combined status
        save_status(current_status, environment)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed monitoring for {environment} environment in {elapsed:.2f} seconds. Processed {len(host_statuses)} hosts.")

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
            # Use shorter interval if we're in development mode
            monitoring_interval = int(os.environ.get('MONITORING_INTERVAL') or Config.MONITORING_INTERVAL)
            # Cap minimum interval at 5 seconds to prevent excessive polling
            wait_time = max(5, monitoring_interval - elapsed)
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
    prod_username, prod_password = get_jboss_credentials('production')
    nonprod_username, nonprod_password = get_jboss_credentials('non_production')
    
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
