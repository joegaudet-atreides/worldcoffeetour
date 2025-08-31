#!/usr/bin/env python3
"""
Apply corrections to existing coffee posts without re-processing Instagram data
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

def yaml_safe_string(text):
    """Make a string safe for YAML by properly escaping it"""
    if not text:
        return '""'
    
    # Clean up the text first
    text = str(text)
    
    # Fix UTF-8 encoding issues first - handle byte sequences
    byte_replacements = {
        '\u0080\u0099': "'",  # I€™ve -> I've
        '\u0080\u009c': '"',  # Left double quote
        '\u0080\u009d': '"',  # Right double quote
        '\u0080\u0094': '-',  # Em dash
        '\u0080\u0093': '-',  # En dash
        'â\u0080\u0099': "'", # Another variant
        'â\u0080\u009c': '"',
        'â\u0080\u009d': '"',
        'â\u0080\u0094': '-',
        'â\u0080\u0093': '-',
    }
    
    for wrong, right in byte_replacements.items():
        text = text.replace(wrong, right)
    
    # Handle common character encoding problems from Instagram export
    char_replacements = {
        'â': "'",          # â often means '
        'â': '"',          # â often means "
        'â': '"',          # â often means "
        'â': '-',          # â often means -
        'â': '-',          # â often means -
        'Â': '',           # Â is often a stray character
        'Ã¡': 'a',         # á encoded incorrectly
        'Ã©': 'e',         # é encoded incorrectly
        'Ã­': 'i',         # í encoded incorrectly
        'Ã³': 'o',         # ó encoded incorrectly
        'Ãº': 'u',         # ú encoded incorrectly
        'Ã±': 'ñ',         # ñ encoded incorrectly
    }
    
    for wrong, right in char_replacements.items():
        text = text.replace(wrong, right)
    
    # Handle quotes and special characters for YAML
    if '"' in text or "'" in text or ':' in text or '\n' in text or text.startswith(' ') or text.endswith(' '):
        # Escape internal quotes and wrap in quotes
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'
    
    return text

def load_corrections():
    """Load manual corrections from JSON file"""
    corrections_file = Path("post-corrections.json")
    if corrections_file.exists():
        with open(corrections_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Remove metadata fields starting with _
        return {k: v for k, v in data.items() if not k.startswith('_')}
    return {}

def get_post_files():
    """Get all existing post files"""
    posts_dir = Path("_coffee_posts")
    if not posts_dir.exists():
        print("❌ No _coffee_posts directory found!")
        return []
    
    return list(posts_dir.glob("*.md"))

def parse_front_matter(content):
    """Parse YAML front matter from markdown content"""
    if not content.startswith('---\n'):
        return {}, content
    
    # Find the end of front matter
    end_pos = content.find('\n---\n', 4)
    if end_pos == -1:
        return {}, content
    
    front_matter_text = content[4:end_pos]
    body = content[end_pos + 5:]  # Skip the closing ---\n
    
    # Parse YAML manually (simple key: value parsing)
    front_matter = {}
    for line in front_matter_text.split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # Convert numeric values
            if value.replace('.', '').replace('-', '').isdigit():
                if '.' in value:
                    front_matter[key] = float(value)
                else:
                    front_matter[key] = int(value)
            elif value.lower() in ['true', 'false']:
                front_matter[key] = value.lower() == 'true'
            else:
                front_matter[key] = value
    
    return front_matter, body

def generate_front_matter(data):
    """Generate YAML front matter from data dict"""
    lines = ['---']
    
    # Standard fields in order
    field_order = [
        'layout', 'title', 'date', 'city', 'country', 'continent',
        'latitude', 'longitude', 'cafe_name', 'rating', 'notes',
        'image_url', 'images', 'instagram_url'
    ]
    
    # Add ordered fields
    for field in field_order:
        if field in data and data[field] is not None:
            value = data[field]
            if isinstance(value, str):
                lines.append(f'{field}: {yaml_safe_string(value)}')
            elif isinstance(value, (int, float)):
                lines.append(f'{field}: {value}')
            elif isinstance(value, list):
                if value:  # Only add if list is not empty
                    lines.append(f'{field}:')
                    for item in value:
                        lines.append(f'  - {yaml_safe_string(str(item))}')
    
    lines.append('---')
    return '\n'.join(lines) + '\n'

def apply_corrections_to_posts():
    """Apply corrections to existing posts"""
    corrections = load_corrections()
    if not corrections:
        print("📝 No corrections found in post-corrections.json")
        return
    
    print(f"📝 Found {len(corrections)} corrections to apply")
    
    post_files = get_post_files()
    if not post_files:
        print("❌ No post files found in _coffee_posts/")
        return
    
    print(f"📁 Found {len(post_files)} post files")
    
    applied_count = 0
    
    for post_file in post_files:
        # Read the file
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse front matter
        front_matter, body = parse_front_matter(content)
        
        # Generate post key from URL-like structure
        # Convert filename to URL format for matching
        filename_stem = post_file.stem
        post_key = f"coffee/{filename_stem}"
        
        # Check if this post has corrections
        if post_key in corrections:
            print(f"   ✅ Applying corrections to: {post_file.name}")
            
            # Apply corrections to front matter
            correction = corrections[post_key]
            for key, value in correction.items():
                front_matter[key] = value
            
            # Regenerate the file with corrections
            new_front_matter = generate_front_matter(front_matter)
            new_content = new_front_matter + body
            
            # Write the corrected file
            with open(post_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            applied_count += 1
        else:
            # Try alternative matching strategies
            
            # Method 1: Try matching by timestamp in filename
            timestamp_match = re.search(r'-(\d{10})\.md$', str(post_file))
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                for correction_key in corrections.keys():
                    if timestamp in correction_key:
                        print(f"   ✅ Applying corrections to: {post_file.name} (timestamp match)")
                        correction = corrections[correction_key]
                        for key, value in correction.items():
                            front_matter[key] = value
                        
                        new_front_matter = generate_front_matter(front_matter)
                        new_content = new_front_matter + body
                        
                        with open(post_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        applied_count += 1
                        break
    
    print(f"\n✅ Applied corrections to {applied_count} posts")
    print(f"📊 {len(corrections) - applied_count} corrections could not be matched to posts")
    
    if applied_count < len(corrections):
        print(f"\n💡 Unmatched corrections:")
        matched_keys = set()
        for post_file in post_files:
            filename_stem = post_file.stem
            post_key = f"coffee/{filename_stem}"
            if post_key in corrections:
                matched_keys.add(post_key)
        
        unmatched = set(corrections.keys()) - matched_keys
        for key in sorted(unmatched):
            print(f"   - {key}")

def main():
    print("""
☕ Apply Coffee Post Corrections
===============================
This script applies corrections from post-corrections.json to existing posts
""")
    
    # Check if corrections file exists
    if not Path("post-corrections.json").exists():
        print("❌ post-corrections.json not found!")
        print("💡 Create corrections using the admin interface at /admin.html")
        return
    
    # Check if posts directory exists
    if not Path("_coffee_posts").exists():
        print("❌ _coffee_posts directory not found!")
        print("💡 Run the main processing script first to create posts")
        return
    
    apply_corrections_to_posts()
    
    print(f"""
🎉 Corrections Applied Successfully!

Next steps:
1. Check the updated posts in _coffee_posts/
2. Run 'bundle exec jekyll serve' to see changes
3. Commit changes if satisfied: git add . && git commit -m "Apply manual corrections"
""")

if __name__ == "__main__":
    main()