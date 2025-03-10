# monitor/routes.py
from flask import Blueprint, request, jsonify
import os
import threading
import time
import logging
from datetime import datetime

from auth.routes import token_required
from config import Config
from hosts.routes import load_hosts
from monitor.utils import (
    get_status_file, load_status, save_status, 
    get_jboss_credentials, parse_datasources, parse_deployments
)
from monitor.tasks import monitor_host_worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

monitor_bp = Blueprint('monitor', __name__)

def monitor_host(environment, host, username, password):
    """Monitor a single host and update its status"""
    host_id = host['id']
    logger.info(f"Starting monitoring for host: {host['host']}:{host['port']}")
    
    # Get host status
    host_status = monitor_host_worker(host, username, password)
    
    # Load current status
    status = load_status(environment)
    
    # Check if status changed
    previous_status = status.get(host_id, {})
    
    # Update status with this host's status
    status[host_id] = host_status
    
    # Add metadata for this update
    status['_single_host_updated'] = host_id
    status['_single_host_updated_at'] = datetime.now().isoformat()
    
    # Save updated status
    save_status(status, environment)
    
    logger.info(f"Completed monitoring for host: {host['host']}:{host['port']}")
    
    return host_status

@monitor_bp.route('/<environment>/status', methods=['GET'])
@token_required
def get_monitor_status(current_user, environment):
    """Get monitoring status for the specified environment with enhanced caching control"""
    try:
        if environment not in ['production', 'non_production']:
            return jsonify({'message': 'Invalid environment'}), 400

        # Generate ETag based on the last modification time of status file
        status_file = get_status_file(environment)
        etag = None
        if os.path.exists(status_file):
            # Add timestamp to make ETag more unique
            file_mtime = os.path.getmtime(status_file)
            etag = f"W/\"{file_mtime}_{int(time.time())}\""
            
            # Check if client sent If-None-Match header
            if_none_match = request.headers.get('If-None-Match')
            if if_none_match and if_none_match == etag:
                # Return 304 Not Modified if ETags match
                return '', 304

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

        # Add metadata to response
        metadata = {
            'last_updated': status.get('_last_updated', datetime.now().isoformat()),
            'environment': environment,
            'host_count': len(hosts),
            'fetch_time': datetime.now().isoformat()
        }

        # Create response with metadata
        response_data = {
            'hosts': result,
            'metadata': metadata
        }

        # Create response
        response = jsonify(response_data)
        
        # Add aggressive cache control headers
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Add ETag header
        if etag:
            response.headers['ETag'] = etag
            
        # Add timestamp header to help clients detect changes
        response.headers['X-Last-Updated'] = metadata['last_updated']
            
        return response, 200
    except Exception as e:
        logger.error(f"Error in get_monitor_status: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500

@monitor_bp.route('/<environment>/check/<host_id>', methods=['POST'])
@token_required
def check_host(current_user, environment, host_id):
    """Manually check status for a specific host with improved responsiveness"""
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
        try:
            logger.info(f"Running manual check for host {host['host']}:{host['port']}")
            host_status = monitor_host_worker(host, username, password)
            
            # Immediately update the status file for faster feedback
            status = load_status(environment)
            status[host_id] = host_status
            
            # Add metadata to indicate a manual update occurred
            status['_manual_check'] = True
            status['_manual_check_host'] = host_id
            status['_manual_check_time'] = datetime.now().isoformat()
            
            # Save updated status
            save_status(status, environment)
            logger.info(f"Manual check completed for host {host['host']}:{host['port']}")
        except Exception as e:
            logger.error(f"Error in manual check thread: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    check_thread = threading.Thread(target=run_check)
    check_thread.daemon = True
    check_thread.start()

    return jsonify({
        'message': 'Check initiated',
        'host': host,
        'request_time': datetime.now().isoformat()
    }), 200

@monitor_bp.route('/<environment>/check-all', methods=['POST'])
@token_required
def check_all_hosts(current_user, environment):
    """Manually check status for all hosts with improved parallelism and responsiveness"""
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

    # Start a thread to run all checks in background to avoid blocking the API
    def run_checks():
        from concurrent.futures import ThreadPoolExecutor, as_completed
        logger.info(f"Starting parallel checks for all hosts in {environment}")
        start_time = time.time()
        
        # Load current status
        current_status = load_status(environment)
        host_statuses = {}
        status_changed = False
        
        # Calculate effective max workers based on config
        max_workers = Config.MAX_WORKERS
        if hasattr(Config, 'MAX_CONCURRENT_HOSTS') and Config.MAX_CONCURRENT_HOSTS > 0:
            max_workers = min(max_workers, Config.MAX_CONCURRENT_HOSTS)
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all host checks in parallel
            future_to_host = {
                executor.submit(monitor_host_worker, host, username, password): host['id']
                for host in hosts
            }
            
            # Process results as they complete
            for future in as_completed(future_to_host):
                host_id = future_to_host[future]
                try:
                    host_status = future.result()
                    if host_status:
                        if host_status.get('status_changed', False):
                            status_changed = True
                        host_statuses[host_id] = host_status
                except Exception as e:
                    logger.error(f"Error checking host {host_id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Add error status
                    host_statuses[host_id] = {
                        'instance_status': 'error',
                        'datasources': [],
                        'deployments': [],
                        'last_check': datetime.now().isoformat(),
                        'error': str(e),
                        'status_changed': True
                    }
                    status_changed = True
                
                # Update status file incrementally as each host completes
                # This provides faster feedback while the full check runs
                if len(host_statuses) % 3 == 0 or len(host_statuses) == len(hosts):
                    # Every 3 hosts or when all hosts are done, update the status file
                    try:
                        updated_status = load_status(environment)  # Get fresh copy to avoid overwriting
                        
                        # Add all processed host statuses
                        for h_id, h_status in host_statuses.items():
                            updated_status[h_id] = h_status
                        
                        # Add metadata for manual check
                        updated_status['_manual_check'] = True
                        updated_status['_manual_check_all'] = True
                        updated_status['_manual_check_time'] = datetime.now().isoformat()
                        updated_status['_manual_check_progress'] = f"{len(host_statuses)}/{len(hosts)}"
                        
                        if status_changed:
                            updated_status['_status_changed_at'] = datetime.now().isoformat()
                        
                        # Save the current progress
                        save_status(updated_status, environment)
                        logger.info(f"Updated status file with {len(host_statuses)}/{len(hosts)} hosts processed")
                    except Exception as e:
                        logger.error(f"Error updating status file during incremental update: {str(e)}")
        
        # Final update after all hosts are processed
        try:
            updated_status = load_status(environment)  # Get fresh copy
            
            # Add all host statuses
            for host_id, host_status in host_statuses.items():
                updated_status[host_id] = host_status
            
            # Add metadata for manual check
            updated_status['_manual_check'] = True
            updated_status['_manual_check_all'] = True
            updated_status['_manual_check_time'] = datetime.now().isoformat()
            updated_status['_manual_check_completed'] = datetime.now().isoformat()
            updated_status['_manual_check_duration'] = f"{time.time() - start_time:.2f}s"
            
            if status_changed:
                updated_status['_status_changed_at'] = datetime.now().isoformat()
            
            # Save the final status
            save_status(updated_status, environment)
        except Exception as e:
            logger.error(f"Error updating status file after completing all checks: {str(e)}")
        
        elapsed = time.time() - start_time
        logger.info(f"Completed all host checks in {elapsed:.2f} seconds. Processed {len(host_statuses)} hosts.")

    check_thread = threading.Thread(target=run_checks)
    check_thread.daemon = True
    check_thread.start()

    return jsonify({
        'message': 'Check initiated for all hosts',
        'host_count': len(hosts),
        'request_time': datetime.now().isoformat()
    }), 200

@monitor_bp.route('/<environment>/debug', methods=['GET'])
@token_required
def debug_environment(current_user, environment):
    """Get debug information for the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    # Get environment details
    hosts = load_hosts(environment)
    status = load_status(environment)
    
    # Get JBoss credentials
    username, password = get_jboss_credentials(environment)
    has_credentials = bool(username and password)
    
    # Get file permissions and directory structure
    from hosts.routes import get_environment_path
    env_path = get_environment_path(environment)
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
        'last_modified': datetime.fromtimestamp(os.path.getmtime(status_file)).isoformat() if os.path.exists(status_file) else None,
        'metadata': {k: v for k, v in status.items() if k.startswith('_')}
    }
    
    # Get thread pool stats
    thread_stats = {
        'max_workers': Config.MAX_WORKERS,
        'thread_timeout': Config.CLI_TIMEOUT,  # Using CLI_TIMEOUT as THREAD_TIMEOUT might not exist
        'active_threads': threading.active_count(),
        'current_thread': threading.current_thread().name
    }
    
    if hasattr(Config, 'MAX_CONCURRENT_HOSTS'):
        thread_stats['max_concurrent_hosts'] = Config.MAX_CONCURRENT_HOSTS
    
    # Get host status summary
    host_summary = {
        'total': len(hosts),
        'up': sum(1 for h_id, h in status.items() if not h_id.startswith('_') and h.get('instance_status') == 'up'),
        'down': sum(1 for h_id, h in status.items() if not h_id.startswith('_') and h.get('instance_status') == 'down'),
        'error': sum(1 for h_id, h in status.items() if not h_id.startswith('_') and h.get('instance_status') == 'error'),
        'unknown': sum(1 for h_id, h in status.items() if not h_id.startswith('_') and h.get('instance_status') not in ['up', 'down', 'error'])
    }
    
    # Get last check times for all hosts
    host_check_times = {}
    for h_id, h in status.items():
        if not h_id.startswith('_') and 'last_check' in h:
            host_check_times[h_id] = h['last_check']
    
    response = jsonify({
        'environment': environment,
        'host_count': len(hosts),
        'status_count': len([k for k in status.keys() if not k.startswith('_')]),
        'has_credentials': has_credentials,
        'env_directory': env_stats,
        'status_file': status_stats,
        'thread_stats': thread_stats,
        'host_summary': host_summary,
        'host_check_times': host_check_times,
        'config': {
            'monitoring_interval': Config.MONITORING_INTERVAL,
            'cli_timeout': Config.CLI_TIMEOUT,
        },
        'server_time': datetime.now().isoformat()
    })
    
    # Add cache control headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response, 200

@monitor_bp.route('/<environment>/status/<host_id>', methods=['DELETE'])
@token_required
def clear_host_status(current_user, environment, host_id):
    """Clear status for a specific host"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    status = load_status(environment)
    
    if host_id in status:
        del status[host_id]
        # Add metadata for this operation
        status['_host_status_cleared'] = host_id
        status['_host_status_cleared_at'] = datetime.now().isoformat()
        status['_host_status_cleared_by'] = current_user['username']
        
        save_status(status, environment)
        return jsonify({
            'message': 'Host status cleared successfully',
            'host_id': host_id,
            'cleared_at': datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            'message': 'Host status not found',
            'host_id': host_id
        }), 404

@monitor_bp.route('/<environment>/status/metadata', methods=['GET'])
@token_required
def get_status_metadata(current_user, environment):
    """Get just the status metadata for fast polling"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    # Load status
    status = load_status(environment)
    
    # Extract metadata (keys starting with _)
    metadata = {k: v for k, v in status.items() if k.startswith('_')}
    
    # Add server timestamp
    metadata['server_time'] = datetime.now().isoformat()
    
    # Add some stats
    metadata['host_count'] = len([k for k in status.keys() if not k.startswith('_')])
    metadata['up_count'] = sum(1 for h_id, h in status.items() 
                              if not h_id.startswith('_') and h.get('instance_status') == 'up')
    metadata['down_count'] = sum(1 for h_id, h in status.items() 
                                if not h_id.startswith('_') and h.get('instance_status') == 'down')
    
    response = jsonify(metadata)
    
    # Add cache control headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response, 200
