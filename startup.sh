#!/bin/bash
# Azure startup script that calls our Python startup
# Try different Python commands in order of preference
if command -v python3 &> /dev/null; then
    echo "Using python3"
    python3 startup.py
elif command -v python &> /dev/null; then
    echo "Using python"
    python startup.py
else
    echo "Python not found, trying /usr/bin/python3"
    /usr/bin/python3 startup.py
fi