# File Upload Server

Flask-based file upload server with streaming support for files up to 10GB.

## Requirements

- Python 3.6+
- Flask 3.0+
- Werkzeug 3.0+

## Setup (First Time)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run Server

```bash
./run.sh
```

Or manually:
```bash
python3 server.py
```

Access at: `http://localhost:8080`

## Features

- Drag & drop file/folder upload (Chrome/Edge only)
- Streams files in 8KB chunks (memory efficient)
- Handles files up to 10GB
- Automatic file versioning
- Duplicate detection
- 5 concurrent uploads

## Configuration

Edit `server.py`:
```python
PORT = 8080                    # Server port
MAX_FILE_SIZE = 10 * 1024**3   # 10GB max
UPLOAD_DIR = "./uploads"        # Upload location
```

## Browser Support

- ✅ Chrome, Edge, Brave - Full support (folder upload)
- ⚠️ Firefox, Safari - Single files only (no folder upload)

## API

### Upload File
```bash
curl -X POST -F "file=@myfile.txt" http://localhost:8080/
```

### List Files
```bash
curl http://localhost:8080/list
```

## Troubleshooting

**Flask not installed:**
```bash
pip3 install Flask Werkzeug
```

**Port 8080 busy:**
```bash
lsof -ti:8080 | xargs kill -9
```

**Permission denied:**
```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

## Architecture

Single Flask server on port 8080. Streams uploads in 8KB chunks to avoid loading large files into memory. Constant ~8KB RAM usage regardless of file size.

## License

Open source - use as you wish.
