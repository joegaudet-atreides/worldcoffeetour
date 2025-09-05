#!/usr/bin/env python3
"""
Quick fix for common YAML issues in Jekyll posts
"""

import os
import re
from pathlib import Path

def fix_yaml_issues(file_path):
    """Fix common YAML issues in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Fix unquoted values that start with special characters
    content = re.sub(r'^(\s*\w+:\s*)([%@#&*!|>].*?)$', r'\1"\2"', content, flags=re.MULTILINE)
    
    # Fix unquoted values with colons inside
    content = re.sub(r'^(\s*\w+:\s*)([^"\'\n]*:[^"\'\n]*)$', r'\1"\2"', content, flags=re.MULTILINE)
    
    # Fix values that contain hash symbols
    content = re.sub(r'^(\s*\w+:\s*)([^"\'\n]*#[^"\'\n]*)$', r'\1"\2"', content, flags=re.MULTILINE)
    
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Fixed"
        except Exception as e:
            return False, f"Error writing: {e}"
    
    return True, "OK"

def main():
    print("🔧 Quick YAML fix for Jekyll posts...")
    
    posts_dir = Path("_coffee_posts")
    fixed_count = 0
    
    for post_file in posts_dir.glob("*.md"):
        success, message = fix_yaml_issues(post_file)
        if success and message == "Fixed":
            print(f"✅ Fixed: {post_file.name}")
            fixed_count += 1
        elif not success:
            print(f"❌ Error in {post_file.name}: {message}")
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()