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
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL') or 15)  # in seconds (reduced for more responsiveness)
    CLI_TIMEOUT = int(os.environ.get('CLI_TIMEOUT') or 30)  # CLI command timeout in seconds
    
    # JBoss CLI Credentials from Environment Variables
    PROD_JBOSS_USERNAME = os.environ.get('PROD_JBOSS_USERNAME')
    PROD_JBOSS_PASSWORD = os.environ.get('PROD_JBOSS_PASSWORD')
    NONPROD_JBOSS_USERNAME = os.environ.get('NONPROD_JBOSS_USERNAME')
    NONPROD_JBOSS_PASSWORD = os.environ.get('NONPROD_JBOSS_PASSWORD')
    
    # Multithreading settings - improved for better parallelism
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS') or 20)  # Maximum number of worker threads
    MAX_CONCURRENT_HOSTS = int(os.environ.get('MAX_CONCURRENT_HOSTS') or 0)  # 0 means no limit
    
    # Status file updates
    STATUS_UPDATE_LOCK_TIMEOUT = int(os.environ.get('STATUS_UPDATE_LOCK_TIMEOUT') or 10)  # Lock timeout for status file updates in seconds
    
    # Performance tweaks
    CLI_CONNECTION_POOL_SIZE = int(os.environ.get('CLI_CONNECTION_POOL_SIZE') or 10)  # Size of the connection pool for CLI commands
    
    # Logging configuration
    LOG_DIR = os.environ.get('LOG_DIR') or '/app/jbossmonit/logs'
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_MAX_DAYS = int(os.environ.get('LOG_MAX_DAYS') or 3)  # Maximum age of log files in days
    LOG_ROTATION = os.environ.get('LOG_ROTATION') or 'midnight'  # When to rotate logs
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')  # Enable debug mode
