#!/bin/bash
# Flexible startup script for Azure App Service

echo "=================================================="
echo "VALUATION AGENT BACKEND STARTING"
echo "=================================================="
echo "Python version check:"
python3 --version 2>/dev/null || echo "python3 not found"
python --version 2>/dev/null || echo "python not found"
echo "Working directory: $(pwd)"
echo "Environment PORT: $PORT"
echo "=================================================="

# Try python3 first, then python
if command -v python3 &> /dev/null; then
    echo "Using python3"
    python3 startup_flexible.py
elif command -v python &> /dev/null; then
    echo "Using python"
    python startup_flexible.py
else
    echo "❌ No Python interpreter found"
    exit 1
fi