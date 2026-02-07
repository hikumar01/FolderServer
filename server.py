import os
import signal
import sys
import json
from flask import Flask, request, jsonify, send_from_directory

UPLOAD_DIR = "./uploads"
PORT = 8080
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB max file size
CHUNK_SIZE = 8192  # 8KB chunks for streaming

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Flask app - single server for all file uploads
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def handle_file_upload(file, relative_path):
    """
    Common file upload handler with streaming support for large files.
    Handles versioning and duplicate detection.
    """
    # Security: prevent path traversal
    if relative_path.startswith("/") or ".." in relative_path:
        return {'error': 'Unsafe path', 'status': 'error'}, 400
    
    filepath = os.path.abspath(os.path.join(UPLOAD_DIR, relative_path))
    if not filepath.startswith(os.path.abspath(UPLOAD_DIR)):
        return {'error': 'Outside upload dir', 'status': 'error'}, 400
  
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Save new file to temp location first for comparison
    temp_path = filepath + ".tmp"

    # Stream file to disk in chunks (memory efficient)
    with open(temp_path, 'wb') as f:
        while True:
            chunk = file.stream.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)

    # Check if file exists and handle versioning
    if os.path.exists(filepath):
        # Compare files using chunks to avoid loading large files into memory
        files_identical = False
        try:
            with open(temp_path, 'rb') as new_file, open(filepath, 'rb') as existing_file:
                files_identical = True
                while True:
                    new_chunk = new_file.read(CHUNK_SIZE)
                    existing_chunk = existing_file.read(CHUNK_SIZE)
                    if new_chunk != existing_chunk:
                        files_identical = False
                        break
                    if not new_chunk:  # End of file
                        break
        except Exception as e:
            print(f"[ERROR] Comparison failed: {e}")
            files_identical = False

        if files_identical:
            os.remove(temp_path)
            print(f"[SKIP] Same content: {filepath}")
            return {'status': 'skipped', 'path': relative_path}, 200

        # Create versioned filename
        base, ext = os.path.splitext(filepath)
        counter = 1
        versioned_filepath = filepath
        while os.path.exists(versioned_filepath):
            versioned_filepath = f"{base} ({counter}){ext}" if ext else f"{base} ({counter})"
            counter += 1

        os.rename(temp_path, versioned_filepath)
        print(f"[UPLOAD] New version created: {versioned_filepath}")
        return {'status': 'success', 'path': os.path.basename(versioned_filepath)}, 200
    else:
        os.rename(temp_path, filepath)
        print(f"[UPLOAD] New file: {filepath}")
        return {'status': 'success', 'path': os.path.basename(filepath)}, 200

@app.route('/', methods=['GET', 'POST'])
def handle_request():
    """Unified handler for all requests"""
    if request.method == 'GET':
        # Serve the main page
        return send_from_directory('.', 'index.html')

    elif request.method == 'POST':
        # Handle file upload (both small and large files)
        if 'file' not in request.files:
            return jsonify({'error': 'No file part', 'status': 'error'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file', 'status': 'error'}), 400

        # Get the relative path from form data (multipart) or use filename
        relative_path = request.form.get('path', file.filename)

        try:
            result, status_code = handle_file_upload(file, relative_path)
            return jsonify(result), status_code
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/list', methods=['GET'])
def list_files():
    """List uploaded files"""
    uploads_abs = os.path.abspath(UPLOAD_DIR)
    result = []

    try:
        for entry in os.listdir(uploads_abs):
            full_path = os.path.join(uploads_abs, entry)
            if os.path.isdir(full_path):
                result.append({
                    "path": entry + "/",
                    "size": 0
                })
            elif os.path.isfile(full_path):
                result.append({
                    "path": entry,
                    "size": os.path.getsize(full_path)
                })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

# Setup and run the server
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def shutdown_server(signum=None, frame=None):
    print("\n✅ Server stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_server)
signal.signal(signal.SIGTERM, shutdown_server)

if __name__ == '__main__':
    server_ip = sys.argv[1] if len(sys.argv) > 1 else "localhost"

    print()
    print(f"✅ Server running at http://{server_ip}:{PORT}")
    print(f"📂 Upload directory: {os.path.abspath(UPLOAD_DIR)}")
    print(f"📏 Maximum file size: {MAX_FILE_SIZE / (1024**3):.0f}GB")
    print(f"🔧 Chunk size: {CHUNK_SIZE} bytes")
    print("🔁 Press Ctrl+C to stop...")
    print()

    # Start Flask development server
    app.run(host='0.0.0.0', port=PORT, threaded=True, debug=False)
