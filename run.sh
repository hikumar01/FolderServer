#!/bin/bash

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Install Python 3 first."
    exit 1
fi

# Check/Install Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Python Dependencies not found. Run the following commands to install:"
    echo "   1. python3 -m venv venv"
    echo "   2. source venv/bin/activate"
    echo "   3. pip install -r requirements.txt"   
    exit 1
fi

# Get IP address
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)

# Start server
echo "Starting server on $IP:8080..."
python3 server.py "$IP"
