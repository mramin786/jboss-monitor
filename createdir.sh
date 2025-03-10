#!/bin/bash

BASE_DIR="jboss-monitor-backend"

# Define directory structure
DIRS=(
    "auth" "hosts" "monitor" "reports" "storage"
    "storage/environments/production" "storage/environments/non_production" "storage/users"
)

# Define files and their contents
declare -A FILES
FILES=(
    ["app.py"]="# Flask application entry point"
    ["config.py"]="# Configuration settings"
    ["requirements.txt"]="# Python dependencies"
    ["auth/routes.py"]="# Auth API endpoints"
    ["auth/models.py"]="# User models"
    ["auth/utils.py"]="# Auth helper functions"
    ["hosts/routes.py"]="# Host API endpoints"
    ["hosts/models.py"]="# Host and instance models"
    ["hosts/utils.py"]="# Host-related utilities"
    ["monitor/routes.py"]="# Monitoring API endpoints"
    ["monitor/cli_executor.py"]="# JBoss CLI command executor"
    ["monitor/datasource.py"]="# Datasource monitoring"
    ["monitor/deployment.py"]="# WAR file monitoring"
    ["monitor/tasks.py"]="# Background monitoring tasks"
    ["reports/routes.py"]="# Report API endpoints"
    ["reports/generator.py"]="# Report generation logic"
    ["reports/exporters.py"]="# PDF and CSV exporters"
    ["storage/data_manager.py"]="# Data persistence logic"
)

# Create directories
mkdir -p "$BASE_DIR"
for dir in "${DIRS[@]}"; do
    mkdir -p "$BASE_DIR/$dir"
    touch "$BASE_DIR/$dir/__init__.py"
    echo "# Init file for $dir" > "$BASE_DIR/$dir/__init__.py"
    echo "Created directory: $BASE_DIR/$dir"
done

# Create files with content
for file in "${!FILES[@]}"; do
    echo -e "${FILES[$file]}" > "$BASE_DIR/$file"
    echo "Created file: $BASE_DIR/$file"
done

echo "Project structure created successfully in $BASE_DIR/"
