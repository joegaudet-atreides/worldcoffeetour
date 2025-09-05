#!/usr/bin/env python3
"""
Ensure Jekyll posts are 100% synchronized with SQLite database.
This script can be run repeatedly to maintain sync.
"""

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime
from coffee_db import CoffeeDatabase

def clean_posts_directory():
    """Remove all existing Jekyll posts"""
    posts_dir = Path('_coffee_posts')
    
    if posts_dir.exists():
        print(f"🧹 Cleaning existing posts directory: {posts_dir}")
        
        # Create backup
        backup_dir = Path(f'_coffee_posts_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        if posts_dir.exists():
            shutil.copytree(posts_dir, backup_dir)
            print(f"📦 Backup created: {backup_dir}")
        
        # Remove all .md files
        for md_file in posts_dir.glob('*.md'):
            md_file.unlink()
            
        print(f"✅ Cleaned {len(list(posts_dir.glob('*.md')))} existing posts")
    else:
        posts_dir.mkdir(exist_ok=True)
        print(f"📁 Created posts directory: {posts_dir}")

def yaml_safe_string(value):
    """Make a string safe for YAML"""
    if not value:
        return '""'
    
    # Convert to string and handle special characters
    value = str(value)
    
    # Check if we need quotes
    needs_quotes = (
        ':' in value or 
        '"' in value or 
        "'" in value or 
        value.startswith(('#', '@', '!', '&', '*', '[', '{', '|', '>', '%')) or
        value.strip() != value or
        value.lower() in ('yes', 'no', 'true', 'false', 'null')
    )
    
    if needs_quotes:
        # Escape quotes and wrap in double quotes
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    
    return value

def create_post_content(post):
    """Create Jekyll post content from database post"""
    # Parse images if they're JSON
    images = post.get('images', [])
    if isinstance(images, str):
        import json
        try:
            images = json.loads(images)
        except:
            images = []
    
    # Prepare front matter
    front_matter = {
        'layout': 'coffee_post',
        'title': yaml_safe_string(post.get('title', 'Untitled')),
        'date': post.get('date', datetime.now().strftime('%Y-%m-%d')),
        'city': yaml_safe_string(post.get('city', 'Unknown')),
        'country': yaml_safe_string(post.get('country', 'Unknown')),
        'continent': yaml_safe_string(post.get('continent', 'Unknown')),
        'published': 'true' if post.get('published', True) else 'false'
    }
    
    # Add optional fields
    if post.get('cafe_name'):
        front_matter['cafe_name'] = yaml_safe_string(post['cafe_name'])
    
    if post.get('latitude'):
        front_matter['latitude'] = post['latitude']
    
    if post.get('longitude'):
        front_matter['longitude'] = post['longitude']
    
    if post.get('rating'):
        front_matter['rating'] = post['rating']
    
    if images:
        # Use first image as primary
        front_matter['image_url'] = yaml_safe_string(images[0])
        # Store all images in images array
        front_matter['images'] = images
    
    if post.get('instagram_url'):
        front_matter['instagram_url'] = yaml_safe_string(post['instagram_url'])
    
    # Build content
    content_lines = ['---']
    
    # Add front matter
    for key, value in front_matter.items():
        if key == 'images' and isinstance(value, list):
            content_lines.append(f'{key}:')
            for img in value:
                content_lines.append(f'  - {yaml_safe_string(img)}')
        else:
            content_lines.append(f'{key}: {value}')
    
    content_lines.append('---')
    content_lines.append('')
    
    # Add post content (notes)
    if post.get('notes'):
        content_lines.append(str(post['notes']))
    else:
        content_lines.append(f"Coffee post from {post.get('city', 'Unknown')}, {post.get('country', 'Unknown')}")
    
    return '\\n'.join(content_lines)

def generate_filename(post):
    """Generate Jekyll filename from post data"""
    date = post.get('date', datetime.now().strftime('%Y-%m-%d'))
    title = post.get('title', 'untitled')
    
    # Create slug from title
    slug = title.lower()
    slug = ''.join(c for c in slug if c.isalnum() or c in ' -_')
    slug = '-'.join(slug.split())
    slug = slug[:50]  # Limit length
    
    # Ensure unique filename by adding post ID
    post_id = post.get('id', 'unknown')
    
    return f"{date}-{slug}-{post_id}.md"

def sync_posts_to_jekyll():
    """Synchronize all database posts to Jekyll"""
    print("🔄 Synchronizing database posts to Jekyll...")
    
    db = CoffeeDatabase()
    posts = db.get_all_posts()
    
    print(f"📊 Found {len(posts)} posts in database")
    
    posts_dir = Path('_coffee_posts')
    posts_dir.mkdir(exist_ok=True)
    
    created_count = 0
    error_count = 0
    
    for post in posts:
        try:
            filename = generate_filename(post)
            filepath = posts_dir / filename
            
            content = create_post_content(post)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_count += 1
            
            if created_count % 10 == 0:
                print(f"   Created {created_count}/{len(posts)} posts...", end='\\r')
                
        except Exception as e:
            print(f"\\n❌ Error creating post {post.get('id', 'unknown')}: {e}")
            error_count += 1
    
    print(f"\\n✅ Synchronization complete!")
    print(f"   📝 Created: {created_count} Jekyll posts")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} posts")
    
    db.close()
    return created_count, error_count

