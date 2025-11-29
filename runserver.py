import http.server
import socketserver
import os
from pathlib import Path

PORT = 5500

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).resolve().parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def translate_path(self, path):
        # Serve files from the script's directory
        path = super().translate_path(path)
        relpath = os.path.relpath(path, os.getcwd())
        return os.path.join(SCRIPT_DIR, relpath)

    def log_message(self, format, *args):
        # Custom logging
        print(f"[HTTP] {self.address_string()} - {format % args}")

def run_server():
    # Change to the script directory
    os.chdir(SCRIPT_DIR)
    
    handler = MyHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print("=" * 60)
            print(f"✅ HTTP Server RUNNING on port {PORT}")
            print(f"📁 Serving files from: {SCRIPT_DIR}")
            print(f"🌐 Access at: http://localhost:{PORT}")
            print("=" * 60)
            print("\n📂 Available files:")
            
            # List HTML files in current directory
            for item in os.listdir(SCRIPT_DIR):
                if item.endswith('.html'):
                    print(f"   • http://localhost:{PORT}/{item}")
            
            # List subdirectories with HTML files
            for root, dirs, files in os.walk(SCRIPT_DIR):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    html_files = list(dir_path.glob('*.html'))
                    if html_files:
                        rel_path = dir_path.relative_to(SCRIPT_DIR)
                        for html_file in html_files:
                            print(f"   • http://localhost:{PORT}/{rel_path}/{html_file.name}")
            
            print("\n⏸️  Press Ctrl+C to stop the server\n")
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ ERROR: Port {PORT} is already in use!")
            print(f"Kill the process using port {PORT} or use a different port.")
            print(f"\nOn Windows: netstat -ano | findstr :{PORT}")
            print(f"On Mac/Linux: lsof -i :{PORT}")
        else:
            print(f"❌ ERROR: {e}")
    except KeyboardInterrupt:
        print(f"\n\n✋ Server stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    run_server()