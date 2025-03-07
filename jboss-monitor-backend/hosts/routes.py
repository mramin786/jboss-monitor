# hosts/routes.py
from flask import Blueprint, request, jsonify
import os
import json
import uuid
from datetime import datetime

from auth.routes import token_required
from config import Config

hosts_bp = Blueprint('hosts', __name__)

def get_environment_path(environment):
    """Get the storage path for the specified environment"""
    if environment == 'production':
        return Config.PROD_ENV_PATH
    else:
        return Config.NONPROD_ENV_PATH

def get_hosts_file(environment):
    """Get the hosts file path for the specified environment"""
    return os.path.join(get_environment_path(environment), 'hosts.json')

def load_hosts(environment):
    """Load hosts from file storage"""
    hosts_file = get_hosts_file(environment)
    if os.path.exists(hosts_file):
        with open(hosts_file, 'r') as f:
            return json.load(f)
    return []

def save_hosts(hosts, environment):
    """Save hosts to file storage"""
    hosts_file = get_hosts_file(environment)
    with open(hosts_file, 'w') as f:
        json.dump(hosts, f, indent=2)

def is_host_unique(hosts, host, port):
    """Check if host and port combination is unique"""
    for existing_host in hosts:
        if existing_host['host'] == host and existing_host['port'] == port:
            return False
    return True

@hosts_bp.route('/<environment>', methods=['GET'])
@token_required
def get_hosts(current_user, environment):
    """Get all hosts for the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    hosts = load_hosts(environment)
    return jsonify(hosts), 200

@hosts_bp.route('/<environment>', methods=['POST'])
@token_required
def add_host(current_user, environment):
    """Add a new host to the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    data = request.get_json()
    
    if not data or not data.get('host') or not data.get('port') or not data.get('instance'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    hosts = load_hosts(environment)
    
    # Check if host and port combination is unique
    if not is_host_unique(hosts, data['host'], data['port']):
        return jsonify({'message': 'Host and port combination already exists'}), 409
    
    # Create new host entry
    host_entry = {
        'id': str(uuid.uuid4()),
        'host': data['host'],
        'port': data['port'],
        'instance': data['instance'],
        'added_by': current_user['username'],
        'added_at': datetime.now().isoformat(),
        'last_check': None,
        'status': 'pending'
    }
    
    hosts.append(host_entry)
    save_hosts(hosts, environment)
    
    return jsonify(host_entry), 201

@hosts_bp.route('/<environment>/bulk', methods=['POST'])
@token_required
def add_hosts_bulk(current_user, environment):
    """Add multiple hosts in bulk to the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    data = request.get_json()
    
    if not data or not isinstance(data, list):
        return jsonify({'message': 'Expected array of host entries'}), 400
    
    hosts = load_hosts(environment)
    added_hosts = []
    rejected_hosts = []
    
    for entry in data:
        if not entry.get('host') or not entry.get('port') or not entry.get('instance'):
            rejected_hosts.append({
                'entry': entry,
                'reason': 'Missing required fields'
            })
            continue
        
        # Check if host and port combination is unique
        if not is_host_unique(hosts, entry['host'], entry['port']):
            rejected_hosts.append({
                'entry': entry,
                'reason': 'Host and port combination already exists'
            })
            continue
        
        # Create new host entry
        host_entry = {
            'id': str(uuid.uuid4()),
            'host': entry['host'],
            'port': entry['port'],
            'instance': entry['instance'],
            'added_by': current_user['username'],
            'added_at': datetime.now().isoformat(),
            'last_check': None,
            'status': 'pending'
        }
        
        hosts.append(host_entry)
        added_hosts.append(host_entry)
    
    if added_hosts:
        save_hosts(hosts, environment)
    
    return jsonify({
        'added': added_hosts,
        'rejected': rejected_hosts,
        'total_added': len(added_hosts),
        'total_rejected': len(rejected_hosts)
    }), 200

@hosts_bp.route('/<environment>/parse-bulk', methods=['POST'])
@token_required
def parse_bulk_input(current_user, environment):
    """Parse bulk input in the format: $host $port $jvm"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    data = request.get_json()
    
    if not data or not data.get('input'):
        return jsonify({'message': 'Missing input data'}), 400
    
    # Parse input lines in format: $host $port $jvm
    lines = data['input'].strip().split('\n')
    parsed_hosts = []
    invalid_lines = []
    
    for i, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) >= 3:
            host = parts[0]
            try:
                port = int(parts[1])
                instance = parts[2]
                parsed_hosts.append({
                    'host': host,
                    'port': port,
                    'instance': instance
                })
            except ValueError:
                invalid_lines.append({
                    'line': i + 1,
                    'content': line,
                    'reason': 'Port must be a number'
                })
        else:
            invalid_lines.append({
                'line': i + 1,
                'content': line,
                'reason': 'Invalid format, expected: $host $port $jvm'
            })
    
    return jsonify({
        'parsed_hosts': parsed_hosts,
        'invalid_lines': invalid_lines,
        'total_valid': len(parsed_hosts),
        'total_invalid': len(invalid_lines)
    }), 200

@hosts_bp.route('/<environment>/<host_id>', methods=['DELETE'])
@token_required
def delete_host(current_user, environment, host_id):
    """Delete a host from the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    hosts = load_hosts(environment)
    
    # Find the host by ID
    host_index = None
    for i, host in enumerate(hosts):
        if host['id'] == host_id:
            host_index = i
            break
    
    if host_index is None:
        return jsonify({'message': 'Host not found'}), 404
    
    # Remove host
    deleted_host = hosts.pop(host_index)
    save_hosts(hosts, environment)
    
    return jsonify({
        'message': 'Host deleted successfully',
        'deleted_host': deleted_host
    }), 200
