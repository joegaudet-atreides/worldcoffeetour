#!/usr/bin/env python3
"""
Apply corrections from SQLite database to existing coffee posts automatically
"""

import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime
from post_corrections_db import PostCorrectionsDB

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

def load_corrections_from_db():
    """Load corrections from SQLite database"""
    db = PostCorrectionsDB()
    corrections = db.get_corrections()
    print(f"📝 Loaded {len(corrections)} corrections from SQLite database")
    return corrections

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
        'image_url', 'images', 'instagram_url', 'published'
    ]
    
    # Add ordered fields
    for field in field_order:
        if field in data and data[field] is not None:
            value = data[field]
            if isinstance(value, str):
                lines.append(f'{field}: {yaml_safe_string(value)}')
            elif isinstance(value, bool):
                lines.append(f'{field}: {str(value).lower()}')
            elif isinstance(value, (int, float)):
                lines.append(f'{field}: {value}')
            elif isinstance(value, list):
                if value:  # Only add if list is not empty
                    lines.append(f'{field}:')
                    for item in value:
                        lines.append(f'  - {yaml_safe_string(str(item))}')
    
    lines.append('---')
    return '\n'.join(lines) + '\n'

def validate_yaml_content(filepath):
    """Validate that a file can be parsed as Jekyll post"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for basic YAML structure
        if not content.startswith('---\n'):
            return False, "Missing YAML front matter"
            
        # Find end of front matter
        end_pos = content.find('\n---\n', 4)
        if end_pos == -1:
            return False, "Incomplete YAML front matter"
            
        # Check for control characters in title and content
        lines = content[:end_pos + 5].split('\n')
        for line in lines:
            if any(ord(c) < 32 and c not in '\n\t' for c in line):
                return False, f"Control characters in YAML: {repr(line[:50])}"
                
        return True, "Valid"
        
    except Exception as e:
        return False, f"Error reading file: {e}"

def apply_corrections_to_posts(silent=False):
    """Apply corrections to existing posts"""
    corrections = load_corrections_from_db()
    if not corrections:
        if not silent:
            print("📝 No corrections found in SQLite database")
        return 0
    
    if not silent:
        print(f"📝 Found {len(corrections)} corrections to apply")
    
    post_files = get_post_files()
    if not post_files:
        if not silent:
            print("❌ No post files found in _coffee_posts/")
        return 0
    
    if not silent:
        print(f"📁 Found {len(post_files)} post files")
    
    applied_count = 0
    
    for post_file in post_files:
        # Read the file
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            if not silent:
                print(f"❌ Error reading {post_file.name}: {e}")
            continue
        
        # Parse front matter
        front_matter, body = parse_front_matter(content)
        
        # Generate post key from URL-like structure
        # Convert filename to URL format for matching
        filename_stem = post_file.stem
        post_key = f"coffee/{filename_stem}"
        
        # Check if this post has corrections
        if post_key in corrections:
            if not silent:
                print(f"   ✅ Applying corrections to: {post_file.name}")
            
            # Apply corrections to front matter
            correction = corrections[post_key]
            for key, value in correction.items():
                if value is not None:  # Only apply non-null values
                    # Convert SQLite boolean integers back to proper booleans for Jekyll
                    if key == 'published':
                        front_matter[key] = bool(value)
                    else:
                        front_matter[key] = value
            
            # Regenerate the file with corrections
            new_front_matter = generate_front_matter(front_matter)
            new_content = new_front_matter + body
            
            # Write the corrected file
            try:
                with open(post_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                # Validate the written file
                is_valid, error_msg = validate_yaml_content(post_file)
                if not is_valid and not silent:
                    print(f"   ⚠️  Warning: Created invalid file {post_file.name}: {error_msg}")
                
                applied_count += 1
            except Exception as e:
                if not silent:
                    print(f"❌ Error writing {post_file.name}: {e}")
        else:
            # Try alternative matching strategies
            
            # Method 1: Try matching by timestamp in filename
            timestamp_match = re.search(r'-(\d{10})\.md$', str(post_file))
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                for correction_key in corrections.keys():
                    if timestamp in correction_key:
                        if not silent:
                            print(f"   ✅ Applying corrections to: {post_file.name} (timestamp match)")
                        correction = corrections[correction_key]
                        for key, value in correction.items():
                            if value is not None:  # Only apply non-null values
                                # Convert SQLite boolean integers back to proper booleans for Jekyll
                                if key == 'published':
                                    front_matter[key] = bool(value)
                                else:
                                    front_matter[key] = value
                        
                        new_front_matter = generate_front_matter(front_matter)
                        new_content = new_front_matter + body
                        
                        try:
                            with open(post_file, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            applied_count += 1
                        except Exception as e:
                            if not silent:
                                print(f"❌ Error writing {post_file.name}: {e}")
                        break
    
    if not silent:
        print(f"\n✅ Applied corrections to {applied_count} posts")
        if applied_count < len(corrections):
            print(f"📊 {len(corrections) - applied_count} corrections could not be matched to posts")
    
    return applied_count

def main():
    # Check for silent mode
    silent = '--silent' in sys.argv
    
    if not silent:
        print("""
☕ Apply Coffee Post Corrections (SQLite)
=========================================
This script applies corrections from the SQLite database to existing posts
""")
    
    # Check if posts directory exists
    if not Path("_coffee_posts").exists():
        if not silent:
            print("❌ _coffee_posts directory not found!")
            print("💡 Run the main processing script first to create posts")
        return 1
    
    try:
        applied_count = apply_corrections_to_posts(silent=silent)
        
        if not silent:
            print(f"""
🎉 Corrections Applied Successfully!

Applied {applied_count} corrections from SQLite database.
Changes are now live in Jekyll!
""")
        
        return 0
    except Exception as e:
        if not silent:
            print(f"❌ Error applying corrections: {e}")
        return 1

if __name__ == "__main__":
    exit(main())