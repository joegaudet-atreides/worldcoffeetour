#!/usr/bin/env python3
"""
Regenerate all Jekyll posts from SQLite database
Destroys and recreates all post files
"""

import json
import re
from pathlib import Path
from datetime import datetime
from coffee_db import CoffeeDatabase

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

def regenerate_all_posts(backup=True):
    """Regenerate all posts from SQLite database"""
    print("🔄 Regenerating all Jekyll posts from SQLite database...")
    
    # Initialize database
    db = CoffeeDatabase()
    
    # Get posts directory
    posts_dir = Path("_coffee_posts")
    
    if posts_dir.exists():
        if backup:
            # Create backup
            backup_dir = Path(f"_coffee_posts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            print(f"📦 Creating backup: {backup_dir}")
            posts_dir.rename(backup_dir)
            posts_dir.mkdir()
        else:
            # Clean up all existing posts
            print("🗑️  Removing all existing posts...")
            for file in posts_dir.glob("*.md"):
                file.unlink()
    else:
        posts_dir.mkdir()
    
    # Get all posts from database
    posts = db.get_all_posts()
    print(f"📄 Found {len(posts)} posts in database")
    
    created_count = 0
    error_count = 0
    filenames = set()  # Track filenames to avoid duplicates
    
    for post in posts:
        try:
            # Generate filename
            base_filename = generate_filename(post)
            filename = base_filename
            counter = 1
            
            # Ensure unique filename
            while filename in filenames:
                name_part, ext = base_filename.rsplit('.', 1)
                filename = f"{name_part}-{counter}.{ext}"
                counter += 1
            
            filenames.add(filename)
            
            # Create post content
            content = create_post_content(post)
            
            # Write file
            file_path = posts_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_count += 1
            print(f"   ✅ Created: {filename}")
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error creating post {post.get('id', 'unknown')}: {e}")
    
    db.close()
    
    print(f"\n📊 Regeneration Summary:")
    print(f"   ✅ Posts created: {created_count}")
    print(f"   ❌ Errors: {error_count}")
    
    if error_count == 0:
        print("\n🎉 All posts regenerated successfully!")
        return 0
    else:
        print(f"\n⚠️  {error_count} posts had errors")
        return 1

def clean_orphaned_posts():
    """Remove post files that don't exist in the database"""
    print("🧹 Cleaning orphaned post files...")
    
    db = CoffeeDatabase()
    posts_dir = Path("_coffee_posts")
    
    if not posts_dir.exists():
        print("❌ _coffee_posts directory not found!")
        return
    
    # Get all hashes from database
    db_posts = db.get_all_posts()
    db_filenames = {post.get('original_filename') for post in db_posts if post.get('original_filename')}
    
    # Check all files in directory
    removed_count = 0
    
    for file_path in posts_dir.glob("*.md"):
        if file_path.name not in db_filenames:
            print(f"   🗑️  Removing orphaned file: {file_path.name}")
            file_path.unlink()
            removed_count += 1
    
    print(f"   ✅ Removed {removed_count} orphaned files")
    db.close()

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--no-backup':
        backup = False
    else:
        backup = True
    
    if len(sys.argv) > 1 and sys.argv[1] == '--clean-only':
        clean_orphaned_posts()
        return 0
    
    return regenerate_all_posts(backup=backup)

if __name__ == "__main__":
    exit(main())