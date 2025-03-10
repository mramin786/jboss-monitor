# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import os
from threading import Thread
import time
import logging
from datetime import datetime

# Basic logging setup - before other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import config
from config import Config

# Try to set up advanced logging
try:
    from logging_config import setup_logging
    logger = setup_logging()
    logger.info("Advanced logging configuration applied")
    use_advanced_logging = True
except ImportError as e:
    logger.warning(f"Could not set up advanced logging: {str(e)}")
    use_advanced_logging = False

# Now import modules
from auth.routes import auth_bp
from hosts.routes import hosts_bp
from monitor.routes import monitor_bp
from reports.routes import reports_bp
from monitor.tasks import start_monitoring_worker

# Try to import log cleanup
try:
    from log_cleanup import start_log_cleanup_worker
    use_log_cleanup = True
except ImportError as e:
    logger.warning(f"Could not import log cleanup: {str(e)}")
    use_log_cleanup = False

# Log application startup
logger.info("Starting JBoss Monitor application")

app = Flask(__name__)
app.config.from_object(Config)

# Record start time
app.start_time = time.time()

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(hosts_bp, url_prefix='/api/hosts')
app.register_blueprint(monitor_bp, url_prefix='/api/monitor')
app.register_blueprint(reports_bp, url_prefix='/api/reports')

# Create required directories if they don't exist
def create_directories():
    directories = [
        'storage/environments/production',
        'storage/environments/non_production',
        'storage/users',
        'storage/reports'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    logger.info("Created required storage directories")

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "operational"})

@app.route('/api/diagnostics', methods=['GET'])
def diagnostics():
    """Return diagnostic information about the application"""
    log_dir = Config.LOG_DIR
    
    # Get log file info
    log_files = []
    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            if file.endswith('.log') or '.log.' in file:
                file_path = os.path.join(log_dir, file)
                try:
                    size = os.path.getsize(file_path)
                    modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    log_files.append({
                        'name': file,
                        'size': size,
                        'size_human': f"{size/1024:.2f} KB",
                        'modified': modified
                    })
                except Exception as e:
                    logger.error(f"Error processing log file {file}: {str(e)}")
    
    # Get system info if psutil is available
    system_info = {}
    try:
        import psutil
        system_info = {
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'memory_percent': psutil.virtual_memory().percent,
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'disk_usage': psutil.disk_usage('/').percent
        }
    except ImportError:
        system_info = {"error": "psutil not available"}
    
    # Return diagnostics
    return jsonify({
        'status': 'operational',
        'uptime': time.time() - app.start_time,
        'log_files': log_files,
        'log_dir': log_dir,
        'system_info': system_info,
        'advanced_logging': use_advanced_logging,
        'log_cleanup': use_log_cleanup
    })

if __name__ == '__main__':
    # Create required directories
    create_directories()
    
    # Start log cleanup thread if available
    if use_log_cleanup:
        try:
            logger.info("Starting log cleanup worker")
            cleanup_thread = Thread(target=start_log_cleanup_worker)
            cleanup_thread.daemon = True
            cleanup_thread.start()
        except Exception as e:
            logger.error(f"Error starting log cleanup worker: {str(e)}")
    
    # Start background monitoring thread
    logger.info("Starting monitoring worker")
    monitoring_thread = Thread(target=start_monitoring_worker)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    # Log server startup
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on 0.0.0.0:{port}")
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
