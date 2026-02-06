# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Flask
```bash
./install.sh
```

### Step 2: Start Server
```bash
./run.sh
```

### Step 3: Upload Files
Open `http://YOUR_IP:8080` in Chrome, drag & drop files!

---

## 📋 Command Reference

| Task | Command |
|------|---------|
| Install dependencies | `./install.sh` |
| Start server | `./run.sh` |
| Stop server | Press `Ctrl+C` |
| Run tests | `./test_upload.sh` |
| Check if running | `curl http://localhost:8080/` |
| Kill port 8080 | `lsof -ti:8080 \| xargs kill -9` |

---

## 📁 Project Structure

```
FolderServer/
├── server.py              # Flask server (single server)
├── index.html             # Web UI
├── run.sh                 # Start script
├── install.sh             # Install dependencies
├── test_upload.sh         # Test script
├── requirements.txt       # Python dependencies
├── README.md              # Full documentation
├── SETUP_GUIDE.md         # Setup instructions
├── CHANGES.md             # Change log
├── IMPLEMENTATION_SUMMARY.md  # Complete overview
└── uploads/               # Upload directory (auto-created)
```

---

## ⚙️ Configuration

Edit `server.py`:
```python
PORT = 8080                             # Change port
MAX_FILE_SIZE = 10 * 1024**3           # 10GB max
UPLOAD_DIR = "./uploads"                # Upload location
```

---

## 🎯 Key Features

✅ Single server, one port (8080)
✅ Handles files up to 10GB
✅ Memory efficient (8KB constant)
✅ Automatic file versioning
✅ Duplicate detection
✅ Progress tracking
✅ 5 concurrent uploads

---

## 🔍 Quick Troubleshooting

**Flask not installed?**
```bash
pip3 install Flask Werkzeug
```

**Port busy?**
```bash
lsof -ti:8080 | xargs kill -9
```

**Permission denied?**
```bash
python3 -m venv venv
source venv/bin/activate
pip install Flask Werkzeug
```

---

## 📊 File Size Support

| Size | Status | Memory Used |
|------|--------|-------------|
| 1 KB - 1 MB | ✅ Fast | ~8 KB |
| 1 MB - 100 MB | ✅ Works | ~8 KB |
| 100 MB - 1 GB | ✅ Works | ~8 KB |
| 1 GB - 10 GB | ✅ Works | ~8 KB |
| 10 GB+ | ❌ Limit | N/A |

To increase limit, edit `MAX_FILE_SIZE` in `server.py`

---

## 🌐 Access URLs

| Purpose | URL |
|---------|-----|
| Upload page | `http://localhost:8080/` |
| List files | `http://localhost:8080/list` |
| Remote access | `http://YOUR_IP:8080/` |

Find YOUR_IP with:
- macOS: `ipconfig getifaddr en0`
- Linux: `hostname -I`

---

## 📖 More Info

- **Full docs**: README.md
- **Setup guide**: SETUP_GUIDE.md
- **Changes**: CHANGES.md
- **Overview**: IMPLEMENTATION_SUMMARY.md

---

## ✅ Quick Test

```bash
# 1. Start server
./run.sh

# 2. In another terminal, upload a test file
echo "test" > test.txt
curl -X POST -F "file=@test.txt" http://localhost:8080/

# 3. List uploads
curl http://localhost:8080/list

# 4. Clean up
rm test.txt
```

---

**That's it! Your server is ready to handle large file uploads efficiently! 🎉**
