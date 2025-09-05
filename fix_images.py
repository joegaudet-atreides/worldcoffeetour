#!/usr/bin/env python3
"""
Fix image paths in coffee posts
"""

import os
import re
from pathlib import Path

def fix_image_paths():
    posts_dir = Path("_coffee_posts")
    
    if not posts_dir.exists():
        print("❌ No _coffee_posts directory found!")
        return
    
    fixed_count = 0
    total_count = 0
    
    for post_file in posts_dir.glob("*.md"):
        total_count += 1
        
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix image paths from media/posts/... to /assets/images/posts/...
        updated_content = re.sub(
            r'image_url: "media/posts/([^"]+)"',
            r'image_url: "/assets/images/posts/\1"',
            content
        )
        
        # Also fix any relative paths that don't start with media/posts
        updated_content = re.sub(
            r'image_url: "(?!/)([^"]*\.jpg)"',
            r'image_url: "/assets/images/posts/\1"',
            updated_content
        )
        
        if updated_content != content:
            with open(post_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            fixed_count += 1
            print(f"  ✅ Fixed: {post_file.name}")
    
    print(f"\n💾 Fixed image paths in {fixed_count}/{total_count} posts!")

if __name__ == "__main__":
    print("🔧 Fixing image paths in coffee posts...")
    fix_image_paths()