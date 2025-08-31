#!/usr/bin/env python3
"""
Fast Instagram export processor - skips slow API calls
"""

import json
import re
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

def process_instagram_export():
    """Process your Instagram export with photos - fast version"""
    
    # Load posts
    with open('instagram-export-folder/your_instagram_activity/media/posts_1.json', 'r', encoding='utf-8') as f:
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
    
    # Create Jekyll posts
    posts_dir = Path("_coffee_posts")
    posts_dir.mkdir(exist_ok=True)
    
    # Get existing posts to avoid duplicates (idempotent behavior)
    existing_posts = set()
    for existing_post in posts_dir.glob("*.md"):
        existing_posts.add(existing_post.stem)
    
    created = 0
    skipped = 0
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
            
            # Get all image paths from media items
            image_paths = []
            image_path = ""  # Primary image for backwards compatibility
            
            if post.get('media') and len(post['media']) > 0:
                for media_item in post['media']:
                    media_uri = media_item.get('uri', '')
                    if media_uri:
                        # Convert the path to be relative to our site root
                        # The URI is like "media/posts/202508/filename.jpg"
                        full_path = f"/{media_uri}"
                        image_paths.append(full_path)
                
                # Set primary image to first one for backwards compatibility
                if image_paths:
                    image_path = image_paths[0]
            
            # Use static location mapping for speed
            latitude = None
            longitude = None
            city = "Unknown"
            country = "Unknown"
            continent = "World"
            cafe_name = ""
            
            # Comprehensive static location map
            location_map = {
                'valparaiso': ('Valparaiso', 'Chile', 'South America', -33.0472, -71.6127, 'Le Bagon\'s'),
                'valpoloco': ('Valparaiso', 'Chile', 'South America', -33.0472, -71.6127, 'Le Bagon\'s'),
                'santiago': ('Santiago', 'Chile', 'South America', -33.4489, -70.6693, ''),
                'buenos aires': ('Buenos Aires', 'Argentina', 'South America', -34.6118, -58.3960, ''),
                'tokyo': ('Tokyo', 'Japan', 'Asia', 35.6762, 139.6503, ''),
                'kyoto': ('Kyoto', 'Japan', 'Asia', 35.0116, 135.7681, ''),
                'paris': ('Paris', 'France', 'Europe', 48.8566, 2.3522, ''),
                'rome': ('Rome', 'Italy', 'Europe', 41.9028, 12.4964, ''),
                'portland': ('Portland', 'United States', 'North America', 45.5152, -122.6784, ''),
                'seattle': ('Seattle', 'United States', 'North America', 47.6062, -122.3321, ''),
                'melbourne': ('Melbourne', 'Australia', 'Oceania', -37.8136, 144.9631, ''),
                'sydney': ('Sydney', 'Australia', 'Oceania', -33.8688, 151.2093, ''),
                'revelstoke': ('Revelstoke', 'Canada', 'North America', 50.9981, -118.1957, 'The Modern Bakeshop & Cafe'),
                'kamloops': ('Kamloops', 'Canada', 'North America', 50.6745, -120.3273, ''),
                'whistler': ('Whistler', 'Canada', 'North America', 50.1163, -122.9574, 'HY\'s Steakhouse'),
                'toronto': ('Toronto', 'Canada', 'North America', 43.6532, -79.3832, ''),
                'brooklyn': ('Brooklyn', 'United States', 'North America', 40.6782, -73.9442, ''),
                'bushwick': ('Brooklyn', 'United States', 'North America', 40.6975, -73.9156, ''),
                'cdmx': ('Mexico City', 'Mexico', 'North America', 19.4326, -99.1332, ''),
                'mexico city': ('Mexico City', 'Mexico', 'North America', 19.4326, -99.1332, ''),
                'invermere': ('Invermere', 'Canada', 'North America', 50.5067, -116.0350, ''),
                'gunnison': ('Gunnison', 'United States', 'North America', 38.6477, -107.0603, ''),
                'slc': ('Salt Lake City', 'United States', 'North America', 40.7608, -111.8910, ''),
                'salt lake city': ('Salt Lake City', 'United States', 'North America', 40.7608, -111.8910, ''),
                'victoria': ('Victoria', 'Canada', 'North America', 48.4284, -123.3656, ''),
                'vancouver': ('Vancouver', 'Canada', 'North America', 49.2827, -123.1207, ''),
                'calgary': ('Calgary', 'Canada', 'North America', 51.0447, -114.0719, ''),
                'new york': ('New York', 'United States', 'North America', 40.7128, -74.0060, ''),
                'nyc': ('New York', 'United States', 'North America', 40.7128, -74.0060, ''),
                'vina del mar': ('Vina del Mar', 'Chile', 'South America', -33.0153, -71.5500, ''),
                'silverton': ('Silverton', 'United States', 'North America', 37.8117, -107.6645, ''),
            }
            
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
            filename = f"{date_str}-{slug}-{i}.md"
            filepath = posts_dir / filename
            
            # Check if this post already exists (idempotent behavior)
            if filepath.stem in existing_posts:
                skipped += 1
                print(f"  ⏭️ Skipped existing: {filename}")
                continue
            
            # Create Jekyll post with YAML-safe content
            lat_value = latitude if latitude is not None else "null"
            lng_value = longitude if longitude is not None else "null"
            
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
            created += 1
            print(f"  ✅ Created: {filename}")
            
        except Exception as e:
            print(f"  ❌ Error processing post {i}: {e}")
    
    print(f"\n🎉 Created {created} Jekyll posts!")
    if skipped > 0:
        print(f"⏭️ Skipped {skipped} existing posts (already processed)")
    print("🔄 Your site is rebuilding with all your coffee photos!")
    return created

if __name__ == "__main__":
    print("""
☕ Processing Your Instagram Export (Fast Mode)
===============================================
""")
    process_instagram_export()