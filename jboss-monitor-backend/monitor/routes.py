# monitor/routes.py
from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
import time
import threading
import traceback

from auth.routes import token_required
from config import Config
from hosts.routes import load_hosts, get_environment_path
from monitor.cli_executor import JBossCliExecutor

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

def monitor_host(environment, host, username, password):
    """Monitor a single host and update its status"""
    host_id = host['id']
    status = load_status(environment)
    
    print(f"Monitoring host: {host['host']}:{host['port']}")
    
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
    print(f"Server status check result: {server_result['success']}")
    
    if not server_result['success']:
        status[host_id]['instance_status'] = 'down'
        status[host_id]['last_check'] = datetime.now().isoformat()
        save_status(status, environment)
        return
    
    # Server is up, update status
    status[host_id]['instance_status'] = 'up'
    
    # Get datasources
    datasources_result = cli.get_datasources()
    print(f"Datasource result success: {datasources_result['success']}")
    
    if datasources_result['success']:
        try:
            # Parse datasources carefully
            ds_data = datasources_result['result']
            print(f"Datasource data structure: {type(ds_data)}")
            datasources = []
            
            # Handle data-source
            if isinstance(ds_data, dict) and 'data-source' in ds_data:
                # Get the actual datasource dictionary
                ds_dict = ds_data['data-source']
                print(f"Datasource dict type: {type(ds_dict)}")
                
                # In your JBoss version, data-source is a dictionary with datasource names as keys
                for ds_name, ds_details in ds_dict.items():
                    print(f"Processing datasource: {ds_name}")
                    enabled = ds_details.get('enabled', False)
                    datasources.append({
                        'name': ds_name,
                        'type': 'data-source',
                        'status': 'up' if enabled else 'down'
                    })
            
            # Handle xa-data-source if present
            if isinstance(ds_data, dict) and 'xa-data-source' in ds_data and ds_data['xa-data-source']:
                xa_dict = ds_data['xa-data-source']
                if isinstance(xa_dict, dict):
                    for ds_name, ds_details in xa_dict.items():
                        enabled = ds_details.get('enabled', False)
                        datasources.append({
                            'name': ds_name,
                            'type': 'xa-data-source',
                            'status': 'up' if enabled else 'down'
                        })
            
            print(f"Parsed datasources: {datasources}")
            status[host_id]['datasources'] = datasources
        except Exception as e:
            print(f"Datasource parsing error: {str(e)}")
            traceback.print_exc()
            status[host_id]['datasources'] = []
    
    # Get deployments
    deployments_result = cli.get_deployments()
    print(f"Deployment result success: {deployments_result['success']}")
    
    if deployments_result['success']:
        try:
            # Parse deployments carefully
            deployments_data = deployments_result['result']
            print(f"Deployment data type: {type(deployments_data)}")
            deployments = []
            
            # For your JBoss version, deployments are returned as an array
            if isinstance(deployments_data, list):
                for deployment in deployments_data:
                    print(f"Processing deployment item: {deployment['address'][0][1] if 'address' in deployment else 'unknown'}")
                    # Extract deployment details
                    if 'result' in deployment and isinstance(deployment['result'], dict):
                        deployment_details = deployment['result']
                        deployment_name = deployment['address'][0][1]  # Extract name from address
                        
                        # Check if deployment is enabled
                        enabled = deployment_details.get('enabled', False)
                        
                        deployments.append({
                            'name': deployment_name,
                            'status': 'up' if enabled else 'down'
                        })
            
            print(f"Parsed deployments: {deployments}")
            status[host_id]['deployments'] = deployments
        except Exception as e:
            print(f"Deployment parsing error: {str(e)}")
            traceback.print_exc()
            status[host_id]['deployments'] = []
    
    # Update last check timestamp
    status[host_id]['last_check'] = datetime.now().isoformat()
    
    # Save updated status
    save_status(status, environment)
    print(f"Saved status for host {host['host']}")

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
