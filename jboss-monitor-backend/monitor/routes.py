# monitor/routes.py
from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
import time
import threading
import traceback
import logging

from auth.routes import token_required
from config import Config
from hosts.routes import load_hosts, get_environment_path
from monitor.cli_executor import JBossCliExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

monitor_bp = Blueprint('monitor', __name__)

def get_status_file(environment):
    """Get the status file path for the specified environment"""
    return os.path.join(get_environment_path(environment), 'status.json')

def load_status(environment):
    """Load status from file storage"""
    status_file = get_status_file(environment)
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return json.load(f)
    return {}

def save_status(status, environment):
    """Save status to file storage"""
    status_file = get_status_file(environment)
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)

def get_jboss_credentials(environment):
    """Get JBoss credentials for the specified environment"""
    # Try environment variables first
    if environment == 'production':
        return Config.PROD_JBOSS_USERNAME, Config.PROD_JBOSS_PASSWORD
    elif environment == 'non_production':
        return Config.NONPROD_JBOSS_USERNAME, Config.NONPROD_JBOSS_PASSWORD

    return None, None

def parse_datasources(ds_data):
    """
    Parse datasources from JBoss CLI response
    Handles different JBoss versions and response formats
    
    Returns a list of datasource dictionaries with name, type and status
    """
    datasources = []
    logger.info(f"Parsing datasources from data: {type(ds_data)}")
    
    # If not a dictionary, we can't parse it
    if not isinstance(ds_data, dict):
        logger.warning(f"Datasource data is not a dictionary: {type(ds_data)}")
        return datasources
    
    try:
        # Format 1: {'data-source': {'name1': {...}, 'name2': {...}}, 'xa-data-source': {...}}
        # Common in newer JBoss versions
        if 'data-source' in ds_data and isinstance(ds_data['data-source'], dict):
            for ds_name, ds_details in ds_data['data-source'].items():
                logger.info(f"Processing datasource: {ds_name}")
                enabled = ds_details.get('enabled', False)
                datasources.append({
                    'name': ds_name,
                    'type': 'data-source',
                    'status': 'up' if enabled else 'down'
                })
        
        # Format 2: {'data-source': ['name1', 'name2'], 'xa-data-source': ['name3']}
        # Common in some older JBoss versions
        elif 'data-source' in ds_data and isinstance(ds_data['data-source'], list):
            for ds_name in ds_data['data-source']:
                logger.info(f"Processing datasource (list format): {ds_name}")
                datasources.append({
                    'name': ds_name,
                    'type': 'data-source',
                    'status': 'up'  # Assume up since we can't determine from list format
                })
        
        # Handle XA datasources with dictionary format
        if 'xa-data-source' in ds_data and isinstance(ds_data['xa-data-source'], dict):
            for ds_name, ds_details in ds_data['xa-data-source'].items():
                logger.info(f"Processing XA datasource: {ds_name}")
                enabled = ds_details.get('enabled', False)
                datasources.append({
                    'name': ds_name,
                    'type': 'xa-data-source',
                    'status': 'up' if enabled else 'down'
                })
        
        # Handle XA datasources with list format
        elif 'xa-data-source' in ds_data and isinstance(ds_data['xa-data-source'], list):
            for ds_name in ds_data['xa-data-source']:
                logger.info(f"Processing XA datasource (list format): {ds_name}")
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
    
    Returns a list of deployment dictionaries with name and status
    """
    deployments = []
    logger.info(f"Parsing deployments from data: {type(deployment_data)}")
    
    try:
        # Format 1: Dictionary with deployment names as keys
        # Common in many JBoss versions
        if isinstance(deployment_data, dict):
            for deployment_name, deployment_details in deployment_data.items():
                if isinstance(deployment_details, dict):
                    logger.info(f"Processing deployment: {deployment_name}")
                    enabled = deployment_details.get('enabled', False)
                    deployments.append({
                        'name': deployment_name,
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
                                
                                logger.info(f"Processing deployment from address: {deployment_name}")
                                deployments.append({
                                    'name': deployment_name,
                                    'status': 'up' if enabled else 'down'
                                })
                    elif 'name' in deployment:
                        # Direct name attribute format
                        deployment_name = deployment['name']
                        enabled = deployment.get('enabled', True)
                        
                        logger.info(f"Processing deployment with name attr: {deployment_name}")
                        deployments.append({
                            'name': deployment_name,
                            'status': 'up' if enabled else 'down'
                        })
        
        return deployments
    except Exception as e:
        logger.error(f"Error parsing deployments: {str(e)}")
        traceback.print_exc()
        return []

def monitor_host(environment, host, username, password):
    """Monitor a single host and update its status"""
    host_id = host['id']
    logger.info(f"Starting monitoring for host: {host['host']}:{host['port']}")
    
    status = load_status(environment)
    
    # Initialize status for this host if not exists
    if host_id not in status:
        status[host_id] = {
            'instance_status': 'unknown',
            'datasources': [],
            'deployments': [],
            'last_check': None
        }
    
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
        status[host_id]['instance_status'] = 'down'
        status[host_id]['last_check'] = datetime.now().isoformat()
        save_status(status, environment)
        return
    
    # Server is up, update status
    status[host_id]['instance_status'] = 'up'
    
    # Get datasources
    datasources_result = cli.get_datasources()
    logger.info(f"Datasource check result success: {datasources_result['success']}")
    
    if datasources_result['success'] and 'result' in datasources_result:
        logger.info(f"Raw datasource result: {json.dumps(datasources_result['result'])[:500]}...")
        datasources = parse_datasources(datasources_result['result'])
        logger.info(f"Parsed {len(datasources)} datasources")
        status[host_id]['datasources'] = datasources
    else:
        logger.warning(f"Failed to get datasources: {datasources_result.get('error', 'Unknown error')}")
        status[host_id]['datasources'] = []
    
    # Get deployments
    deployments_result = cli.get_deployments()
    logger.info(f"Deployment check result success: {deployments_result['success']}")
    
    if deployments_result['success'] and 'result' in deployments_result:
        logger.info(f"Raw deployment result: {json.dumps(deployments_result['result'])[:500]}...")
        deployments = parse_deployments(deployments_result['result'])
        logger.info(f"Parsed {len(deployments)} deployments")
        status[host_id]['deployments'] = deployments
    else:
        logger.warning(f"Failed to get deployments: {deployments_result.get('error', 'Unknown error')}")
        status[host_id]['deployments'] = []
    
    # Update last check timestamp
    status[host_id]['last_check'] = datetime.now().isoformat()
    
    # Save updated status
    save_status(status, environment)
    logger.info(f"Completed monitoring for host: {host['host']}:{host['port']}")

@monitor_bp.route('/<environment>/status', methods=['GET'])
@token_required
def get_monitor_status(current_user, environment):
    """Get monitoring status for the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400

    hosts = load_hosts(environment)
    status = load_status(environment)

    # Combine hosts with their status
    result = []
    for host in hosts:
        host_id = host['id']
        host_status = status.get(host_id, {
            'instance_status': 'unknown',
            'datasources': [],
            'deployments': [],
            'last_check': None
        })

        result.append({
            **host,
            'status': host_status
        })

    return jsonify(result), 200

