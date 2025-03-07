# config.py
import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Authentication settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # File storage paths
    STORAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage')
    
    # Environment-specific storage paths
    PROD_ENV_PATH = os.path.join(STORAGE_PATH, 'environments', 'production')
    NONPROD_ENV_PATH = os.path.join(STORAGE_PATH, 'environments', 'non_production')
    USERS_PATH = os.path.join(STORAGE_PATH, 'users')
    REPORTS_PATH = os.path.join(STORAGE_PATH, 'reports')
    
    # Monitoring settings
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL') or 60)  # in seconds
    CLI_TIMEOUT = int(os.environ.get('CLI_TIMEOUT') or 30)  # CLI command timeout in seconds
    
    # Multithreading settings
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS') or 10)  # Maximum number of worker threads
