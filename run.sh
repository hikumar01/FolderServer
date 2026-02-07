#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    # source venv\Scripts\activate # Windows
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Install Python 3 first."
    exit 1
fi

# Check/Install Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Python Dependencies not found. Install using:"
    echo "   pip install -r requirements.txt"   
    exit 1
fi

# Get IP address
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")

# Start server
python3 server.py "$IP"
