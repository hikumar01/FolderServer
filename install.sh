#!/bin/bash

echo "🔧 Installing FolderServer dependencies..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Try different installation methods
echo "📦 Attempting to install Flask and Werkzeug..."
echo ""

# Method 1: Try standard pip install
echo "Method 1: Standard pip install..."
if pip3 install Flask Werkzeug 2>/dev/null; then
    echo "✅ Installation successful!"
    exit 0
fi

# Method 2: Try with --user flag
echo "Method 1 failed. Trying Method 2: User installation..."
if pip3 install --user Flask Werkzeug 2>/dev/null; then
    echo "✅ Installation successful!"
    exit 0
fi

# Method 3: Try with --trusted-host (for SSL issues)
echo "Method 2 failed. Trying Method 3: With trusted hosts (SSL bypass)..."
if pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org Flask Werkzeug 2>/dev/null; then
    echo "✅ Installation successful!"
    exit 0
fi

# Method 4: Try with sudo (last resort)
echo "Method 3 failed. Trying Method 4: With sudo..."
echo "⚠️  You may be prompted for your password..."
if sudo pip3 install Flask Werkzeug 2>/dev/null; then
    echo "✅ Installation successful!"
    exit 0
fi

# All methods failed
echo ""
echo "❌ All installation methods failed."
echo ""
echo "Please try manual installation:"
echo "  1. Create a virtual environment:"
echo "     python3 -m venv venv"
echo "     source venv/bin/activate"
echo "     pip install Flask Werkzeug"
echo ""
echo "  2. Or install with brew (macOS):"
echo "     brew install python3"
echo "     pip3 install Flask Werkzeug"
echo ""
exit 1