def verify_sync():
    """Verify that Jekyll posts match database"""
    print("\\n🔍 Verifying synchronization...")
    
    db = CoffeeDatabase()
    db_posts = db.get_all_posts()
    
    posts_dir = Path('_coffee_posts')
    jekyll_files = list(posts_dir.glob('*.md')) if posts_dir.exists() else []
    
    db_count = len(db_posts)
    jekyll_count = len(jekyll_files)
    
    print(f"📊 Database posts: {db_count}")
    print(f"📊 Jekyll files: {jekyll_count}")
    
    if db_count == jekyll_count:
        print("✅ Counts match!")
    else:
        print(f"⚠️  Count mismatch! Difference: {abs(db_count - jekyll_count)}")
    
    # Check for published vs unpublished
    published_posts = [p for p in db_posts if p.get('published', True)]
    unpublished_posts = [p for p in db_posts if not p.get('published', True)]
    
    print(f"📊 Published posts: {len(published_posts)}")
    print(f"📊 Unpublished posts: {len(unpublished_posts)}")
    
    db.close()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Database Synchronization Script

Usage:
    python3 ensure_db_sync.py [--clean] [--verify-only] [--stats-only]

Options:
    --clean       Clean all existing Jekyll posts before sync
    --verify-only Only verify sync, don't regenerate
    --stats-only  Only show database statistics
    --help        Show this help message

This script ensures that Jekyll posts are 100% synchronized with the SQLite database.
It can be run repeatedly and is idempotent (safe to run multiple times).

The script will:
1. Clean existing Jekyll posts (if --clean specified)
2. Generate Jekyll posts for all database entries
3. Handle multiple images per post
4. Preserve published/unpublished status
5. Create proper YAML front matter
6. Verify synchronization
        """)
        return
    
    # Show statistics
    if '--stats-only' in sys.argv:
        db = CoffeeDatabase()
        stats = db.get_statistics()
        print("📊 Database Statistics:")
        print(f"   Total posts: {stats.get('total_posts', 0)}")
        print(f"   Published: {stats.get('published_posts', 0)}")
        print(f"   With images: {stats.get('posts_with_images', 0)}")
        print(f"   With location: {stats.get('posts_with_location', 0)}")
        print(f"   With cafe names: {stats.get('posts_with_cafe_names', 0)}")
        db.close()
        return
    
    # Verify only
    if '--verify-only' in sys.argv:
        verify_sync()
        return
    
    # Clean if requested
    if '--clean' in sys.argv:
        clean_posts_directory()
    
    # Sync posts
    created, errors = sync_posts_to_jekyll()
    
    # Verify
    verify_sync()
    
    if errors == 0:
        print("\\n🎉 All posts successfully synchronized!")
        print("\\n💡 Jekyll posts are now 100% generated from SQLite database")
        print("   You can run this script anytime to ensure sync")
    else:
        print(f"\\n⚠️  Sync completed with {errors} errors")
        sys.exit(1)

if __name__ == "__main__":
    main()