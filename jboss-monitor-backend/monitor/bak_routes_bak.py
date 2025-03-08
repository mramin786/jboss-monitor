# monitor/routes.py
from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
import time
import threading

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

def get_jboss_credentials(current_user, environment):
    """Get JBoss credentials for the specified environment"""
    env_key = 'production_jboss_' if environment == 'production' else 'non_production_jboss_'
    
    username = current_user.get(f'{env_key}username')
    password = current_user.get(f'{env_key}password')
    
    return username, password

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
    username, password = get_jboss_credentials(current_user, environment)
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
    username, password = get_jboss_credentials(current_user, environment)
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

def monitor_host(environment, host, username, password):
    """Monitor a single host and update its status"""
    host_id = host['id']
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
    if not server_result['success']:
        status[host_id]['instance_status'] = 'down'
        status[host_id]['last_check'] = datetime.now().isoformat()
        save_status(status, environment)
        return
    
    # Server is up, update status
    status[host_id]['instance_status'] = 'up' if server_result['success'] else 'down'
    
    # Get datasources
    datasources_result = cli.get_datasources()
    if datasources_result['success']:
        try:
            # Extract datasource names
            ds_data = datasources_result['result']
            datasources = []
            
            # Handle data-source
            if 'data-source' in ds_data:
                for ds_name in ds_data['data-source']:
                    # Test connection
                    ds_conn_result = cli.check_datasource_connection(ds_name)
                    datasources.append({
                        'name': ds_name,
                        'type': 'data-source',
                        'status': 'up' if ds_conn_result['success'] and ds_conn_result.get('result') == True else 'down'
                    })
            
            # Handle xa-data-source
            if 'xa-data-source' in ds_data:
                for ds_name in ds_data['xa-data-source']:
                    # Test connection
                    ds_conn_result = cli.check_datasource_connection(ds_name)
                    datasources.append({
                        'name': ds_name,
                        'type': 'xa-data-source',
                        'status': 'up' if ds_conn_result['success'] and ds_conn_result.get('result') == True else 'down'
                    })
                    
            status[host_id]['datasources'] = datasources
        except (KeyError, TypeError):
            status[host_id]['datasources'] = []
    
    # Get deployments
    deployments_result = cli.get_deployments()
    if deployments_result['success']:
        try:
            # Extract deployment names and status
            deployments_data = deployments_result['result']
            deployments = []
            
            for deployment_name, deployment_data in deployments_data.items():
                # Check if deployment is enabled
                enabled = deployment_data.get('enabled', False)
                
                deployments.append({
                    'name': deployment_name,
                    'status': 'up' if enabled else 'down'
                })
                    
            status[host_id]['deployments'] = deployments
        except (KeyError, TypeError):
            status[host_id]['deployments'] = []
    
    # Update last check timestamp
    status[host_id]['last_check'] = datetime.now().isoformat()
    
    # Save updated status
    save_status(status, environment)
