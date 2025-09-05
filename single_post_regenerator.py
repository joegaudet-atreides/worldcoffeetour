#!/usr/bin/env python3
"""
Single post regeneration for per-save updates
"""

import json
import re
from pathlib import Path
from coffee_db import CoffeeDatabase

def is_problematic(post):
    """Check if post is problematic (missing required data)"""
    return not post.get('cafe_name') or \
           not post.get('city') or post.get('city') == 'Unknown' or \
           not post.get('country') or post.get('country') == 'Unknown' or \
           not post.get('latitude') or not post.get('longitude') or \
           not post.get('continent')

def yaml_safe_string(text):
    """Make a string safe for YAML by properly escaping it"""
    if not text:
        return '""'
    
    text = str(text).strip()
    
    # Replace smart quotes with regular ASCII quotes to avoid YAML issues
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # Smart single quotes
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # Smart double quotes
    text = text.replace('\u2013', '-').replace('\u2014', '--')  # En/em dashes
    text = text.replace('\u2026', '...')  # Ellipsis
    
    # Characters that require quoting in YAML
    needs_quoting = any([
        text.startswith(('%', '@', '`', '|', '>', '#', '-', '?', ':', '[', '{', ']', '}', ',', '&', '*', '!', '\'', '"')),
        text.endswith(':'),
        ':' in text,
        '\n' in text,
        '"' in text,
        "'" in text,
        text in ['true', 'false', 'null', 'yes', 'no', 'on', 'off'],
        text.replace('.', '').replace('-', '').isdigit(),
        text.startswith(' ') or text.endswith(' '),
        # Check for any remaining non-ASCII characters that could cause issues
        any(ord(c) > 127 for c in text),
        # Check for any control characters
        any(ord(c) < 32 and c not in '\n\t' for c in text),
    ])
    
    if needs_quoting:
        # Escape internal quotes and wrap in double quotes
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    
    return text

def generate_filename(post):
    """Generate a filename for a post based on date and title"""
    date_str = post['date'] if post['date'] else '1970-01-01'
    
    # Create slug from title
    title = post.get('title', 'untitled')
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)[:50]  # Max 50 chars
    
    return f"{date_str}-{slug}.md"

def create_post_content(post):
    """Create Jekyll post content from database record"""
    lines = ['---']
    
    # Standard field order
    field_order = [
        'layout', 'title', 'date', 'city', 'country', 'continent',
        'latitude', 'longitude', 'cafe_name', 'rating', 'notes',
        'images', 'instagram_url', 'published'
    ]
    
    # Set layout if not present
    if 'layout' not in post or not post['layout']:
        lines.append('layout: post')
    
    # Add ordered fields
    for field in field_order:
        if field in post and post[field] is not None:
            value = post[field]
            
            if field == 'images' and isinstance(value, list):
                if value:  # Only add if list is not empty
                    lines.append(f'{field}:')
                    for item in value:
                        lines.append(f'  - {yaml_safe_string(str(item))}')
            elif isinstance(value, str):
                lines.append(f'{field}: {yaml_safe_string(value)}')
            elif isinstance(value, bool):
                lines.append(f'{field}: {str(value).lower()}')
            elif isinstance(value, (int, float)):
                lines.append(f'{field}: {value}')
    
    lines.append('---')
    lines.append('')  # Empty line after front matter
    
    return '\n'.join(lines)

def regenerate_single_post(post_id):
    """Regenerate a single post by ID"""
    try:
        db = CoffeeDatabase()
        post = db.get_post_by_id(post_id)
        
        if not post:
            return False, f"Post {post_id} not found"
        
        posts_dir = Path("_coffee_posts")
        posts_dir.mkdir(exist_ok=True)
        
        # Remove any existing file for this post (by original filename or new filename)
        if post.get('original_filename'):
            old_file = posts_dir / post['original_filename']
            if old_file.exists():
                old_file.unlink()
        
        # Only generate Jekyll file for published, non-problematic posts
        if not post.get('published'):
            db.close()
            return True, f"Post {post_id} unpublished - no Jekyll file generated"
        
        if is_problematic(post):
            db.close()
            return True, f"Post {post_id} is problematic - no Jekyll file generated"
        
        # Generate new filename and content
        filename = generate_filename(post)
        content = create_post_content(post)
        
        # Write file
        file_path = posts_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        db.close()
        return True, f"Generated {filename}"
        
    except Exception as e:
        return False, str(e)

def remove_post_file(post_id):
    """Remove the Jekyll file for a deleted post"""
    try:
        db = CoffeeDatabase()
        post = db.get_post_by_id(post_id)
        
        if post and post.get('original_filename'):
            posts_dir = Path("_coffee_posts")
            file_path = posts_dir / post['original_filename']
            if file_path.exists():
                file_path.unlink()
                db.close()
                return True, f"Removed {post['original_filename']}"
        
        db.close()
        return False, "Post file not found"
        
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        post_id = int(sys.argv[1])
        success, message = regenerate_single_post(post_id)
        if success:
            print(f"✅ Regenerated: {message}")
        else:
            print(f"❌ Error: {message}")
    else:
        print("Usage: python3 single_post_regenerator.py <post_id>")