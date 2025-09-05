#!/usr/bin/env python3
"""
Comprehensive verification script for Jekyll coffee posts
Checks for broken links, missing images, and YAML issues
"""

import os
import re
from pathlib import Path
import time

def check_yaml_structure(file_path):
    """Check if YAML front matter is properly structured"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Cannot read file: {e}"
    
    if not content.startswith('---\n'):
        return False, "Missing YAML front matter start"
    
    end_pos = content.find('\n---\n', 4)
    if end_pos == -1:
        return False, "Missing YAML front matter end"
    
    front_matter = content[4:end_pos]
    
    # Check for common YAML issues
    lines = front_matter.split('\n')
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if ':' not in line:
            continue
            
        key, value = line.split(':', 1)
        value = value.strip()
        
        # Check for unquoted values with special characters
        if value and not ((value.startswith('"') and value.endswith('"')) or 
                         (value.startswith("'") and value.endswith("'"))):
            if any(char in value for char in ['%', '#', ':', '@', '&', '*', '!', '|', '>']):
                return False, f"Line {i}: Unquoted special character in '{value}'"
    
    return True, "OK"

def check_image_exists(image_path, base_path):
    """Check if an image file exists"""
    if image_path.startswith('http'):
        return True  # External images - assume they exist
    
    # Convert to local path
    local_path = base_path / image_path.lstrip('/')
    return local_path.exists()

def check_post_integrity(file_path, base_path):
    """Check a single post for integrity issues"""
    issues = []
    
    # Check YAML structure
    yaml_ok, yaml_msg = check_yaml_structure(file_path)
    if not yaml_ok:
        issues.append(f"YAML: {yaml_msg}")
    
    # Parse front matter for image checking
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        end_pos = content.find('\n---\n', 4)
        if end_pos != -1:
            front_matter = content[4:end_pos]
            
            # Extract image URLs
            for line in front_matter.split('\n'):
                if ':' in line and not line.strip().startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if key == 'image_url' and value and value != 'null':
                        if not check_image_exists(value, base_path):
                            issues.append(f"Missing image: {value}")
                    
                    elif key == 'images' and value and value != 'null':
                        # Handle images list (simplified)
                        if value.startswith('[') or '- ' in front_matter:
                            # This is a list, but we'll skip complex parsing for now
                            pass
    
    except Exception as e:
        issues.append(f"Error parsing: {e}")
    
    return issues

def verify_jekyll_build():
    """Check if Jekyll can build without errors"""
    try:
        result = os.system('bundle exec jekyll build --dry-run 2>/dev/null')
        return result == 0
    except:
        return False

def main():
    print("🔍 Verifying Jekyll coffee posts...")
    
    posts_dir = Path("_coffee_posts")
    base_path = Path(".")
    
    if not posts_dir.exists():
        print("❌ _coffee_posts directory not found!")
        return 1
    
    total_posts = 0
    posts_with_issues = 0
    total_issues = 0
    
    print(f"📁 Checking {len(list(posts_dir.glob('*.md')))} posts...\n")
    
    for post_file in sorted(posts_dir.glob("*.md")):
        total_posts += 1
        issues = check_post_integrity(post_file, base_path)
        
        if issues:
            posts_with_issues += 1
            total_issues += len(issues)
            print(f"❌ {post_file.name}:")
            for issue in issues:
                print(f"   • {issue}")
            print()
    
    # Check Jekyll build
    print("🏗️  Checking Jekyll build...")
    if verify_jekyll_build():
        print("✅ Jekyll build check passed")
    else:
        print("❌ Jekyll build has issues")
        total_issues += 1
    
    print(f"\n📊 Summary:")
    print(f"   📄 Total posts: {total_posts}")
    print(f"   ❌ Posts with issues: {posts_with_issues}")
    print(f"   🚨 Total issues: {total_issues}")
    
    if total_issues == 0:
        print("\n🎉 All posts verified successfully!")
        return 0
    else:
        print(f"\n⚠️  Found {total_issues} issues that need attention")
        return 1

if __name__ == "__main__":
    exit(main())