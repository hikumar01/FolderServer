import os
import signal
import sys
import json
import uuid
from flask import Flask, request, jsonify, send_from_directory

UPLOAD_DIR = "./uploads"
TMP_DIR = "./tmp"  # Separate directory for temporary upload files
PORT = 8080
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB max file size
CHUNK_SIZE = 8192  # 8KB chunks for streaming

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

# Clean up any leftover temp files from previous crashes
def cleanup_temp_files():
    """Remove temporary files left over from interrupted uploads"""
    try:
        # Clean entire tmp directory - safe because it only contains our temp files
        for filename in os.listdir(TMP_DIR):
            temp_file = os.path.join(TMP_DIR, filename)
            if os.path.isfile(temp_file):
                os.remove(temp_file)
                print(f"[CLEANUP] Removed stale temp file: {filename}")
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {e}")

cleanup_temp_files()

# Flask app - single server for all file uploads
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Enable XSS protection in browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Ensure proper content type for JSON responses
    if response.content_type and 'application/json' in response.content_type:
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

def sanitize_for_output(text):
    """
    Sanitize text for safe output in JSON responses.
    Prevents XSS by escaping HTML entities and removing control characters.
    """
    if not isinstance(text, str):
        return text

    # First, escape HTML entities to prevent XSS
    # This escapes: < > & " ' to their HTML entity equivalents
    sanitized = (text
        .replace('&', '&amp;')   # Must be first!
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;'))

    # Remove control characters except newline, tab, carriage return
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')

    # Limit length to prevent DoS
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]

    return sanitized

def validate_path(relative_path):
    """
    Validate and sanitize relative path for security.
    Returns (is_valid, sanitized_path, error_message)
    """
    # Security: prevent empty paths
    if not relative_path or not relative_path.strip():
        print(f"[SECURITY] Empty path rejected")
        return False, None, 'Empty path not allowed'

    # Security: prevent null byte injection
    if '\x00' in relative_path:
        print(f"[SECURITY] Null byte injection blocked: {repr(relative_path)}")
        return False, None, 'Null bytes not allowed in path'

    # Security: prevent path traversal
    if relative_path.startswith("/") or ".." in relative_path:
        print(f"[SECURITY] Path traversal attempt blocked: {relative_path}")
        return False, None, 'Unsafe path'

    filepath = os.path.abspath(os.path.join(UPLOAD_DIR, relative_path))
    uploads_abs = os.path.abspath(UPLOAD_DIR)

    # Security: ensure filepath is strictly inside uploads directory
    if not filepath.startswith(uploads_abs + os.sep):
        return False, None, 'Outside upload dir'

    return True, filepath, None

def files_are_identical(file1_path, file2_path):
    """Compare two files chunk by chunk to check if they're identical"""
    try:
        # Quick size check first - avoid expensive byte comparison if sizes differ
        size1 = os.path.getsize(file1_path)
        size2 = os.path.getsize(file2_path)
        if size1 != size2:
            return False

        # Byte-by-byte comparison
        with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
            while True:
                chunk1 = f1.read(CHUNK_SIZE)
                chunk2 = f2.read(CHUNK_SIZE)
                if chunk1 != chunk2:
                    return False
                if not chunk1:  # End of file
                    return True
    except Exception as e:
        print(f"[ERROR] File comparison failed: {e}")
        return False

def get_versioned_filepath(filepath):
    """Generate a versioned filename if the file already exists"""
    if not os.path.exists(filepath):
        return filepath, 0

    base, ext = os.path.splitext(filepath)
    counter = 1
    versioned_filepath = f"{base} ({counter}){ext}" if ext else f"{base} ({counter})"

    while os.path.exists(versioned_filepath):
        counter += 1
        versioned_filepath = f"{base} ({counter}){ext}" if ext else f"{base} ({counter})"

    return versioned_filepath, counter

