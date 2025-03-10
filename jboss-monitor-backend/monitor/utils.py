# monitor/utils.py
import os
import json
import logging
import traceback
import filelock
from datetime import datetime
from config import Config
from hosts.routes import get_environment_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_status_file(environment):
    """Get the status file path for the specified environment"""
    return os.path.join(get_environment_path(environment), 'status.json')

def load_status(environment):
    """Load status from file storage with enhanced error handling"""
    status_file = get_status_file(environment)
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            # Handle corrupted JSON file
            logger.error(f"Error loading status file for {environment}: {str(e)}")
            # Create backup of corrupted file
            backup_file = status_file + ".corrupted"
            try:
                import shutil
                shutil.copy2(status_file, backup_file)
                logger.info(f"Created backup of corrupted file at {backup_file}")
                # Create empty status file
                with open(status_file, 'w') as f:
                    json.dump({}, f)
                logger.info(f"Created new empty status file for {environment}")
                return {}
            except Exception as e2:
                logger.error(f"Error handling corrupted status file: {str(e2)}")
                return {}
    return {}

def save_status(status, environment):
    """Save status to file storage with improved thread safety"""
    status_file = get_status_file(environment)
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    
    # Add last_updated timestamp to force ETag changes and help clients detect updates
    status['_last_updated'] = datetime.now().isoformat()
    
    # Use file lock to prevent race conditions
    lock_file = status_file + ".lock"
    lock = filelock.FileLock(lock_file, timeout=Config.STATUS_UPDATE_LOCK_TIMEOUT)
    
    try:
        with lock:
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)
            logger.debug(f"Status file updated for {environment}")
    except filelock.Timeout:
        logger.error(f"Could not acquire lock for {status_file} within {Config.STATUS_UPDATE_LOCK_TIMEOUT} seconds")
        # Still try to write the file as a fallback
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        logger.debug(f"Status file updated for {environment} (without lock)")
    except Exception as e:
        logger.error(f"Error saving status file: {str(e)}")
        logger.error(traceback.format_exc())

def get_jboss_credentials(environment):
    """Get JBoss credentials for the specified environment with debugging"""
    # Try environment variables first
    if environment == 'production':
        username = Config.PROD_JBOSS_USERNAME
        password = Config.PROD_JBOSS_PASSWORD
        print(f"Production credentials from env: Username='{username}', Password exists={password is not None}")
    elif environment == 'non_production':
        username = Config.NONPROD_JBOSS_USERNAME
        password = Config.NONPROD_JBOSS_PASSWORD
        print(f"Non-Production credentials from env: Username='{username}', Password exists={password is not None}")
    
    return username, password

def parse_datasources(ds_data):
    """
    Parse datasources from JBoss CLI response
    Handles different JBoss versions and response formats
    
    Returns a list of datasource dictionaries with name, type and status
    """
    datasources = []
    logger.debug(f"Parsing datasources from data: {type(ds_data)}")
    
    # If not a dictionary, we can't parse it
    if not isinstance(ds_data, dict):
        logger.warning(f"Datasource data is not a dictionary: {type(ds_data)}")
        return datasources
    
    try:
        # Format 1: {'data-source': {'name1': {...}, 'name2': {...}}, 'xa-data-source': {...}}
        # Common in newer JBoss versions
        if 'data-source' in ds_data and isinstance(ds_data['data-source'], dict):
            for ds_name, ds_details in ds_data['data-source'].items():
                logger.debug(f"Processing datasource: {ds_name}")
                enabled = ds_details.get('enabled', False)
                
                # Get connection status if available
                connection_valid = True  # Default to true if we can't determine
                if 'statistics-enabled' in ds_details and ds_details.get('statistics-enabled', False):
                    # If statistics are enabled, we might have more detailed status
                    connection_valid = not ds_details.get('failed', False)
                
                datasources.append({
                    'name': ds_name,
                    'type': 'data-source',
                    'status': 'up' if enabled and connection_valid else 'down',
                    'jndi-name': ds_details.get('jndi-name', ''),
                    'driver': ds_details.get('driver-name', '')
                })
        
        # Format 2: {'data-source': ['name1', 'name2'], 'xa-data-source': ['name3']}
        # Common in some older JBoss versions
        elif 'data-source' in ds_data and isinstance(ds_data['data-source'], list):
            for ds_name in ds_data['data-source']:
                logger.debug(f"Processing datasource (list format): {ds_name}")
                datasources.append({
                    'name': ds_name,
                    'type': 'data-source',
                    'status': 'up'  # Assume up since we can't determine from list format
                })
        
        # Handle XA datasources with dictionary format
        if 'xa-data-source' in ds_data and isinstance(ds_data['xa-data-source'], dict):
            for ds_name, ds_details in ds_data['xa-data-source'].items():
                logger.debug(f"Processing XA datasource: {ds_name}")
                enabled = ds_details.get('enabled', False)
                
                # Get connection status if available
                connection_valid = True  # Default to true if we can't determine
                if 'statistics-enabled' in ds_details and ds_details.get('statistics-enabled', False):
                    # If statistics are enabled, we might have more detailed status
                    connection_valid = not ds_details.get('failed', False)
                
                datasources.append({
                    'name': ds_name,
                    'type': 'xa-data-source',
                    'status': 'up' if enabled and connection_valid else 'down',
                    'jndi-name': ds_details.get('jndi-name', ''),
                    'driver': ds_details.get('driver-name', '')
                })
        
        # Handle XA datasources with list format
        elif 'xa-data-source' in ds_data and isinstance(ds_data['xa-data-source'], list):
            for ds_name in ds_data['xa-data-source']:
                logger.debug(f"Processing XA datasource (list format): {ds_name}")
                datasources.append({
                    'name': ds_name,
                    'type': 'xa-data-source',
                    'status': 'up'  # Assume up since we can't determine from list format
                })
        
        return datasources
    except Exception as e:
        logger.error(f"Error parsing datasources: {str(e)}")
        traceback.print_exc()
        return []

