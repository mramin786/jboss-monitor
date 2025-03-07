# reports/routes.py
from flask import Blueprint, request, jsonify, send_file
import os
import json
import uuid
import threading
from datetime import datetime
import time

from auth.routes import token_required
from config import Config
from hosts.routes import load_hosts, get_environment_path
from monitor.routes import load_status, monitor_host
from reports.generator import generate_pdf_report, generate_csv_report

reports_bp = Blueprint('reports', __name__)

def get_report_file(report_id, format):
    """Get the report file path"""
    filename = f"{report_id}.{format}"
    return os.path.join(Config.REPORTS_PATH, filename)

def get_reports_index_file():
    """Get the reports index file path"""
    return os.path.join(Config.REPORTS_PATH, 'reports_index.json')

def load_reports_index():
    """Load reports index from file storage"""
    index_file = get_reports_index_file()
    if os.path.exists(index_file):
        with open(index_file, 'r') as f:
            return json.load(f)
    return []

def save_reports_index(reports):
    """Save reports index to file storage"""
    index_file = get_reports_index_file()
    with open(index_file, 'w') as f:
        json.dump(reports, f, indent=2)

@reports_bp.route('/', methods=['GET'])
@token_required
def get_reports(current_user):
    """Get all reports"""
    reports = load_reports_index()
    
    # Sort by creation date (newest first)
    reports.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify(reports), 200

@reports_bp.route('/<environment>/generate', methods=['POST'])
@token_required
def generate_report(current_user, environment):
    """Generate a new report for the specified environment"""
    if environment not in ['production', 'non_production']:
        return jsonify({'message': 'Invalid environment'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Missing request data'}), 400
    
    # Get JBoss credentials
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'JBoss credentials are required'}), 400
    
    # Report format
    format = data.get('format', 'pdf').lower()
    if format not in ['pdf', 'csv']:
        return jsonify({'message': 'Invalid report format'}), 400
    
    # Generate report ID
    report_id = str(uuid.uuid4())
    
    # Create report entry
    report = {
        'id': report_id,
        'environment': environment,
        'format': format,
        'created_by': current_user['username'],
        'created_at': datetime.now().isoformat(),
        'status': 'generating',
        'filename': f"{report_id}.{format}"
    }
    
    # Update reports index
    reports = load_reports_index()
    reports.append(report)
    save_reports_index(reports)
    
    # Get hosts for the environment
    hosts = load_hosts(environment)
    
    # Start a thread to generate the report
    def generate_report_thread():
        try:
            # First, update all host statuses
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = []
                for host in hosts:
                    futures.append(
                        executor.submit(monitor_host, environment, host, username, password)
                    )
                
                # Wait for all status updates to complete
                for future in as_completed(futures):
                    future.result()
            
            # Load the updated status
            status = load_status(environment)
            
            # Combine hosts with their status
            host_status = []
            for host in hosts:
                host_id = host['id']
                host_status.append({
                    **host,
                    'status': status.get(host_id, {
                        'instance_status': 'unknown',
                        'datasources': [],
                        'deployments': [],
                        'last_check': None
                    })
                })
            
            # Generate the report file
            if format == 'pdf':
                generate_pdf_report(report_id, environment, host_status)
            else:  # CSV
                generate_csv_report(report_id, environment, host_status)
            
            # Update report status
            reports = load_reports_index()
            for r in reports:
                if r['id'] == report_id:
                    r['status'] = 'completed'
                    r['completed_at'] = datetime.now().isoformat()
                    break
            
            save_reports_index(reports)
        
        except Exception as e:
            # Update report status to failed
            reports = load_reports_index()
            for r in reports:
                if r['id'] == report_id:
                    r['status'] = 'failed'
                    r['error'] = str(e)
                    break
            
            save_reports_index(reports)
    
    # Start report generation thread
    report_thread = threading.Thread(target=generate_report_thread)
    report_thread.daemon = True
    report_thread.start()
    
    return jsonify(report), 201

@reports_bp.route('/<report_id>', methods=['GET'])
@token_required
def get_report(current_user, report_id):
    """Get report details"""
    reports = load_reports_index()
    
    # Find the report by ID
    report = None
    for r in reports:
        if r['id'] == report_id:
            report = r
            break
    
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    return jsonify(report), 200

@reports_bp.route('/<report_id>/download', methods=['GET'])
@token_required
def download_report(current_user, report_id):
    """Download a report file"""
    reports = load_reports_index()
    
    # Find the report by ID
    report = None
    for r in reports:
        if r['id'] == report_id:
            report = r
            break
    
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    if report['status'] != 'completed':
        return jsonify({'message': 'Report is not ready for download'}), 400
    
    # Get the report file path
    report_file = get_report_file(report_id, report['format'])
    
    if not os.path.exists(report_file):
        return jsonify({'message': 'Report file not found'}), 404
    
    # Set content type based on format
    content_type = 'application/pdf' if report['format'] == 'pdf' else 'text/csv'
    
    # Generate a more descriptive filename
    filename = f"jboss_monitor_{report['environment']}_{datetime.now().strftime('%Y%m%d')}_{report_id[:8]}.{report['format']}"
    
    return send_file(
        report_file,
        mimetype=content_type,
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route('/<report_id>', methods=['DELETE'])
@token_required
def delete_report(current_user, report_id):
    """Delete a report"""
    reports = load_reports_index()
    
    # Find the report by ID
    report_index = None
    for i, r in enumerate(reports):
        if r['id'] == report_id:
            report_index = i
            report = r
            break
    
    if report_index is None:
        return jsonify({'message': 'Report not found'}), 404
    
    # Delete the report file
    report_file = get_report_file(report_id, report['format'])
    if os.path.exists(report_file):
        os.remove(report_file)
    
    # Remove from index
    del reports[report_index]
    save_reports_index(reports)
    
    return jsonify({
        'message': 'Report deleted successfully'
    }), 200
