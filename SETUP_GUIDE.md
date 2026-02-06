# Quick Setup Guide

## 🎯 Overview

Your file upload server now uses a **single Flask server** that efficiently handles files of any size (up to 10GB) using memory-efficient streaming.

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

#### Option B: Automated Installer
```bash
./install.sh
```

#### Option C: User Installation
```bash
pip3 install --user Flask Werkzeug
```

#### Option D: System Installation (requires password)
```bash
sudo pip3 install Flask Werkzeug
```

### Step 2: Start the Server

```bash
./run.sh
```

You should see:
```
✅ Server running at http://YOUR_IP:8080
📂 Upload directory: /Users/hikumar/src/FolderServer/uploads
📏 Maximum file size: 10GB
🔧 Chunk size: 8192 bytes (memory efficient)
🔁 Press Ctrl+C to stop...
```

### Step 3: Upload Files

1. Open browser to `http://YOUR_IP:8080`
2. Drag and drop files or folders
3. Watch the progress with file sizes displayed
4. All files handled by the same server efficiently

## 🔧 How It Works

### Single Server Architecture

```
Browser
   │
   └─ All files (any size) ──► Port 8080 (Flask)
                                 • Streams in 8KB chunks
                                 • Memory efficient
                                 • Up to 10GB per file
```

### Memory Efficiency

No matter the file size, the server only uses ~8KB of memory per upload:

| File Size | Server Memory | How? |
|-----------|--------------|------|
| 1 MB      | ~8 KB        | Streaming |
| 1 GB      | ~8 KB        | Streaming |
| 10 GB     | ~8 KB        | Streaming |

### Streaming Process

1. **Upload**: Browser sends file in multipart chunks
2. **Stream**: Server reads 8KB at a time, writes to disk
3. **Compare**: If file exists, compare chunk-by-chunk
4. **Version**: Create `file (1).ext` if different

## ✅ Testing

### Test Small File
```bash
echo "Small test file" > test_small.txt
# Upload via browser
```

### Test Large File (100MB)
```bash
dd if=/dev/zero of=test_100mb.bin bs=1048576 count=100
# Upload via browser - will show progress with file size
```

### Test Very Large File (1GB)
```bash
dd if=/dev/zero of=test_1gb.bin bs=1048576 count=1024
# Upload via browser - streams efficiently, no memory issues
```

## 📝 Configuration

Edit `server.py` to customize:

```python
UPLOAD_DIR = "./uploads"                        # Where files are stored
PORT = 8080                                      # Server port
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024         # 10GB max (change as needed)
CHUNK_SIZE = 8192                                # 8KB chunks (8192 is optimal)
```

### Increase Maximum File Size

To allow 50GB files:
```python
MAX_FILE_SIZE = 50 * 1024 * 1024 * 1024  # 50GB
```

### Change Port

To use port 9000 instead:
```python
PORT = 9000
```

## 🐛 Troubleshooting

### Flask Not Installed Error
```
ModuleNotFoundError: No module named 'flask'
```

**Solution**: Install Flask using Step 1 above

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```

**Solution**: Kill existing process
```bash
lsof -ti:8080 | xargs kill -9
```

### SSL Certificate Error (macOS)
```
SSLCertVerificationError
```

**Solution**: Install Python certificates
```bash
/Applications/Python\ 3.10/Install\ Certificates.command
```

Or use the installer script which handles this.

### Permission Denied During Install
```
OSError: [Errno 1] Operation not permitted
```

**Solution**: Use virtual environment (Option A in Step 1)

### Upload Fails or Hangs

1. **Check disk space**: `df -h`
2. **Check server logs**: Look at terminal output
3. **Check file size**: Ensure it's under MAX_FILE_SIZE
4. **Browser timeout**: Try Chrome (best for large uploads)

## 📊 What Changed

### Simplified Architecture

**Before:**
- Two servers (http.server + Flask)
- Two ports (8080 + 8081)
- Complex fallback logic
- http.server fails on files > 2MB

**After:**
- One server (Flask only)
- One port (8080)
- Simple, reliable
- Works for all file sizes

### Files Modified

1. **server.py**
   - Removed http.server completely
   - Single Flask server only
   - Added streaming file handler
   - Chunk-based comparison for duplicates

2. **index.html**
   - Removed dual-server logic
   - Single upload endpoint
   - Added file size display in progress

3. **run.sh**
   - Updated dependency checks
   - Simplified startup
   - Better error messages

4. **README.md** & **SETUP_GUIDE.md**
   - Updated documentation
   - Reflects new architecture

## 🎓 Benefits

| Feature | Value |
|---------|-------|
| Simplicity | Single server, one port |
| Memory | Constant ~8KB per upload |
| Reliability | Flask is production-grade |
| File Size | Up to 10GB (configurable) |
| Speed | No overhead from dual servers |
| Maintenance | Easier to debug and modify |

## 🔐 Security

All security features maintained:
- ✅ Path traversal protection
- ✅ Upload directory isolation
- ✅ File size limits
- ✅ Streaming prevents memory attacks

## 💡 Tips

### Multiple Concurrent Uploads

The server supports 5 concurrent uploads by default. All are streamed efficiently.

### Network Performance

Upload speed depends on your network:
- 100 Mbps → ~12 MB/s → 1GB in ~85 seconds
- 1 Gbps → ~125 MB/s → 1GB in ~8 seconds

### Disk I/O

Streaming writes are efficient. Even with slow HDDs, uploads work well because:
1. Writing happens as data arrives
2. No large buffers needed
3. OS handles disk caching

## 📞 Common Questions

**Q: Why Flask instead of http.server?**

A: Python's http.server has bugs with files > 2MB. Flask is production-ready and handles any size reliably.

**Q: Will large files crash the server?**

A: No! Streaming ensures constant low memory usage regardless of file size.

**Q: Can I upload 100 files at once?**

A: Yes, but only 5 upload simultaneously (to prevent overload). Others queue automatically.

**Q: What if two people upload the same file?**

A: Each gets their own copy. Versioning creates `file (1).ext`, `file (2).ext`, etc.

**Q: Does it work on Firefox?**

A: Folder upload requires Chrome APIs. Single file upload works on all browsers.

---

**Ready to use?** Run `./run.sh` and start uploading!
