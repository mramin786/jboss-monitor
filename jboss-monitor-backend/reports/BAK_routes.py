# reports/routes.py
from flask import Blueprint, request, jsonify, send_file
import os
import json
import uuid
import threading
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    os.makedirs(os.path.dirname(index_file), exist_ok=True)
    with open(index_file, 'w') as f:
        json.dump(reports, f, indent=2)

@reports_bp.route('/', methods=['GET'])
@reports_bp.route('', methods=['GET'])
@token_required
def get_reports(current_user):
    """Get all reports"""
    try:
        # Ensure directory exists
        os.makedirs(Config.REPORTS_PATH, exist_ok=True)
        
        # Ensure index file exists
        index_file = get_reports_index_file()
        if not os.path.exists(index_file):
            with open(index_file, 'w') as f:
                json.dump([], f)
        
        reports = load_reports_index()
        
        # Sort by creation date (newest first)
        reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Create response with cache control headers
        response = jsonify(reports)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
    except Exception as e:
        import traceback
        print(f"Error in get_reports: {str(e)}")
        print(traceback.format_exc())
        # Return empty array instead of error to prevent UI error
        response = jsonify([])
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response, 200

@reports_bp.route('/<environment>/generate', methods=['POST'])  # No trailing slash
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

    # Ensure reports directory exists
    os.makedirs(Config.REPORTS_PATH, exist_ok=True)

    # Update reports index
    reports = load_reports_index()
    reports.append(report)
    save_reports_index(reports)

    # Get hosts for the environment
    hosts = load_hosts(environment)

    # Start a thread to generate the report
    def generate_report_thread():
        try:
            print(f"Starting report generation for report ID: {report_id}")
            
            # First, update all host statuses
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = []
                for host in hosts:
                    futures.append(
                        executor.submit(monitor_host, environment, host, username, password)
                    )

                # Wait for all status updates to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error updating host status: {str(e)}")

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
            try:
                if format == 'pdf':
                    report_path = generate_pdf_report(report_id, environment, host_status)
                    print(f"PDF report generated at: {report_path}")
                else:  # CSV
                    report_path = generate_csv_report(report_id, environment, host_status)
                    print(f"CSV report generated at: {report_path}")
            except Exception as e:
                import traceback
                print(f"Error generating report file: {str(e)}")
                print(traceback.format_exc())
                raise
            
            # Update report status
            reports = load_reports_index()
            for r in reports:
                if r['id'] == report_id:
                    r['status'] = 'completed'
                    r['completed_at'] = datetime.now().isoformat()
                    break

            save_reports_index(reports)
            print(f"Report {report_id} marked as completed")

        except Exception as e:
            import traceback
            print(f"Error in report generation thread: {str(e)}")
            print(traceback.format_exc())
            
            # Update report status to failed
            try:
                reports = load_reports_index()
                for r in reports:
                    if r['id'] == report_id:
                        r['status'] = 'failed'
                        r['error'] = str(e)
                        break
                save_reports_index(reports)
                print(f"Report {report_id} marked as failed: {str(e)}")
            except Exception as e2:
                print(f"Error updating report status: {str(e2)}")

    # Start report generation thread
    report_thread = threading.Thread(target=generate_report_thread)
    report_thread.daemon = True
    report_thread.start()

    # Return immediately with the report info
    response = jsonify(report)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response, 201

@reports_bp.route('/<report_id>', methods=['GET'])
@token_required
def get_report(current_user, report_id):
    """Get report details"""
    try:
        reports = load_reports_index()

        # Find the report by ID
        report = None
        for r in reports:
            if r['id'] == report_id:
                report = r
                break

        if not report:
            return jsonify({'message': 'Report not found'}), 404

        # Return with cache control headers
        response = jsonify(report)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@reports_bp.route('/<report_id>/download', methods=['GET'])
@token_required
def download_report(current_user, report_id):
    """Download a report file"""
    try:
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

        # Return with cache control headers
        response = send_file(
            report_file,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        import traceback
        print(f"Error downloading report: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'message': f'Error: {str(e)}'}), 500

@reports_bp.route('/<report_id>', methods=['DELETE'])  # No trailing slash
@token_required
def delete_report(current_user, report_id):
    """Delete a report"""
    try:
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

        # Return with cache control headers
        response = jsonify({
            'message': 'Report deleted successfully'
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response, 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@reports_bp.route('/debug', methods=['GET'])
@token_required
def debug_reports(current_user):
    """Debug endpoint to check reports system"""
    try:
        reports_path = Config.REPORTS_PATH
        index_file = get_reports_index_file()
        
        # Check reports directory
        dir_exists = os.path.exists(reports_path)
        dir_writable = os.access(reports_path, os.W_OK) if dir_exists else False
        
        # Check index file
        index_exists = os.path.exists(index_file)
        index_content = None
        if index_exists:
            try:
                with open(index_file, 'r') as f:
                    index_content = json.load(f)
            except Exception as e:
                index_content = f"Error reading index: {str(e)}"
        
        # Check report files
        report_files = []
        if dir_exists:
            for f in os.listdir(reports_path):
                if f.endswith('.pdf') or f.endswith('.csv'):
                    file_path = os.path.join(reports_path, f)
                    report_files.append({
                        'name': f,
                        'size': os.path.getsize(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
        
        debug_info = {
            'reports_path': reports_path,
            'directory_exists': dir_exists,
            'directory_writable': dir_writable,
            'index_file': index_file,
            'index_exists': index_exists,
            'index_content': index_content,
            'report_files': report_files
        }
        
        response = jsonify(debug_info)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response, 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