def parse_deployments(deployment_data):
    """
    Parse deployments from JBoss CLI response
    Handles different JBoss versions and response formats
    Accepts all deployment types, not just .war files
    
    Returns a list of deployment dictionaries with name and status
    """
    deployments = []
    logger.debug(f"Parsing deployments from data: {type(deployment_data)}")
    
    try:
        # Format 1: Dictionary with deployment names as keys
        # Common in many JBoss versions
        if isinstance(deployment_data, dict):
            for deployment_name, deployment_details in deployment_data.items():
                if isinstance(deployment_details, dict):
                    logger.debug(f"Processing deployment: {deployment_name}")
                    enabled = deployment_details.get('enabled', False)
                    
                    # Get runtime name if available
                    runtime_name = deployment_details.get('runtime-name', deployment_name)
                    
                    # Get deployment type (war, ear, jar, etc.) from name
                    deployment_type = 'unknown'
                    if '.' in deployment_name:
                        deployment_type = deployment_name.split('.')[-1].lower()
                    
                    deployments.append({
                        'name': deployment_name,
                        'runtime-name': runtime_name,
                        'type': deployment_type,
                        'status': 'up' if enabled else 'down'
                    })
        
        # Format 2: List of deployment objects
        # Sometimes seen in JBoss EAP
        elif isinstance(deployment_data, list):
            for deployment in deployment_data:
                if isinstance(deployment, dict):
                    # Try to extract from various formats
                    if 'address' in deployment and isinstance(deployment['address'], list) and len(deployment['address']) > 0:
                        # Extract from address format like [{"deployment": "example.war"}]
                        for addr_part in deployment['address']:
                            if isinstance(addr_part, dict) and 'deployment' in addr_part:
                                deployment_name = addr_part['deployment']
                                enabled = True
                                if 'result' in deployment and isinstance(deployment['result'], dict):
                                    enabled = deployment['result'].get('enabled', True)
                                
                                # Get deployment type from name
                                deployment_type = 'unknown'
                                if '.' in deployment_name:
                                    deployment_type = deployment_name.split('.')[-1].lower()
                                
                                logger.debug(f"Processing deployment from address: {deployment_name}")
                                deployments.append({
                                    'name': deployment_name,
                                    'type': deployment_type,
                                    'status': 'up' if enabled else 'down'
                                })
                    elif 'name' in deployment:
                        # Direct name attribute format
                        deployment_name = deployment['name']
                        enabled = deployment.get('enabled', True)
                        
                        # Get deployment type from name
                        deployment_type = 'unknown'
                        if '.' in deployment_name:
                            deployment_type = deployment_name.split('.')[-1].lower()
                        
                        logger.debug(f"Processing deployment with name attr: {deployment_name}")
                        deployments.append({
                            'name': deployment_name,
                            'type': deployment_type,
                            'status': 'up' if enabled else 'down'
                        })
        
        return deployments
    except Exception as e:
        logger.error(f"Error parsing deployments: {str(e)}")
        traceback.print_exc()
        return []
