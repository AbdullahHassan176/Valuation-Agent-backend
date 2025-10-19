#!/bin/bash
# Azure App Service startup script

echo "Starting Valuation Agent Backend..."

# Install dependencies if not already installed
if [ ! -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements-minimal.txt
else
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

# Start the application
echo "Starting FastAPI application..."
python startup.py
