import http.server
import socketserver
import threading
import os
import signal
import sys
import hashlib
import json
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.serving import make_server

UPLOAD_DIR = "./uploads"
PORT = 8080
FLASK_PORT = 8081  # Fallback server for large files
MAX_HTTP_SERVER_SIZE = 2 * 1024 * 1024  # 2MB limit for http.server
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB max file size

os.makedirs(UPLOAD_DIR, exist_ok=True)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

# Flask app for large file uploads
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
flask_server = None

@app.route('/large-upload', methods=['POST'])
def large_upload():
    """Handle large file uploads via Flask"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get the relative path from form data
    relative_path = request.form.get('path', file.filename)
    
    # Security: prevent path traversal
    if relative_path.startswith("/") or ".." in relative_path:
        return jsonify({'error': 'Unsafe path'}), 400
    
    filepath = os.path.abspath(os.path.join(UPLOAD_DIR, relative_path))
    if not filepath.startswith(os.path.abspath(UPLOAD_DIR)):
        return jsonify({'error': 'Outside upload dir'}), 400
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Check if file exists and handle versioning
    if os.path.exists(filepath):
        # Check if content is the same
        temp_path = filepath + ".tmp"
        file.save(temp_path)
        
        with open(temp_path, 'rb') as new_file:
            new_data = new_file.read()
        
        with open(filepath, 'rb') as existing_file:
            existing_data = existing_file.read()
        
        if existing_data == new_data:
            os.remove(temp_path)
            print(f"[SKIP] Same content: {filepath}")
            return jsonify({'status': 'skipped', 'path': relative_path}), 200
        
        os.remove(temp_path)
        
        # Create versioned filename
        base, ext = os.path.splitext(filepath)
        counter = 1
        versioned_filepath = filepath
        while os.path.exists(versioned_filepath):
            versioned_filepath = f"{base} ({counter}){ext}" if ext else f"{base} ({counter})"
            counter += 1
        
        file.seek(0)  # Reset file pointer
        file.save(versioned_filepath)
        print(f"[UPLOAD] New version created: {versioned_filepath}")
        return jsonify({'status': 'success', 'path': os.path.basename(versioned_filepath)}), 200
    else:
        file.save(filepath)
        print(f"[UPLOAD] New file: {filepath}")
        return jsonify({'status': 'success', 'path': os.path.basename(filepath)}), 200

@app.route('/list', methods=['GET'])
def flask_list_files():
    """List uploaded files - Flask version"""
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

@app.route('/')
def flask_index():
    """Serve the main page from Flask"""
    return send_from_directory('.', 'index.html')

class UploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/list':
            self.list_uploads()
            return
        return super().do_GET()

    def list_uploads(self):
        uploads_abs = os.path.abspath(UPLOAD_DIR)
        result = []

        try:
            for entry in os.listdir(uploads_abs):
                full_path = os.path.join(uploads_abs, entry)
                if os.path.isdir(full_path):
                    result.append({
                        "path": entry + "/",  # Mark directory with '/'
                        "size": 0
                    })
                elif os.path.isfile(full_path):
                    result.append({
                        "path": entry,
                        "size": os.path.getsize(full_path)
                    })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())

        except Exception as e:
            self.send_error(500, f"Error: {e}")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type', '')

        if content_length <= 0 or "boundary=" not in content_type:
            self.send_error(400, "Invalid POST request")
            return

        # Check if file is too large for http.server
        if content_length > MAX_HTTP_SERVER_SIZE:
            # Redirect to Flask server
            self.send_response(307)  # Temporary Redirect
            self.send_header('Location', f'http://{self.headers.get("Host").split(":")[0]}:{FLASK_PORT}/large-upload')
            self.send_header('X-Large-File-Redirect', 'true')
            self.end_headers()
            # Still need to consume the body to prevent connection issues
            # But we'll do it in chunks to avoid memory issues
            bytes_consumed = 0
            chunk_size = 8192
            while bytes_consumed < content_length:
                to_read = min(chunk_size, content_length - bytes_consumed)
                self.rfile.read(to_read)
                bytes_consumed += to_read
            return

        boundary = content_type.split("boundary=")[1].strip().encode()
        data = self.rfile.read(content_length)
        parts = data.split(b"--" + boundary)

        uploaded_files = []

        for part in parts:
            if b'filename="' not in part or b'\r\n\r\n' not in part:
                continue

            try:
                headers, file_data = part.split(b'\r\n\r\n', 1)
                header_str = headers.decode(errors='ignore')
                filename = header_str.split('filename="')[1].split('"')[0]
                filename = filename.replace("\\", "/")

                if filename.startswith("/") or ".." in filename:
                    raise ValueError("Unsafe path")

                filepath = os.path.abspath(os.path.join(UPLOAD_DIR, filename))
                if not filepath.startswith(os.path.abspath(UPLOAD_DIR)):
                    raise ValueError("Outside upload dir")

                os.makedirs(os.path.dirname(filepath), exist_ok=True)

                if file_data.endswith(b"\r\n"):
                    file_data = file_data[:-2]
                elif file_data.endswith(b"--"):
                    file_data = file_data[:-2]

                file_written = False

                if os.path.exists(filepath):
                    with open(filepath, 'rb') as existing:
                        existing_data = existing.read()
                    if existing_data == file_data:
                        # Skip if the content is the same - is matching only with base version
                        # This is a simple check; for more robust versioning, consider using hashes
                        # Can be improved to check for all versions
                        print(f"[SKIP] Same content: {filepath}")
                        uploaded_files.append("[SKIPPED] " + filepath)
                        continue
                    else:
                        base, ext = os.path.splitext(filepath)
                        counter = 1
                        versioned_filepath = filepath
                        while os.path.exists(versioned_filepath):
                            versioned_filepath = f"{base} ({counter}){ext}" if ext else f"{base} ({counter})"
                            counter += 1
                        with open(versioned_filepath, 'wb') as f:
                            f.write(file_data)
                        print(f"[UPLOAD] New version created: {versioned_filepath}")
                        uploaded_files.append(os.path.basename(versioned_filepath))
                        file_written = True
                else:
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    print(f"[UPLOAD] New file: {filepath}")
                    uploaded_files.append(os.path.basename(filepath))
                    file_written = True

            except Exception as e:
                print(f"[ERROR] {e}")
                self.send_error(500, f"Upload failed: {e}")
                return

        if uploaded_files:
            self.send_response(200)
            self.end_headers()
            self.wfile.write("\n".join(uploaded_files).encode())
        else:
            self.send_error(400, "No valid file found")

    def log_message(self, format, *args):
        # print(f"[REQUEST] {self.client_address[0]} - {format % args}")
        pass

# Setup and run the servers
os.chdir(os.path.dirname(os.path.abspath(__file__)))
httpd = ThreadedHTTPServer(("", PORT), UploadHandler)
flask_server = make_server('', FLASK_PORT, app, threaded=True)

def shutdown_server(signum=None, frame=None):
    print("\n🔴 Shutting down servers...")
    httpd.shutdown()
    httpd.server_close()
    flask_server.shutdown()
    print("✅ Servers stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_server)
signal.signal(signal.SIGTERM, shutdown_server)

# Start http.server thread
http_thread = threading.Thread(target=httpd.serve_forever)
http_thread.daemon = True
http_thread.start()

# Start Flask server thread
flask_thread = threading.Thread(target=flask_server.serve_forever)
flask_thread.daemon = True
flask_thread.start()

server_ip = sys.argv[1] if len(sys.argv) > 1 else "localhost"
print(f"✅ Main Server (http.server) running at http://{server_ip}:{PORT}")
print(f"✅ Large File Server (Flask) running at http://{server_ip}:{FLASK_PORT}")
print(f"📂 Upload directory: {os.path.abspath(UPLOAD_DIR)}")
print(f"📏 Files < 2MB: http.server | Files >= 2MB: Flask (up to 10GB)")
print("🔁 Press Ctrl+C to stop...")

try:
    http_thread.join()
    flask_thread.join()
except KeyboardInterrupt:
    shutdown_server()
