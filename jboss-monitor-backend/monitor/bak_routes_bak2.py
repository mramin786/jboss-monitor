# monitor/routes.py
import os
import json
from datetime import datetime
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, request, jsonify
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
    status[host_id]['instance_status'] = 'up'
    
    # Get datasources
    datasources_result = cli.get_datasources()
    if datasources_result['success']:
        try:
            # Parse datasources carefully
            ds_data = datasources_result['result']
            datasources = []
            
            # Handle data-source
            if isinstance(ds_data, dict) and 'data-source' in ds_data:
                for ds_name in ds_data['data-source']:
                    # Test connection
                    ds_conn_result = cli.check_datasource_connection(ds_name)
                    datasources.append({
                        'name': ds_name,
                        'type': 'data-source',
                        'status': 'up' if ds_conn_result['success'] and ds_conn_result.get('result') == True else 'down'
                    })
            
            # Handle xa-data-source
            if isinstance(ds_data, dict) and 'xa-data-source' in ds_data:
                for ds_name in ds_data['xa-data-source']:
                    # Test connection
                    ds_conn_result = cli.check_datasource_connection(ds_name)
                    datasources.append({
                        'name': ds_name,
                        'type': 'xa-data-source',
                        'status': 'up' if ds_conn_result['success'] and ds_conn_result.get('result') == True else 'down'
                    })
                    
            status[host_id]['datasources'] = datasources
        except Exception as e:
            print(f"Datasource parsing error: {e}")
            status[host_id]['datasources'] = []
    
    # Get deployments
    deployments_result = cli.get_deployments()
    if deployments_result['success']:
        try:
            # Parse deployments carefully
            deployments_data = deployments_result['result']
            deployments = []
            
            # Check if it's a dictionary before calling .items()
            if isinstance(deployments_data, dict):
                for deployment_name, deployment_data in deployments_data.items():
                    # Check if deployment is enabled
                    enabled = deployment_data.get('enabled', False)
                    
                    deployments.append({
                        'name': deployment_name,
                        'status': 'up' if enabled else 'down'
                    })
            elif isinstance(deployments_data, str):
                # If it's a string, log it and skip parsing
                print(f"Unexpected deployments data format: {deployments_data}")
                deployments = []
                    
            status[host_id]['deployments'] = deployments
        except Exception as e:
            print(f"Deployment parsing error: {e}")
            status[host_id]['deployments'] = []
    
    # Update last check timestamp
    status[host_id]['last_check'] = datetime.now().isoformat()
    
    # Save updated status
    save_status(status, environment)
