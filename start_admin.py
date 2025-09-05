#!/usr/bin/env python3
"""
Start the database-driven admin system
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def main():
    print("🚀 Starting Coffee Posts Admin System...")
    
    # Check if database exists
    db_path = Path("coffee_posts.db")
    if not db_path.exists():
        print("📥 No database found. Importing posts...")
        subprocess.run([sys.executable, "import_posts_to_db.py"])
    
    print("🔧 Starting API server...")
    
    try:
        # Start the API server
        process = subprocess.Popen([sys.executable, "admin_api.py"])
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Open admin interface
        admin_url = f"file://{Path('admin.html').absolute()}"
        print(f"🌐 Opening admin interface: {admin_url}")
        webbrowser.open(admin_url)
        
        print("💡 Admin system running!")
        print("   • API server: http://localhost:8081")
        print("   • Admin interface opened in browser")
        print("   • Press Ctrl+C to stop")
        
        # Wait for user to stop
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping admin system...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()