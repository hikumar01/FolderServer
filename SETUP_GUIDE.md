# Quick Setup Guide for Large File Upload Support

## 🎯 What Was Changed

Your file upload server now supports **large files (>2MB)** with an automatic fallback mechanism:

- **Small files (< 2MB)**: Use the original `http.server` (fast, lightweight)
- **Large files (≥ 2MB)**: Automatically use Flask server (reliable, up to 10GB)

## 🚀 Quick Start

### Step 1: Install Flask

Choose ONE method that works for you:

#### Option A: Virtual Environment (Recommended)
```bash
cd /Users/hikumar/src/FolderServer
python3 -m venv venv
source venv/bin/activate
pip install Flask Werkzeug
```

#### Option B: User Installation
```bash
pip3 install --user Flask Werkzeug
```

#### Option C: System Installation (requires password)
```bash
sudo pip3 install Flask Werkzeug
```

#### Option D: Use Install Script
```bash
./install.sh
```

### Step 2: Start the Server

```bash
./run.sh
```

You should see:
```
✅ Main Server (http.server) running at http://YOUR_IP:8080
✅ Large File Server (Flask) running at http://YOUR_IP:8081
📂 Upload directory: /Users/hikumar/src/FolderServer/uploads
📏 Files < 2MB: http.server | Files >= 2MB: Flask (up to 10GB)
```

### Step 3: Upload Files

1. Open browser to `http://YOUR_IP:8080`
2. Drag and drop files or folders
3. Watch the automatic routing:
   - Small files → Port 8080 (http.server)
   - Large files → Port 8081 (Flask) with "(Large file - using fallback server)" indicator

## 🔧 How It Works

### Architecture

```
Browser
   │
   ├─ File < 2MB ──────────► Port 8080 (http.server)
   │                          • Fast & lightweight
   │                          • Original Python server
   │
   └─ File ≥ 2MB ──────────► Port 8081 (Flask)
                               • Reliable for large files
                               • Handles up to 10GB
                               • Production-grade
```

### Automatic Fallback

The JavaScript client detects file size and automatically:
1. Routes small files to port 8080
2. Routes large files to port 8081
3. Displays progress for both

### Server-Side Protection

The http.server checks `Content-Length` header:
- If < 2MB: Process normally
- If ≥ 2MB: Return 307 redirect to Flask (safety fallback)

## 📝 Configuration

Edit `server.py` to customize:

```python
MAX_HTTP_SERVER_SIZE = 2 * 1024 * 1024      # 2MB threshold
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024     # 10GB max
PORT = 8080                                  # Main port
FLASK_PORT = 8081                            # Fallback port
```

## ✅ Testing

### Test Small File (http.server)
```bash
# Create a small test file
echo "Small test" > test_small.txt
# Upload via browser - should use port 8080
```

### Test Large File (Flask)
```bash
# Create a 3MB test file
dd if=/dev/zero of=test_large.bin bs=1048576 count=3
# Upload via browser - should use port 8081 with fallback indicator
```

## 🐛 Troubleshooting

### Flask Not Installed Error
```
ModuleNotFoundError: No module named 'flask'
```

**Solution**: Install Flask using one of the methods in Step 1

### Both Ports Busy
```
OSError: [Errno 48] Address already in use
```

**Solution**: Kill existing processes
```bash
lsof -ti:8080 | xargs kill -9
lsof -ti:8081 | xargs kill -9
```

### SSL Certificate Error (macOS)
```
SSLCertVerificationError
```

**Solution**: Install Python certificates
```bash
/Applications/Python\ 3.10/Install\ Certificates.command
```

Or use trusted hosts:
```bash
pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org Flask Werkzeug
```

### Permission Denied
```
OSError: [Errno 1] Operation not permitted
```

**Solution**: Use virtual environment or sudo

## 📊 What Changed in Each File

### `server.py`
- ✅ Added Flask import and configuration
- ✅ Created Flask routes for large file handling
- ✅ Added size check in `do_POST()` method
- ✅ Implemented two-server startup (http.server + Flask)
- ✅ Added graceful shutdown for both servers

### `index.html`
- ✅ Added Flask port and size threshold constants
- ✅ Modified `uploadFile()` to detect large files
- ✅ Auto-route to Flask for large files
- ✅ Added response parsing for both server types
- ✅ Added "(Large file)" indicator in progress

### New Files
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Full documentation
- ✅ `SETUP_GUIDE.md` - This quick start guide
- ✅ `install.sh` - Automated installation script

## 🎓 Benefits

| Feature | Before | After |
|---------|--------|-------|
| Small files (< 2MB) | ✅ Works | ✅ Works (unchanged) |
| Large files (≥ 2MB) | ❌ Fails/unreliable | ✅ Works reliably |
| Maximum file size | ~2MB | 10GB (configurable) |
| Memory usage | High (loads all to RAM) | Efficient (streaming) |
| Concurrent uploads | 5 | 5 (unchanged) |
| Browser support | Chrome only | Chrome only (unchanged) |

## 🔐 Security

All existing security features maintained:
- ✅ Path traversal protection
- ✅ Upload directory isolation
- ✅ File versioning
- ✅ **NEW**: File size limits enforced

## 📞 Need Help?

Check logs when running the server - both servers output status messages:
- `[UPLOAD]` - File successfully uploaded
- `[SKIP]` - Duplicate file (same content)
- `[ERROR]` - Upload failed

---

**Ready to test?** Install Flask (Step 1) and run `./run.sh` (Step 2)!
