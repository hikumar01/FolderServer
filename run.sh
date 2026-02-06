#!/bin/bash

echo "🚀 Starting FolderServer..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask is not installed!"
    echo ""
    echo "Flask is required for large file uploads (≥2MB)."
    echo ""
    echo "Install options:"
    echo "  1. Run:  ./install.sh"
    echo "  2. Or:   pip3 install Flask Werkzeug"
    echo "  3. Or:   python3 -m venv venv && source venv/bin/activate && pip install Flask Werkzeug"
    echo ""
    read -p "Would you like to run ./install.sh now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./install.sh
        if [ $? -ne 0 ]; then
            echo "❌ Installation failed. Please install manually."
            exit 1
        fi
    else
        echo "❌ Cannot start server without Flask. Exiting."
        exit 1
    fi
fi

# Check if Werkzeug is installed
if ! python3 -c "import werkzeug" 2>/dev/null; then
    echo "❌ Werkzeug is not installed!"
    echo "Run: pip3 install Werkzeug"
    exit 1
fi

# Get the IP address
# Try multiple methods to get the IP
if command -v ipconfig &> /dev/null; then
    # macOS
    IP=$(ipconfig getifaddr en0 2>/dev/null)
    if [ -z "$IP" ]; then
        IP=$(ipconfig getifaddr en1 2>/dev/null)
    fi
elif command -v hostname &> /dev/null; then
    # Linux/Unix
    IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

# Fallback to localhost if no IP found
if [ -z "$IP" ]; then
    IP="localhost"
    echo "⚠️  Could not detect IP address, using localhost"
fi

echo "✅ All dependencies found"
echo "🌐 Server IP: $IP"
echo ""

# Start the server
python3 server.py "$IP"
