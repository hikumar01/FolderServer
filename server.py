import http.server
import socketserver
import threading
import os
import signal
import sys
import hashlib
import json

UPLOAD_DIR = "./uploads"
PORT = 8080

os.makedirs(UPLOAD_DIR, exist_ok=True)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

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

# Setup and run the server
os.chdir(os.path.dirname(os.path.abspath(__file__)))
httpd = ThreadedHTTPServer(("", PORT), UploadHandler)

def shutdown_server(signum=None, frame=None):
    print("\n🔴 Shutting down server...")
    httpd.shutdown()
    httpd.server_close()
    print("✅ Server stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_server)
signal.signal(signal.SIGTERM, shutdown_server)

thread = threading.Thread(target=httpd.serve_forever)
thread.daemon = True
thread.start()

server_ip = sys.argv[1] if len(sys.argv) > 1 else "localhost"
print(f"✅ Server running at http://{server_ip}:{PORT}")
print(f"📂 Upload directory: {os.path.abspath(UPLOAD_DIR)}")
print("🔁 Press Ctrl+C to stop...")

try:
    thread.join()
except KeyboardInterrupt:
    shutdown_server()
