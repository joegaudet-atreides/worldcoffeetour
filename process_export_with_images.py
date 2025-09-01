#!/usr/bin/env python3
"""
Enhanced Instagram export processor - copies images and is idempotent
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

def yaml_safe_string(text):
    """Make a string safe for YAML by properly escaping it"""
    if not text:
        return '""'
    
    # Clean up the text first
    text = str(text)
    
    # Fix UTF-8 encoding issues first - handle byte sequences
    byte_replacements = {
        '\u0080\u0099': "'",  # Iâ\x80\x99ve -> I've
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
        'Ã±': 'n',         # ñ encoded incorrectly
    }
    
    for wrong, right in char_replacements.items():
        text = text.replace(wrong, right)
    
    # Replace standard Unicode characters
    text = text.replace('"', '"').replace('"', '"')  # Smart quotes
    text = text.replace(''', "'").replace(''', "'")  # Smart apostrophes
    text = text.replace('—', '-').replace('–', '-')  # Em/en dashes
    text = text.replace('\n', ' ').replace('\r', ' ')  # Remove line breaks
    text = text.replace('\t', ' ')  # Replace tabs with spaces
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    
    # Remove any remaining non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Escape quotes and wrap in quotes for YAML safety
    text = text.replace('"', '\\"')
    return f'"{text}"'

def copy_image_safely(source_path, dest_path):
    """Copy an image file if it doesn't already exist or if it's different"""
    try:
        if not source_path.exists():
            print(f"    ⚠️ Source image doesn't exist: {source_path}")
            return False
            
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if destination already exists and is the same size
        if dest_path.exists():
            if dest_path.stat().st_size == source_path.stat().st_size:
                print(f"    ⏭️ Image already exists: {dest_path.name}")
                return True
            else:
                print(f"    🔄 Updating changed image: {dest_path.name}")
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        print(f"    📸 Copied image: {dest_path.name}")
        return True
        
    except Exception as e:
        print(f"    ❌ Failed to copy image {source_path}: {e}")
        return False

def process_instagram_export_with_images():
    """Process your Instagram export with photos - copy images version"""
    
    export_folder = Path('instagram-export-folder')
    if not export_folder.exists():
        print("❌ Error: instagram-export-folder not found!")
        print("Please place your Instagram export in a folder named 'instagram-export-folder'")
        return 0
    
    posts_json = export_folder / 'your_instagram_activity/media/posts_1.json'
    if not posts_json.exists():
        print(f"❌ Error: {posts_json} not found!")
        return 0
    
    # Load posts
    with open(posts_json, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    # Find coffee posts (tolerant of spelling variations)
    coffee_posts = []
    coffee_hashtags = [
        '#worldcoffeetour',
        '#worldcofeetour',  # common typo
        '#world_coffee_tour',
        '#worldcoffee',
        '#cofeetour',
        'worldcoffeetour',  # without hash
        'world coffee tour'  # without hash, with spaces
    ]
    
    for post in posts:
        title = post.get('title', '').lower()
        if any(hashtag in title for hashtag in coffee_hashtags):
            coffee_posts.append(post)
    
    print(f"☕ Found {len(coffee_posts)} coffee tour posts!")
    
    # Create Jekyll posts directory
    posts_dir = Path("_coffee_posts")
    posts_dir.mkdir(exist_ok=True)
    
    # Create media directory
    media_dir = Path("media")
    media_dir.mkdir(exist_ok=True)
    
    # Get existing posts to avoid duplicates (idempotent behavior)
    existing_posts = set()
    for existing_post in posts_dir.glob("*.md"):
        existing_posts.add(existing_post.stem)
    
    # Track processed posts to avoid creating duplicates in this run
    processed_posts = set()
    
    created = 0
    updated = 0
    skipped = 0
    images_copied = 0
    
    for i, post in enumerate(coffee_posts, 1):
        try:
            # Get timestamp
            timestamp = post.get('creation_timestamp', 0)
            date = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            date_str = date.strftime("%Y-%m-%d")
            
            # Get caption/title
            caption = post.get('title', '')
            
            # Extract first meaningful line as title
            lines = [line.strip() for line in caption.split('\n') if line.strip()]
            post_title = ""
            for line in lines:
                # Skip lines that are just hashtags or too short
                if not line.startswith('#') and not line.startswith('@') and len(line) > 10:
                    # Clean up special characters
                    line = line.replace('"', '"').replace('"', '"')
                    line = line.replace(''', "'").replace(''', "'")
                    line = line.replace('—', '-').replace('–', '-')
                    post_title = line[:80]
                    break
            
            if not post_title:
                post_title = f"Coffee Stop {i}"
            
            # Clean notes (full caption without hashtags)
            notes = re.sub(r'#\w+\s*', '', caption).strip()
            notes = notes.replace('"', '"').replace('"', '"')
            notes = notes.replace(''', "'").replace(''', "'")
            notes = notes.replace('—', '-').replace('–', '-')
            notes = re.sub(r'\n\n+', '\n', notes).strip()
            
            # Process images - copy them to our media folder
            image_paths = []
            image_path = ""  # Primary image for backwards compatibility
            
            if post.get('media') and len(post['media']) > 0:
                # Create date-specific media directory
                date_folder = f"{date.strftime('%Y%m')}"
                media_posts_dir = media_dir / "posts" / date_folder
                media_posts_dir.mkdir(parents=True, exist_ok=True)
                
                for media_item in post['media']:
                    media_uri = media_item.get('uri', '')
                    if media_uri:
                        # Get source file path
                        source_file = export_folder / media_uri
                        
                        # Get just the filename
                        filename = Path(media_uri).name
                        
                        # Destination path
                        dest_file = media_posts_dir / filename
                        
                        # Copy the image
                        if copy_image_safely(source_file, dest_file):
                            # Add the web-relative path
                            web_path = f"/media/posts/{date_folder}/{filename}"
                            image_paths.append(web_path)
                            images_copied += 1
                
                # Set primary image to first one for backwards compatibility
                if image_paths:
                    image_path = image_paths[0]
            
            # Location mapping
            latitude = None
            longitude = None
            city = "Unknown"
            country = "Unknown"  
            continent = "World"
            cafe_name = ""
            
            # Comprehensive static location map
            # Location map - only include GPS coordinates when they're clearly identifiable
            # Use None for coordinates when location is ambiguous or multiple cafes exist
            location_map = {
                # Chile - specific locations mentioned
                'valparaiso': ('Valparaiso', 'Chile', 'South America', -33.0472, -71.6127, 'Le Bagon\'s'),
                'valpoloco': ('Valparaiso', 'Chile', 'South America', -33.0472, -71.6127, 'Le Bagon\'s'),
                'santiago': ('Santiago', 'Chile', 'South America', None, None, ''),
                'vina del mar': ('Vina del Mar', 'Chile', 'South America', -33.0153, -71.5500, ''),
                
                # Argentina
                'buenos aires': ('Buenos Aires', 'Argentina', 'South America', None, None, ''),
                
                # Japan - major cities, coords only if very specific
                'tokyo': ('Tokyo', 'Japan', 'Asia', None, None, ''),
                'kyoto': ('Kyoto', 'Japan', 'Asia', None, None, ''),
                
                # Europe
                'paris': ('Paris', 'France', 'Europe', None, None, ''),
                'rome': ('Rome', 'Italy', 'Europe', None, None, ''),
                
                # USA - major cities without coords, small towns with coords
                'portland': ('Portland', 'United States', 'North America', None, None, ''),
                'seattle': ('Seattle', 'United States', 'North America', None, None, ''),
                'brooklyn': ('Brooklyn', 'United States', 'North America', None, None, ''),
                'bushwick': ('Brooklyn', 'United States', 'North America', None, None, ''),
                'new york': ('New York', 'United States', 'North America', None, None, ''),
                'nyc': ('New York', 'United States', 'North America', None, None, ''),
                
                # Mountain West - smaller towns with specific coords
                'silverton': ('Silverton', 'United States', 'North America', 37.8117, -107.6645, ''),
                'gunnison': ('Gunnison', 'United States', 'North America', 38.6477, -107.0603, ''),
                'slc': ('Salt Lake City', 'United States', 'North America', None, None, ''),
                'salt lake city': ('Salt Lake City', 'United States', 'North America', None, None, ''),
                
                # Canada - specific smaller towns with coords, major cities without
                'revelstoke': ('Revelstoke', 'Canada', 'North America', 50.9981, -118.1957, 'The Modern Bakeshop & Cafe'),
                'invermere': ('Invermere', 'Canada', 'North America', 50.5067, -116.0350, ''),
                'whistler': ('Whistler', 'Canada', 'North America', 50.1163, -122.9574, 'HY\'s Steakhouse'),
                'kamloops': ('Kamloops', 'Canada', 'North America', 50.6745, -120.3273, ''),
                'victoria': ('Victoria', 'Canada', 'North America', 48.4284, -123.3656, ''),
                'vancouver': ('Vancouver', 'Canada', 'North America', None, None, ''),
                'toronto': ('Toronto', 'Canada', 'North America', None, None, ''),
                'calgary': ('Calgary', 'Canada', 'North America', None, None, ''),
                
                # Mexico
                'cdmx': ('Mexico City', 'Mexico', 'North America', None, None, ''),
                'mexico city': ('Mexico City', 'Mexico', 'North America', None, None, ''),
                
                # Australia
                'melbourne': ('Melbourne', 'Australia', 'Oceania', None, None, ''),
                'sydney': ('Sydney', 'Australia', 'Oceania', None, None, ''),
            }
            
            # Match location from caption
            caption_lower = caption.lower()
            for location_key, (city_name, country_name, continent_name, lat, lng, cafe) in location_map.items():
                if location_key in caption_lower:
                    city = city_name
                    country = country_name
                    continent = continent_name
                    latitude = lat
                    longitude = lng
                    cafe_name = cafe
                    print(f"    📌 Found location: {city}, {country}")
                    break
            
            # Generate filename
            slug = re.sub(r'[^\w\s-]', '', post_title.lower())
            slug = re.sub(r'[-\s]+', '-', slug)[:30]
            
            # Create a unique key for this post based on title and timestamp
            post_key = f"{date_str}-{slug}-{timestamp}"
            
            # Skip if we already processed this exact post in this run
            if post_key in processed_posts:
                skipped += 1
                print(f"  ⏭️ Skipping duplicate in this run: {post_key}")
                continue
                
            processed_posts.add(post_key)
            
            filename = f"{post_key}.md"
            filepath = posts_dir / filename
            
            # Check if this post already exists (idempotent behavior)
            existing_files = list(posts_dir.glob(f"{date_str}-{slug}-*.md"))
            if existing_files:
                # Update existing file
                filepath = existing_files[0]
                updated += 1
                print(f"  🔄 Updating existing: {filepath.name}")
            else:
                created += 1
                print(f"  ✅ Creating: {filename}")
            
            # Create Jekyll post with YAML-safe content
            # Only include coordinates if they're actually set (not None)
            lat_value = latitude if latitude is not None else ""
            lng_value = longitude if longitude is not None else ""
            
            # Format image paths for YAML
            images_yaml = ""
            if len(image_paths) > 1:
                images_yaml = "images:\n"
                for img_path in image_paths:
                    images_yaml += f"  - \"{img_path}\"\n"
            
            post_content = f"""---
layout: post
title: {yaml_safe_string(post_title)}
date: {date_str}
city: {yaml_safe_string(city)}
country: {yaml_safe_string(country)}
continent: {yaml_safe_string(continent)}
latitude: {lat_value}
longitude: {lng_value}
cafe_name: {yaml_safe_string(cafe_name)}
rating: 
notes: {yaml_safe_string(notes)}
image_url: "{image_path}"
{images_yaml.rstrip()}
instagram_url: ""
---"""
            
            filepath.write_text(post_content)
            
        except Exception as e:
            print(f"  ❌ Error processing post {i}: {e}")
    
    print(f"\n🎉 Results:")
    print(f"  ✅ Created {created} new Jekyll posts")
    print(f"  🔄 Updated {updated} existing Jekyll posts")
    print(f"  📸 Copied {images_copied} images")
    if skipped > 0:
        print(f"  ⏭️ Skipped {skipped} posts (no changes)")
    print("🔄 Your site is rebuilding with all your coffee photos!")
    return created + updated

if __name__ == "__main__":
    print("""
☕ Processing Your Instagram Export (Enhanced with Images)
========================================================
""")
    process_instagram_export_with_images()