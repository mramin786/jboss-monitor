# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import os
from threading import Thread
import time

# Import modules
from auth.routes import auth_bp
from hosts.routes import hosts_bp
from monitor.routes import monitor_bp
from reports.routes import reports_bp
from monitor.tasks import start_monitoring_worker

# Import config
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app)

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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "operational"})

if __name__ == '__main__':
    create_directories()
    # Start background monitoring thread
    monitoring_thread = Thread(target=start_monitoring_worker)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
