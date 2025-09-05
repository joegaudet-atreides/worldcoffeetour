#!/usr/bin/env python3
"""
Simple API server for coffee post admin interface
Works directly with SQLite database
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.parse
from pathlib import Path
import subprocess
import os
from coffee_db import CoffeeDatabase
import threading
import time

class CoffeeAdminHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404)
    
    def do_PUT(self):
        if self.path.startswith('/api/'):
            self.handle_api_put()
        else:
            self.send_error(404)
    
    def handle_api_get(self):
        try:
            db = CoffeeDatabase()
            
            if self.path == '/api/posts':
                # Get all posts
                posts = db.get_all_posts()
                self.send_json_response(posts)
            
            elif self.path.startswith('/api/posts/'):
                # Get single post
                post_id = int(self.path.split('/')[-1])
                post = db.get_post_by_id(post_id)
                if post:
                    self.send_json_response(post)
                else:
                    self.send_error(404)
            
            elif self.path == '/api/stats':
                # Get statistics
                stats = db.get_statistics()
                self.send_json_response(stats)
            
            elif self.path.startswith('/api/search'):
                # Search posts
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                query = query_params.get('q', [''])[0]
                if query:
                    results = db.search_posts(query)
                    self.send_json_response(results)
                else:
                    self.send_json_response([])
            
            else:
                self.send_error(404)
            
            db.close()
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_api_post(self):
        try:
            # Handle regenerate endpoint without requiring JSON data
            if self.path == '/api/regenerate':
                # Regenerate all posts
                def regenerate_async():
                    time.sleep(0.1)  # Small delay to send response first
                    from regenerate_posts import regenerate_all_posts
                    regenerate_all_posts(backup=False)
                
                threading.Thread(target=regenerate_async).start()
                self.send_json_response({'success': True, 'message': 'Regeneration started'})
                return
            
            # For other endpoints, parse JSON data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            db = CoffeeDatabase()
            
            if self.path == '/api/posts':
                # Create new post
                post_id, action = db.upsert_post(data)
                # Regenerate the single post
                from single_post_regenerator import regenerate_single_post
                regen_success, regen_message = regenerate_single_post(post_id)
                self.send_json_response({
                    'id': post_id, 
                    'action': action,
                    'regenerated': regen_success,
                    'regen_message': regen_message
                })
            
            elif self.path.startswith('/api/posts/') and '/update' in self.path:
                # Update existing post
                post_id = int(self.path.split('/')[-2])
                success = db.update_post(post_id, data)
                if success:
                    # Regenerate the single post
                    from single_post_regenerator import regenerate_single_post
                    regen_success, regen_message = regenerate_single_post(post_id)
                    self.send_json_response({
                        'success': True, 
                        'regenerated': regen_success,
                        'regen_message': regen_message
                    })
                else:
                    self.send_error(404)
            
            elif self.path.startswith('/api/posts/') and '/delete' in self.path:
                # Delete post
                post_id = int(self.path.split('/')[-2])
                # Remove the Jekyll file first
                from single_post_regenerator import remove_post_file
                remove_success, remove_message = remove_post_file(post_id)
                # Then delete from database
                success = db.delete_post(post_id)
                if success:
                    self.send_json_response({
                        'success': True,
                        'file_removed': remove_success,
                        'remove_message': remove_message
                    })
                else:
                    self.send_error(404)
            
            
            else:
                self.send_error(404)
            
            db.close()
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_api_put(self):
        try:
            # Parse JSON data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            db = CoffeeDatabase()
            
            if self.path.startswith('/api/posts/') and not '/update' in self.path:
                # Update publish status: PUT /api/posts/{id}
                post_id = int(self.path.split('/')[-1])
                
                # For publish toggle, we only update the published field
                if 'published' in data:
                    success = db.update_post(post_id, data)
                    if success:
                        # Regenerate the single post if it's now published
                        from single_post_regenerator import regenerate_single_post
                        regen_success, regen_message = regenerate_single_post(post_id)
                        self.send_json_response({
                            'success': True,
                            'regenerated': regen_success,
                            'regen_message': regen_message
                        })
                    else:
                        self.send_error(404)
                else:
                    self.send_error(400, "Missing 'published' field")
            
            else:
                self.send_error(404)
            
            db.close()
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    port = 8081
    server = HTTPServer(('localhost', port), CoffeeAdminHandler)
    print(f"🚀 Coffee Admin API server running at http://localhost:{port}")
    print("📝 Database-driven admin interface ready!")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()