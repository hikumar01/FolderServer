# Folder Upload Server

A Python-based file upload server with support for large files.

## Features

- ✅ Drag & drop folder/file upload
- ✅ Automatic fallback for large files (>2MB)
- ✅ Files < 2MB: Uses lightweight `http.server`
- ✅ Files >= 2MB: Uses Flask for reliable large file handling (up to 10GB)
- ✅ Automatic file versioning (prevents overwriting)
- ✅ Progress tracking
- ✅ Concurrent uploads (5 simultaneous)

## Installation

### Install Dependencies

```bash
pip3 install -r requirements.txt
```

If you encounter permission errors:

```bash
# Option 1: Use sudo (macOS/Linux)
sudo pip3 install -r requirements.txt

# Option 2: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Option 3: Install to user directory
pip3 install --user Flask Werkzeug
```

### SSL Certificate Issues (macOS)

If you see SSL certificate errors:

```bash
# Install certificates for Python
/Applications/Python\ 3.*/Install\ Certificates.command

# Or use trusted hosts
pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org Flask Werkzeug
```

## Usage

### Start the Server

```bash
./run.sh
```

Or manually:

```bash
python3 server.py $(ipconfig getifaddr en0)
```

### Access the Server

1. Open your browser to `http://YOUR_IP:8080`
2. Drag and drop folders or files
3. Files under 2MB use the fast http.server
4. Files 2MB and larger automatically use the Flask fallback server

## Architecture

### Two-Server Approach

The application runs **two concurrent servers**:

1. **Main Server (http.server)** - Port 8080
   - Handles small files (< 2MB)
   - Lightweight, minimal overhead
   - Known issue: Python's http.server has problems with files >2MB

2. **Fallback Server (Flask)** - Port 8081
   - Handles large files (>= 2MB)
   - Production-grade, reliable for large uploads
   - Maximum file size: 10GB (configurable)

### How It Works

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ├──── File < 2MB ──────► http.server (Port 8080)
       │
       └──── File >= 2MB ─────► Flask Server (Port 8081)
```

The JavaScript client automatically detects file size and routes to the appropriate server.

## Configuration

Edit `server.py` to change limits:

```python
MAX_HTTP_SERVER_SIZE = 2 * 1024 * 1024      # 2MB - threshold for Flask
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024     # 10GB - maximum upload size
PORT = 8080                                  # Main server port
FLASK_PORT = 8081                            # Flask server port
```

## File Versioning

When uploading a file that already exists:
- If content is identical: Upload is skipped
- If content differs: New version is created (e.g., `file (1).txt`, `file (2).txt`)

## Security Features

- ✅ Path traversal protection (prevents `../` attacks)
- ✅ Upload directory isolation
- ✅ File size limits
- ✅ Automatic directory creation with safety checks

## Troubleshooting

### "Module 'flask' not found"

Flask is not installed. Run:
```bash
pip3 install Flask Werkzeug
```

### "Permission denied" during install

Use one of these methods:
```bash
# Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Or sudo
sudo pip3 install Flask Werkzeug
```

### Large files still failing

1. Check server logs for errors
2. Verify both servers are running (check ports 8080 and 8081)
3. Increase `MAX_FILE_SIZE` in `server.py` if needed
4. Check available disk space

### Browser compatibility

This uploader uses Chrome-specific APIs. Use Chrome, Edge, or Brave browser.

## License

Open source - use as you wish.
