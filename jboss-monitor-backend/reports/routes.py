# reports/routes.py
from flask import Blueprint, request, jsonify, send_file
import os
import json
import logging
import uuid
import threading
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from reports.comparison import compare_reports, generate_comparison_pdf
from auth.routes import token_required
from config import Config
from hosts.routes import load_hosts, get_environment_path
from monitor.routes import load_status, monitor_host
from reports.generator import generate_pdf_report, generate_csv_report
from reports.utils import rotate_reports

reports_bp = Blueprint('reports', __name__)
# Configure logging
logger = logging.getLogger(__name__)
@reports_bp.route('/compare', methods=['POST'])
@token_required
def compare_reports_endpoint(current_user):
    """Compare two reports and return the differences"""
    try:
        data = request.get_json()
        
        if not data or not data.get('report1_id') or not data.get('report2_id'):
            return jsonify({'message': 'Missing required report IDs'}), 400
        
        report1_id = data.get('report1_id')
        report2_id = data.get('report2_id')
        
        # Compare the reports
        comparison_result = compare_reports(report1_id, report2_id)
        
        if 'error' in comparison_result:
            return jsonify({'message': comparison_result['error']}), 400
        
        # Generate a unique ID for this comparison
        comparison_id = str(uuid.uuid4())
        
        # Get comparison summary to return to the client
        comparison_summary = {
            'id': comparison_id,
            'report1_id': report1_id,
            'report2_id': report2_id,
            'created_at': datetime.now().isoformat(),
            'created_by': current_user['username'],
            'summary': comparison_result['summary']
        }
        
        # Generate a PDF report of the comparison asynchronously in a thread
        def generate_pdf_thread():
            try:
                # Generate the PDF
                generate_comparison_pdf(comparison_id, comparison_result)
                
                # Load the reports index
                reports_index_file = os.path.join(Config.REPORTS_PATH, 'reports_index.json')
                reports = load_reports_index()
                
                # Add the comparison report to the index
                report_entry = {
                    'id': comparison_id,
                    'type': 'comparison',
                    'report1_id': report1_id,
                    'report2_id': report2_id,
                    'environment': comparison_result['report1']['environment'],
                    'format': 'pdf',
                    'created_by': current_user['username'],
                    'created_at': datetime.now().isoformat(),
                    'status': 'completed',
                    'filename': f"{comparison_id}.pdf",
                    'completed_at': datetime.now().isoformat()
                }
                
                reports.append(report_entry)
                save_reports_index(reports)
                
                logger.info(f"Comparison report {comparison_id} generated successfully")
            except Exception as e:
                logger.error(f"Error generating comparison report: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Start the thread
        thread = threading.Thread(target=generate_pdf_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify(comparison_summary), 201
        
    except Exception as e:
        logger.error(f"Error in compare_reports endpoint: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'message': f'Error: {str(e)}'}), 500

@reports_bp.route('/comparisons', methods=['GET'])
@token_required
def get_comparisons(current_user):
    """Get all comparison reports"""
    try:
        reports = load_reports_index()
        
        # Filter out only comparison reports
        comparisons = [r for r in reports if r.get('type') == 'comparison']
        
        # Sort by creation date (newest first)
        comparisons.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Create response with cache control headers
        response = jsonify(comparisons)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
    except Exception as e:
        logger.error(f"Error in get_comparisons: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty array instead of error to prevent UI error
        response = jsonify([])
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response, 200

@reports_bp.route('/comparison/<comparison_id>/download', methods=['GET'])
@token_required
def download_comparison(current_user, comparison_id):
    """Download a comparison report"""
    try:
        reports = load_reports_index()
        
        # Find the comparison by ID
        comparison = next((r for r in reports if r['id'] == comparison_id), None)
        
        if not comparison:
            return jsonify({'message': 'Comparison report not found'}), 404
            
        if comparison.get('status') != 'completed':
            return jsonify({'message': 'Comparison report is not ready for download'}), 400
            
        # Get the report file path
        report_file = os.path.join(Config.REPORTS_PATH, f"{comparison_id}.pdf")
        
        if not os.path.exists(report_file):
            return jsonify({'message': 'Comparison report file not found'}), 404
            
        # Generate a more descriptive filename
        env = comparison.get('environment', 'environment')
        filename = f"jboss_comparison_{env}_{datetime.now().strftime('%Y%m%d')}_{comparison_id[:8]}.pdf"
        
        # Return with cache control headers
        response = send_file(
            report_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Error downloading comparison report: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'message': f'Error: {str(e)}'}), 500
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

    # Report format - Always use PDF now
    format = 'pdf'

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
                report_path = generate_pdf_report(report_id, environment, host_status)
                print(f"PDF report generated at: {report_path}")
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

            # Add report rotation after a successful report generation
            try:
                rotate_reports(environment, max_reports=Config.MAX_REPORTS_PER_ENV)
                print(f"Report rotation completed for {environment}")
            except Exception as rotation_error:
                print(f"Error rotating reports: {str(rotation_error)}")

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

@reports_bp.route('/cleanup', methods=['POST'])
@token_required
def cleanup_reports(current_user):
    """Manually trigger reports cleanup"""
    try:
        # Check if user is admin
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized. Admin role required'}), 403
            
        # Get max_reports parameter from request
        data = request.get_json() or {}
        max_reports = data.get('max_reports', Config.MAX_REPORTS_PER_ENV)
        environment = data.get('environment')  # Can be None to process all environments
        
        # Run cleanup
        deleted_count = rotate_reports(environment, max_reports)
        
        return jsonify({
            'message': f'Cleanup completed successfully',
            'deleted_count': deleted_count,
            'max_reports': max_reports,
            'environment': environment or 'all'
        }), 200
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
        
        # Get config info
        config_info = {
            'max_reports_per_env': Config.MAX_REPORTS_PER_ENV,
            'reports_cleanup_enabled': Config.REPORTS_CLEANUP_ENABLED
        }
        debug_info = {
            'reports_path': reports_path,
            'directory_exists': dir_exists,
            'directory_writable': dir_writable,
            'index_file': index_file,
            'index_exists': index_exists,
            'index_content': index_content,
            'report_files': report_files,
            'config': config_info
        }
        
        response = jsonify(debug_info)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response, 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
