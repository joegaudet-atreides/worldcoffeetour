#!/usr/bin/env python3
"""
Simple API server for post corrections using SQLite
"""

import json
import sys
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from post_corrections_db import PostCorrectionsDB

class CorrectionsHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = PostCorrectionsDB()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests - retrieve corrections"""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/corrections':
            try:
                # Get all corrections
                corrections = self.db.get_corrections()
                self.send_json_response(corrections)
            except Exception as e:
                self.send_error_response(str(e))
        
        elif parsed_url.path.startswith('/corrections/'):
            try:
                # Get specific post corrections
                post_id = parsed_url.path[13:]  # Remove '/corrections/'
                corrections = self.db.get_corrections(post_id)
                if corrections:
                    self.send_json_response(corrections)
                else:
                    self.send_json_response({})
            except Exception as e:
                self.send_error_response(str(e))
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests - save corrections"""
        if self.path == '/corrections':
            try:
                # Read the request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                corrections_data = json.loads(post_data)
                
                # Save to database
                self.db.save_corrections(corrections_data)
                
                # Auto-apply corrections to Jekyll posts
                try:
                    result = subprocess.run([
                        'python3', 'apply_corrections_sqlite.py', '--silent'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        self.send_json_response({
                            "success": True, 
                            "message": "Corrections saved and applied to Jekyll posts"
                        })
                    else:
                        self.send_json_response({
                            "success": True, 
                            "message": "Corrections saved but failed to apply to posts",
                            "apply_error": result.stderr
                        })
                except subprocess.TimeoutExpired:
                    self.send_json_response({
                        "success": True,
                        "message": "Corrections saved but apply timed out"
                    })
                except Exception as apply_error:
                    self.send_json_response({
                        "success": True,
                        "message": f"Corrections saved but apply failed: {apply_error}"
                    })
            except Exception as e:
                self.send_error_response(str(e))
        
        elif self.path == '/corrections/import':
            try:
                # Import from JSON (for migration)
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                json_data = json.loads(post_data)
                
                self.db.import_from_json(json_data)
                
                self.send_json_response({"success": True, "message": "JSON imported"})
            except Exception as e:
                self.send_error_response(str(e))
        
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        """Handle DELETE requests - delete corrections"""
        if self.path.startswith('/corrections/'):
            try:
                post_id = self.path[13:]  # Remove '/corrections/'
                self.db.delete_correction(post_id)
                
                # Auto-apply corrections to Jekyll posts
                try:
                    result = subprocess.run([
                        'python3', 'apply_corrections_sqlite.py', '--silent'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        self.send_json_response({
                            "success": True, 
                            "message": "Correction deleted and changes applied to Jekyll posts"
                        })
                    else:
                        self.send_json_response({
                            "success": True, 
                            "message": "Correction deleted but failed to apply changes to posts",
                            "apply_error": result.stderr
                        })
                except subprocess.TimeoutExpired:
                    self.send_json_response({
                        "success": True,
                        "message": "Correction deleted but apply timed out"
                    })
                except Exception as apply_error:
                    self.send_json_response({
                        "success": True,
                        "message": f"Correction deleted but apply failed: {apply_error}"
                    })
            except Exception as e:
                self.send_error_response(str(e))
        else:
            self.send_error(404)
    
    def send_json_response(self, data):
        """Send a JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_error_response(self, error_message):
        """Send an error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_data = {"error": error_message}
        json_data = json.dumps(error_data)
        self.wfile.write(json_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass

def run_server(port=8001):
    """Run the corrections API server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CorrectionsHandler)
    print(f"🗄️  Corrections API server running on http://localhost:{port}")
    print("   Available endpoints:")
    print("   GET  /corrections - Get all corrections")
    print("   POST /corrections - Save corrections")
    print("   GET  /corrections/{post_id} - Get specific post corrections")
    print("   DELETE /corrections/{post_id} - Delete post corrections")
    print("\n   Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()

if __name__ == "__main__":
    port = 8001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default 8001")
    
    run_server(port)