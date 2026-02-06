# Folder Upload Server

A Python Flask-based file upload server with efficient streaming support for files of any size.

## Features

- ✅ Drag & drop folder/file upload
- ✅ Single server handles all file sizes (up to 10GB)
- ✅ Memory-efficient streaming (8KB chunks)
- ✅ Automatic file versioning (prevents overwriting)
- ✅ Progress tracking with file sizes
- ✅ Concurrent uploads (5 simultaneous)
- ✅ Path traversal protection
- ✅ Duplicate file detection

## Installation

### Install Dependencies

```bash
pip3 install -r requirements.txt
```

If you encounter permission errors:

```bash
# Option 1: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Option 2: Install to user directory
pip3 install --user Flask Werkzeug

# Option 3: System install (requires password)
sudo pip3 install Flask Werkzeug

# Option 4: Use automated installer
./install.sh
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
3. Watch the upload progress
4. Files are stored in the `./uploads` directory

## Architecture

### Single Flask Server

The application uses **one Flask server** on port 8080:

- **Memory Efficient**: Streams files in 8KB chunks (doesn't load entire file into RAM)
- **Handles All Sizes**: From tiny files to 10GB files
- **Production Grade**: Flask is reliable and battle-tested
- **Threading**: Supports 5 concurrent uploads

### How It Works

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       └──── All files ────► Flask Server (Port 8080)
                              • Streams in chunks
                              • Memory efficient
                              • Up to 10GB per file
```

### Streaming Upload Process

1. **Client** sends file via multipart/form-data
2. **Server** streams file to disk in 8KB chunks
3. **Comparison** done chunk-by-chunk (for duplicates)
4. **Versioning** creates `file (1).ext` if different content exists

## Configuration

Edit `server.py` to change settings:

```python
UPLOAD_DIR = "./uploads"                        # Upload directory
PORT = 8080                                      # Server port
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024         # 10GB max
CHUNK_SIZE = 8192                                # 8KB chunks
```

## File Versioning

When uploading a file that already exists:
- **Identical content**: Upload is skipped (saves time and space)
- **Different content**: New version is created (e.g., `file (1).txt`, `file (2).txt`)

The comparison is done efficiently using chunk-by-chunk reading, so even comparing 10GB files won't use excessive memory.

## Security Features

- ✅ Path traversal protection (prevents `../` attacks)
- ✅ Upload directory isolation (files can't escape uploads folder)
- ✅ File size limits (configurable max size)
- ✅ Automatic directory creation with safety checks
- ✅ Streaming prevents memory exhaustion attacks

## Browser Compatibility

This uploader uses Chrome-specific APIs (`webkitGetAsEntry`) for folder uploads.

**Supported browsers:**
- ✅ Google Chrome
- ✅ Microsoft Edge
- ✅ Brave
- ❌ Firefox (folder upload not supported)
- ❌ Safari (folder upload not supported)

## Performance

| File Size | Memory Usage | Upload Method |
|-----------|--------------|---------------|
| 1 MB      | ~8 KB        | Streaming     |
| 100 MB    | ~8 KB        | Streaming     |
| 1 GB      | ~8 KB        | Streaming     |
| 10 GB     | ~8 KB        | Streaming     |

The server maintains constant low memory usage regardless of file size.

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

# Or automated installer
./install.sh
```

### "Address already in use"

Port 8080 is busy. Kill the process or change the port:
```bash
# Kill existing process
lsof -ti:8080 | xargs kill -9

# Or change PORT in server.py
```

### Large files failing

1. Check available disk space
2. Verify `MAX_FILE_SIZE` in `server.py`
3. Check server logs for specific errors
4. Ensure browser isn't timing out (Chrome handles large uploads well)

### Upload is slow

- **Network speed** is usually the bottleneck, not the server
- 1 GB file on 100 Mbps connection takes ~80 seconds
- Progress bar shows real-time speed

## API Documentation

### Upload File

**Endpoint:** `POST /`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file`: The file to upload (required)
- `path`: Relative path within uploads directory (optional, defaults to filename)

**Response:** JSON

```json
{
  "status": "success",
  "path": "uploaded_filename.txt"
}
```

Or:

```json
{
  "status": "skipped",
  "path": "duplicate_file.txt"
}
```

### List Files

**Endpoint:** `GET /list`

**Response:** JSON array

```json
[
  {
    "path": "file.txt",
    "size": 1024
  },
  {
    "path": "folder/",
    "size": 0
  }
]
```

## Development

### Run in Debug Mode

Edit `server.py`:

```python
app.run(host='0.0.0.0', port=PORT, threaded=True, debug=True)
```

### Add Logging

Uncomment or add logging statements:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

Open source - use as you wish.

## Why Flask Instead of http.server?

Python's built-in `http.server` has documented issues:
- ❌ Files > 2MB cause connection resets
- ❌ Incomplete reads for large files
- ❌ Loads entire file into memory
- ❌ Not recommended for production

Flask advantages:
- ✅ Production-ready
- ✅ Reliable for any file size
- ✅ Streaming support
- ✅ Better error handling
- ✅ Active development and community
