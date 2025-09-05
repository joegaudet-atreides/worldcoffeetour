#!/usr/bin/env python3
"""
Import existing Jekyll posts into SQLite database
"""

import re
import json
from pathlib import Path
from coffee_db import CoffeeDatabase

def parse_front_matter(content):
    """Parse YAML front matter from Jekyll post"""
    if not content.startswith('---\n'):
        return {}, content
    
    # Find the end of front matter
    end_pos = content.find('\n---\n', 4)
    if end_pos == -1:
        return {}, content
    
    front_matter_text = content[4:end_pos]
    body = content[end_pos + 5:]
    
    # Parse YAML manually (simple key: value parsing)
    front_matter = {}
    current_list_key = None
    
    for line in front_matter_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Handle list items
        if line.startswith('- ') and current_list_key:
            if current_list_key not in front_matter:
                front_matter[current_list_key] = []
            item_value = line[2:].strip()
            # Remove quotes if present
            if (item_value.startswith('"') and item_value.endswith('"')) or (item_value.startswith("'") and item_value.endswith("'")):
                item_value = item_value[1:-1]
            front_matter[current_list_key].append(item_value)
            continue
        
        # Handle key: value pairs
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Check if this starts a list
            if value == '' or value == '[]':
                current_list_key = key
                front_matter[key] = []
                continue
            else:
                current_list_key = None
            
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Convert types
            if value.lower() == 'null' or value == '':
                front_matter[key] = None
            elif value.lower() in ['true', 'false']:
                front_matter[key] = value.lower() == 'true'
            elif key not in ['date', 'title'] and value.replace('.', '').replace('-', '').isdigit():
                if '.' in value:
                    front_matter[key] = float(value)
                else:
                    front_matter[key] = int(value)
            else:
                front_matter[key] = value
    
    return front_matter, body

def import_post_file(db, file_path):
    """Import a single post file into the database"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading {file_path.name}: {e}"
    
    try:
        front_matter, body = parse_front_matter(content)
        
        if not front_matter:
            return False, f"No front matter found in {file_path.name}"
        
        # Add original filename for reference
        front_matter['original_filename'] = file_path.name
        
        # Ensure images is a list if present
        if 'image_url' in front_matter and front_matter['image_url']:
            # Convert single image_url to images list
            if 'images' not in front_matter or not front_matter['images']:
                front_matter['images'] = [front_matter['image_url']]
            elif isinstance(front_matter['images'], list) and front_matter['image_url'] not in front_matter['images']:
                # Add image_url to images if not already there
                front_matter['images'].insert(0, front_matter['image_url'])
        
        # Set default values for required fields
        if 'published' not in front_matter:
            front_matter['published'] = True
        
        if 'continent' not in front_matter or not front_matter['continent']:
            front_matter['continent'] = 'Unknown'
            
        if 'city' not in front_matter or not front_matter['city']:
            front_matter['city'] = 'Unknown'
            
        if 'country' not in front_matter or not front_matter['country']:
            front_matter['country'] = 'Unknown'
        
        # Import into database
        post_id, action = db.upsert_post(front_matter)
        return True, action
        
    except Exception as e:
        return False, f"Error parsing {file_path.name}: {e}"

def main():
    print("📥 Importing Jekyll posts into SQLite database...")
    
    # Initialize database
    db = CoffeeDatabase()
    
    # Get all post files
    posts_dir = Path("_coffee_posts")
    if not posts_dir.exists():
        print("❌ _coffee_posts directory not found!")
        return 1
    
    post_files = list(posts_dir.glob("*.md"))
    print(f"📁 Found {len(post_files)} post files")
    
    imported_count = 0
    updated_count = 0
    error_count = 0
    
    for post_file in post_files:
        success, result = import_post_file(db, post_file)
        
        if success:
            if result == 'inserted':
                imported_count += 1
                print(f"   ✅ Imported: {post_file.name}")
            elif result == 'updated':
                updated_count += 1
                print(f"   🔄 Updated: {post_file.name}")
        else:
            error_count += 1
            print(f"   ❌ Error: {result}")
    
    # Show statistics
    stats = db.get_statistics()
    
    print(f"\n📊 Import Summary:")
    print(f"   ✅ New posts imported: {imported_count}")
    print(f"   🔄 Posts updated: {updated_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"\n📈 Database Statistics:")
    print(f"   📄 Total posts: {stats['total_posts']}")
    print(f"   ✅ Published posts: {stats['published_posts']}")
    print(f"   🖼️  Posts with images: {stats['posts_with_images']}")
    print(f"   ⭐ Posts with ratings: {stats['posts_with_ratings']}")
    
    if stats['by_continent']:
        print(f"   🌍 By continent:")
        for continent, count in stats['by_continent'].items():
            print(f"      {continent}: {count}")
    
    db.close()
    return 0

if __name__ == "__main__":
    exit(main())