def handle_file_upload(file, relative_path, strategy='rename'):
    """
    Common file upload handler with streaming support for large files.
    Handles versioning and duplicate detection.

    Args:
        file: The file object to upload
        relative_path: The relative path where to save the file
        strategy: How to handle conflicts - 'merge', 'replace', 'rename', 'skip'
    """
    # Validate path
    is_valid, filepath, error = validate_path(relative_path)
    if not is_valid:
        print(f"[SECURITY] {error}: {relative_path}")
        return {'error': error, 'status': 'error'}, 400

    uploads_abs = os.path.abspath(UPLOAD_DIR)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Save new file to temp directory first for comparison
    # Use UUID to prevent race conditions with concurrent uploads
    # Store in separate tmp directory to avoid conflicts with user uploads
    temp_filename = f"{uuid.uuid4().hex}.tmp"
    temp_path = os.path.join(TMP_DIR, temp_filename)

    # Stream file to disk in chunks (memory efficient)
    try:
        with open(temp_path, 'wb') as f:
            while True:
                chunk = file.stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        # Clean up temp file on failure
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass  # Best effort cleanup
        print(f"[ERROR] Upload streaming failed for {relative_path}: {e}")
        raise

    # Check if file exists and handle based on strategy
    if not os.path.exists(filepath):
        # New file - no conflict
        os.rename(temp_path, filepath)
        print(f"[UPLOAD] {relative_path} (new file)")
        return {'status': 'success', 'path': sanitize_for_output(os.path.basename(filepath)), 'action': 'new'}, 200

    # File exists - check if identical first (fast path for duplicates)
    if files_are_identical(temp_path, filepath):
        os.remove(temp_path)
        print(f"[SKIP] {relative_path} (duplicate)")
        return {'status': 'skipped', 'path': sanitize_for_output(relative_path), 'reason': 'identical'}, 200

    # Handle based on strategy
    if strategy == 'skip':
        os.remove(temp_path)
        print(f"[SKIP] {relative_path} (user choice)")
        return {'status': 'skipped', 'path': sanitize_for_output(relative_path), 'reason': 'user_skip'}, 200

    elif strategy in ('replace', 'merge'):
        # For files, merge means replace (merge only applies to directories conceptually)
        os.remove(filepath)
        os.rename(temp_path, filepath)
        action = 'replaced' if strategy == 'replace' else 'merged'
        print(f"[{strategy.upper()}] {relative_path}")
        return {'status': 'success', 'path': sanitize_for_output(os.path.basename(filepath)), 'action': action}, 200

    else:  # strategy == 'rename' (default)
        # Create versioned filename
        versioned_filepath, version = get_versioned_filepath(filepath)

        # Security: ensure versioned file will be created inside uploads directory
        versioned_abs = os.path.abspath(versioned_filepath)
        if not versioned_abs.startswith(uploads_abs + os.sep):
            os.remove(temp_path)  # Clean up temp file
            print(f"[SECURITY] Versioned path outside upload dir blocked: {versioned_filepath}")
            return {'error': 'Versioned file would be outside upload dir', 'status': 'error'}, 400

        os.rename(temp_path, versioned_filepath)
        print(f"[UPLOAD] {relative_path} → version ({version})")
        return {'status': 'success', 'path': sanitize_for_output(os.path.basename(versioned_filepath)), 'action': 'renamed'}, 200

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
        strategy = request.form.get('strategy', 'rename')

        # Sanitize strategy input (whitelist approach)
        if strategy not in ['rename', 'replace', 'merge', 'skip']:
            strategy = 'rename'

        try:
            result, status_code = handle_file_upload(file, relative_path, strategy)
            return jsonify(result), status_code
        except Exception as e:
            # Log detailed error server-side only
            print(f"[ERROR] Upload failed for {relative_path}: {type(e).__name__}: {e}")
            # Return generic error to client (no sensitive information)
            return jsonify({'error': 'Upload failed', 'status': 'error'}), 500

@app.route('/check-file-conflicts', methods=['POST'])
def check_file_conflicts():
    """
    Check for file-level conflicts within directories being merged.
    Returns list of files that exist with their sizes for comparison.
    """
    try:
        data = request.get_json()
        if not data or 'paths' not in data:
            return jsonify({'error': 'No paths provided'}), 400

        paths_to_check = data['paths']  # List of relative file paths
        conflicts = []
        uploads_abs = os.path.abspath(UPLOAD_DIR)

        for relative_path in paths_to_check:
            # Validate path
            is_valid, filepath, error = validate_path(relative_path)
            if not is_valid:
                continue

            # Check if file exists
            if os.path.exists(filepath) and os.path.isfile(filepath):
                conflicts.append({
                    'path': sanitize_for_output(relative_path),
                    'existingSize': os.path.getsize(filepath)
                })

        return jsonify({'conflicts': conflicts}), 200
    except Exception as e:
        print(f"[ERROR] File conflict check failed: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to check file conflicts'}), 500

@app.route('/list', methods=['GET'])
def list_files():
    """List uploaded files with caching headers for performance"""
    uploads_abs = os.path.abspath(UPLOAD_DIR)
    result = []

    try:
        for entry in os.listdir(uploads_abs):
            full_path = os.path.join(uploads_abs, entry)
            # Sanitize entry names to prevent XSS
            sanitized_entry = sanitize_for_output(entry)

            if os.path.isdir(full_path):
                result.append({
                    "path": sanitized_entry + "/",
                    "size": 0
                })
            elif os.path.isfile(full_path):
                result.append({
                    "path": sanitized_entry,
                    "size": os.path.getsize(full_path)
                })

        response = jsonify(result)
        # Disable caching to ensure immediate updates after uploads
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
    except Exception as e:
        # Log detailed error server-side only
        print(f"[ERROR] List files failed: {type(e).__name__}: {e}")
        # Return generic error to client
        return jsonify({'error': 'Failed to retrieve file list'}), 500

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
