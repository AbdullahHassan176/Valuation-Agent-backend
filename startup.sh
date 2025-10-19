#!/bin/bash
# Azure App Service startup script

echo "Starting Valuation Agent Backend..."

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start the application
echo "Starting FastAPI application..."
python startup.py