@monitor_bp.route('/<environment>/check/<host_id>', methods=['POST'])
@token_required
def check_host(current_user, environment, host_id):
    """Manually check status for a specific host"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400

    # Get JBoss credentials
    username, password = get_jboss_credentials(environment)
    if not username or not password:
        return jsonify({'message': 'JBoss credentials not found'}), 400

    # Find the host
    hosts = load_hosts(environment)
    host = None
    for h in hosts:
        if h['id'] == host_id:
            host = h
            break

    if not host:
        return jsonify({'message': 'Host not found'}), 404

    # Create a thread to run the check in background
    def run_check():
        monitor_host(environment, host, username, password)

    check_thread = threading.Thread(target=run_check)
    check_thread.daemon = True
    check_thread.start()

    return jsonify({
        'message': 'Check initiated',
        'host': host
    }), 200

@monitor_bp.route('/<environment>/check-all', methods=['POST'])
@token_required
def check_all_hosts(current_user, environment):
    """Manually check status for all hosts"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400

    # Get JBoss credentials
    username, password = get_jboss_credentials(environment)
    if not username or not password:
        return jsonify({'message': 'JBoss credentials not found'}), 400

    # Get all hosts
    hosts = load_hosts(environment)
    
    if not hosts:
        return jsonify({
            'message': 'No hosts found for this environment',
            'host_count': 0
        }), 200

    # Create a thread to run all checks in background
    def run_checks():
        for host in hosts:
            monitor_host(environment, host, username, password)

    check_thread = threading.Thread(target=run_checks)
    check_thread.daemon = True
    check_thread.start()

    return jsonify({
        'message': 'Check initiated for all hosts',
        'host_count': len(hosts)
    }), 200

@monitor_bp.route('/<environment>/debug', methods=['GET'])
@token_required
def debug_environment(current_user, environment):
    """Get debug information for the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    # Get environment details
    env_path = get_environment_path(environment)
    hosts = load_hosts(environment)
    status = load_status(environment)
    
    # Get JBoss credentials
    username, password = get_jboss_credentials(environment)
    has_credentials = bool(username and password)
    
    # Get file permissions and directory structure
    env_stats = {
        'path': env_path,
        'exists': os.path.exists(env_path),
        'is_dir': os.path.isdir(env_path) if os.path.exists(env_path) else False,
        'permissions': oct(os.stat(env_path).st_mode)[-3:] if os.path.exists(env_path) else None,
        'files': os.listdir(env_path) if os.path.exists(env_path) and os.path.isdir(env_path) else []
    }
    
    # Get status file details
    status_file = get_status_file(environment)
    status_stats = {
        'path': status_file,
        'exists': os.path.exists(status_file),
        'size': os.path.getsize(status_file) if os.path.exists(status_file) else 0,
        'last_modified': datetime.fromtimestamp(os.path.getmtime(status_file)).isoformat() if os.path.exists(status_file) else None
    }
    
    return jsonify({
        'environment': environment,
        'host_count': len(hosts),
        'status_count': len(status),
        'has_credentials': has_credentials,
        'env_directory': env_stats,
        'status_file': status_stats
    }), 200

@monitor_bp.route('/<environment>/status/<host_id>', methods=['DELETE'])
@token_required
def clear_host_status(current_user, environment, host_id):
    """Clear status for a specific host"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    status = load_status(environment)
    
    if host_id in status:
        del status[host_id]
        save_status(status, environment)
        return jsonify({
            'message': 'Host status cleared successfully'
        }), 200
    else:
        return jsonify({
            'message': 'Host status not found'
        }), 404
