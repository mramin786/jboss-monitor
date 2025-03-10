# Backend Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Security Settings
SECRET_KEY=your_very_secret_development_key
JWT_SECRET_KEY=your_very_secret_jwt_key

# .env file in backend directory
# System-wide JBoss CLI Credentials for Monitoring

# Production Environment Credentials
PROD_JBOSS_USERNAME=your_production_username
PROD_JBOSS_PASSWORD=your_production_password

# Non-Production Environment Credentials
NONPROD_JBOSS_USERNAME=your_production_username
NONPROD_JBOSS_PASSWORD=your_production_username
# Monitoring Configuration
MONITORING_INTERVAL=60
CLI_TIMEOUT=30
MAX_WORKERS=10
~                           
