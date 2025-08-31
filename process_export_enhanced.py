#!/usr/bin/env python3
"""
Enhanced Instagram export processor with improved location and cafe detection
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
import time
import os

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

def extract_location_from_caption(caption: str):
    """Extract location hints from caption with improved @ mention and context handling"""
    locations = []
    
    # Enhanced location patterns
    location_patterns = [
        r'([A-Z][a-zA-Z\s]+Coffee)',  # "[Name] Coffee"
        r'([A-Z][a-zA-Z\s]+Cafe)',    # "[Name] Cafe"  
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "in Vancouver"
        r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "at Whistler"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+stop',  # "Vancouver stop"
        r'([A-Z][a-z]+),\s*([A-Z][a-z]+)',  # "Vancouver, BC"
        r'([A-Z][a-z]+),\s*([A-Z]{2})',  # "Toronto, ON"
        r'leg\s+of\s+the.*?([A-Z][a-z]+)',  # "Denver leg of the trip"
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, caption)
        for match in matches:
            if isinstance(match, tuple):
                locations.extend([m for m in match if m])
            else:
                locations.append(match)
    
    # Enhanced @ mention to location mapping for known businesses
    business_location_map = {
        'mercatodiluigi': 'Vancouver',
        'cafeblackmamba': 'Santiago', 
        'goodnickbar': 'Vina del Mar',
        'tributary_coffee_roasters': 'Gunnison',
        'bklynmacs': 'Brooklyn',
        'blackfoxcoffee': 'New York',
        'fahrenheitcoffee': 'Toronto',
        'voodoochild': 'Toronto',
    }
    
    # Extract @ mentions and map to locations
    at_mentions = re.findall(r'@([a-zA-Z0-9_]+)', caption.lower())
    for mention in at_mentions:
        if mention in business_location_map:
            locations.append(business_location_map[mention])
            print(f"    🏷️ @ mention '{mention}' → {business_location_map[mention]}")
    
    # Toronto slang detection
    if re.search(r'\bTO\b', caption) and ('NYC' in caption or 'New York' in caption):
        locations.append('Toronto')
        print(f"    🍁 Toronto slang 'TO' detected")
    
    # FIDI (Financial District NYC) detection  
    if 'FIDI' in caption or 'fidi' in caption.lower():
        locations.append('New York')
        print(f"    🏢 FIDI (Financial District) → New York")
    
    # Filter out common false positives
    false_positives = {'Tour', 'Stop', 'Day', 'Good', 'Great', 'Amazing', 'Fantastic', 'World', 'Coffee'}
    locations = [loc for loc in locations if loc not in false_positives and len(loc) > 2]
    
    return locations

def extract_cafe_name_from_caption(caption: str):
    """Extract cafe name from @ mentions in caption"""
    # Enhanced @ mention to cafe name mapping
    business_name_map = {
        'mercatodiluigi': 'Mercato di Luigi',
        'cafeblackmamba': 'Cafe Black Mamba', 
        'goodnickbar': 'Good Nick Bar',
        'tributary_coffee_roasters': 'Tributary Coffee Roasters',
        'bklynmacs': 'Brooklyn Macs',
        'blackfoxcoffee': 'Black Fox Coffee Co',
        'fahrenheitcoffee': 'Fahrenheit Coffee',
        'voodoochild': 'Voodoo Child',
        'sey_coffee': 'Sey Coffee',
        'tinaaluu': None,  # Person, not a cafe
        'rsupeene': None,  # Person, not a cafe
    }
    
    # Extract @ mentions
    at_mentions = re.findall(r'@([a-zA-Z0-9_]+)', caption.lower())
    
    for mention in at_mentions:
        if mention in business_name_map and business_name_map[mention]:
            print(f"    ☕ @ mention '{mention}' → {business_name_map[mention]}")
            return business_name_map[mention]
    
    return ""

def geocode_location(location: str):
    """Geocode a location using OpenStreetMap Nominatim"""
    try:
        params = urllib.parse.urlencode({
            'q': location,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        })
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'WorldCoffeeTour/1.0 (https://worldcoffeetour.joegaudet.com)')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                
                address = result.get('address', {})
                city = (address.get('city') or 
                       address.get('town') or 
                       address.get('village') or 
                       location.split()[0])  # Use first word as fallback
                country = address.get('country', 'Unknown')
                
                # Map country to continent
                continent_map = {
                    'Canada': 'North America',
                    'United States': 'North America', 
                    'United States of America': 'North America',
                    'Mexico': 'North America',
                    'Chile': 'South America',
                    'Argentina': 'South America',
                    'Brazil': 'South America',
                    'United Kingdom': 'Europe',
                    'France': 'Europe',
                    'Germany': 'Europe',
                    'Italy': 'Europe',
                    'Spain': 'Europe',
                    'Japan': 'Asia',
                    'China': 'Asia',
                    'India': 'Asia',
                    'Australia': 'Oceania',
                    'New Zealand': 'Oceania'
                }
                continent = continent_map.get(country, 'World')
                
                # Extract cafe name from location if it contains "Coffee" or "Cafe"
                cafe_name = ""
                if any(word in location for word in ['Coffee', 'Cafe', 'cafe', 'coffee']):
                    # It's likely a cafe name
                    cafe_name = location
                
                return lat, lon, city, country, continent, cafe_name
                
    except Exception as e:
        print(f"    ❌ Geocoding error for '{location}': {e}")
    
    return None

def find_cafe_at_location(latitude: float, longitude: float):
    """Find cafe names near coordinates using Overpass API"""
    try:
        overpass_query = f"""
        [out:json][timeout:10];
        (
          node["amenity"~"^(cafe|restaurant)$"](around:100,{latitude},{longitude});
          way["amenity"~"^(cafe|restaurant)$"](around:100,{latitude},{longitude});
        );
        out center;
        """
        
        req = urllib.request.Request(
            'https://overpass-api.de/api/interpreter',
            data=overpass_query.encode('utf-8'),
            headers={'User-Agent': 'WorldCoffeeTour/1.0'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            cafes = []
            
            for element in data.get('elements', []):
                name = element.get('tags', {}).get('name')
                amenity = element.get('tags', {}).get('amenity')
                
                if name and amenity in ['cafe', 'restaurant']:
                    cafes.append(name)
            
            if cafes:
                return cafes[0]  # Return first cafe found
                
    except Exception as e:
        print(f"    ❌ Overpass API error: {e}")
    
    return None

def load_corrections():
    """Load manual corrections from JSON file"""
    corrections_file = Path("post-corrections.json")
    if corrections_file.exists():
        with open(corrections_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Remove metadata fields starting with _
        return {k: v for k, v in data.items() if not k.startswith('_')}
    return {}

def get_post_key(post_data):
    """Generate consistent key for post identification"""
    # Use creation timestamp as unique identifier
    timestamp = post_data.get('creation_timestamp', 0)
    # Create a simplified title for the key
    title = post_data.get('title', '')[:50]
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title).strip()
    title = re.sub(r'\s+', '-', title).lower()
    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    return f"coffee/{date_str}-{title}-{timestamp}"

def apply_corrections(post_data, corrections):
    """Apply manual corrections to post data"""
    post_key = get_post_key(post_data)
    if post_key in corrections:
        print(f"   ✓ Applying manual corrections to: {post_key}")
        return {**post_data, **corrections[post_key]}
    return post_data

def process_instagram_export():
    """Process Instagram export with enhanced location detection"""
    
    # Load manual corrections
    corrections = load_corrections()
    if corrections:
        print(f"📝 Loaded {len(corrections)} manual corrections from post-corrections.json")
    
    # Load posts
    with open('instagram-export-folder/your_instagram_activity/media/posts_1.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    # Find coffee posts
    coffee_posts = []
    coffee_hashtags = [
        '#worldcoffeetour', '#worldcofeetour', '#world_coffee_tour',
        '#worldcoffee', '#cofeetour', 'worldcoffeetour', 'world coffee tour'
    ]
    
    for post in posts:
        title = post.get('title', '').lower()
        if any(hashtag in title for hashtag in coffee_hashtags):
            coffee_posts.append(post)
    
    print(f"☕ Found {len(coffee_posts)} coffee tour posts!")
    
    # Create Jekyll posts
    posts_dir = Path("_coffee_posts")
    posts_dir.mkdir(exist_ok=True)
    
    # Get existing posts to avoid duplicates (extract timestamp from filenames)
    existing_timestamps = set()
    for existing_post in posts_dir.glob("*.md"):
        # Extract timestamp from filename pattern: YYYY-MM-DD-title-TIMESTAMP.md
        filename_parts = existing_post.stem.split('-')
        if len(filename_parts) > 0:
            try:
                # Timestamp is the last part of the filename
                timestamp_str = filename_parts[-1]
                if timestamp_str.isdigit():
                    existing_timestamps.add(int(timestamp_str))
            except (ValueError, IndexError):
                pass  # Skip malformed filenames
    
    created = 0
    skipped = 0
    locations_found = 0
    cafes_found = 0
    
    for i, post in enumerate(coffee_posts, 1):
        try:
            # Apply manual corrections first
            original_post = post.copy()  # Keep original for comparison
            post = apply_corrections(post, corrections)
            
            # Get timestamp
            timestamp = post.get('creation_timestamp', 0)
            date = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            date_str = date.strftime("%Y-%m-%d")
            
            # Get caption/title and fix encoding issues early
            caption = post.get('title', '')
            
            # Fix character encoding issues immediately for better matching
            caption_fixes = {
                'â\u0080\u0099': "'",  # I â€™ve -> I've
                'â\u0080\u009c': '"',
                'â\u0080\u009d': '"', 
                'â\u0080\u0094': '-',
                'â\u0080\u0093': '-',
                'Iâ\u0080\u0099ve': "I've",
                'Iâ€™ve': "I've",
            }
            
            for wrong, right in caption_fixes.items():
                caption = caption.replace(wrong, right)
            
            # Extract first meaningful line as title
            lines = [line.strip() for line in caption.split('\n') if line.strip()]
            post_title = ""
            for line in lines:
                if not line.startswith('#') and not line.startswith('@') and len(line) > 10:
                    line = line.replace('"', '"').replace('"', '"')
                    line = line.replace(''', "'").replace(''', "'")
                    line = line.replace('—', '-').replace('–', '-')
                    post_title = line[:80]
                    break
            
            if not post_title:
                post_title = f"Coffee Stop {i}"
            
            # Clean notes
            notes = re.sub(r'#\w+\s*', '', caption).strip()
            notes = notes.replace('"', '"').replace('"', '"')
            notes = notes.replace(''', "'").replace(''', "'")
            notes = notes.replace('—', '-').replace('–', '-')
            notes = re.sub(r'\n\n+', '\n', notes).strip()
            
            # Get all image paths from media items
            image_paths = []
            image_path = ""
            
            if post.get('media') and len(post['media']) > 0:
                for media_item in post['media']:
                    media_uri = media_item.get('uri', '')
                    if media_uri:
                        full_path = f"/{media_uri}"
                        image_paths.append(full_path)
                
                if image_paths:
                    image_path = image_paths[0]
            
            # Enhanced location detection - use corrections if available
            latitude = post.get('latitude')
            longitude = post.get('longitude') 
            city = post.get('city', "Unknown")
            country = post.get('country', "Unknown")
            continent = post.get('continent', "World")
            cafe_name = post.get('cafe_name', "")
            
            # Check if this post was manually corrected
            was_corrected = post != original_post
            if was_corrected:
                print(f"    📝 Using manual corrections for location and metadata")
            
            # First try static location mapping for speed (existing logic)
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
            found_static = False
            
            # Only do static location detection if not manually corrected
            if not was_corrected:
                # Special Toronto context detection - overrides NYC mapping when TO context is present
                toronto_indicators = ['high park', 'queen west', 'queen street', 'kensington market', 'cn tower', 'harbourfront']
                if (re.search(r'\bTO\b', caption) and 
                    any(indicator in caption_lower for indicator in toronto_indicators)):
                    city = "Toronto"
                    country = "Canada" 
                    continent = "North America"
                    latitude = 43.6532
                    longitude = -79.3832
                    found_static = True
                    print(f"    🍁 Toronto context detected (TO + landmarks)")
                    locations_found += 1
                
                if not found_static:
                    for location_key, (city_name, country_name, continent_name, lat, lng, cafe) in location_map.items():
                        if location_key in caption_lower:
                            city = city_name
                            country = country_name
                            continent = continent_name
                            latitude = lat
                            longitude = lng
                            cafe_name = cafe
                            found_static = True
                            print(f"    📌 Static location: {city}, {country}")
                            locations_found += 1
                            if cafe_name:
                                cafes_found += 1
                            break
            
            # Try to extract cafe name from @ mentions first (works regardless of location detection)
            extracted_cafe = extract_cafe_name_from_caption(caption)
            if extracted_cafe and not cafe_name:
                cafe_name = extracted_cafe
                cafes_found += 1

            # If no static location found and no manual corrections, try enhanced detection
            if not found_static and not was_corrected:
                location_hints = extract_location_from_caption(caption)
                print(f"    🔍 Analyzing: {post_title[:50]}...")
                
                if location_hints:
                    print(f"    💡 Location hints: {location_hints}")
                    
                    for hint in location_hints:
                        geo_result = geocode_location(hint)
                        if geo_result:
                            lat, lon, geo_city, geo_country, geo_continent, geo_cafe = geo_result
                            
                            city = geo_city
                            country = geo_country
                            continent = geo_continent
                            latitude = lat
                            longitude = lon
                            
                            if geo_cafe and not cafe_name:
                                cafe_name = geo_cafe
                                cafes_found += 1
                            elif not cafe_name:
                                # Try to find nearby cafe
                                nearby_cafe = find_cafe_at_location(lat, lon)
                                if nearby_cafe:
                                    cafe_name = nearby_cafe
                                    cafes_found += 1
                            
                            locations_found += 1
                            print(f"    ✅ Found: {city}, {country} ({latitude:.4f}, {longitude:.4f})")
                            if cafe_name:
                                print(f"    ☕ Cafe: {cafe_name}")
                            
                            # Add small delay to be respectful to APIs
                            time.sleep(1)
                            break
            
            # Use timestamp as unique identifier for idempotency
            post_timestamp = timestamp
            
            # Check if this post already exists based on timestamp
            if post_timestamp in existing_timestamps:
                skipped += 1
                print(f"  ⏭️ Skipped existing post: {post_timestamp}")
                continue
            
            # Generate filename using timestamp for uniqueness
            slug = re.sub(r'[^\w\s-]', '', post_title.lower())
            slug = re.sub(r'[-\s]+', '-', slug)[:30]
            filename = f"{date_str}-{slug}-{post_timestamp}.md"
            filepath = posts_dir / filename
            
            # Format image paths for YAML
            images_yaml = ""
            if len(image_paths) > 1:
                images_yaml = "images:\n"
                for img_path in image_paths:
                    images_yaml += f"  - \"{img_path}\"\n"
            
            # Create Jekyll post with YAML-safe content
            lat_value = latitude if latitude is not None else "null"
            lng_value = longitude if longitude is not None else "null"
            
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
    
    print(f"\n🎉 Processing complete!")
    print(f"📊 Created {created} Jekyll posts")
    print(f"🌍 Found locations for {locations_found} posts")
    print(f"☕ Found cafe names for {cafes_found} posts")
    if skipped > 0:
        print(f"⏭️ Skipped {skipped} existing posts")
    
    return created

if __name__ == "__main__":
    print("""
☕ Processing Instagram Export (Enhanced Mode)
============================================
Includes improved location and cafe detection using OpenStreetMap APIs
""")
    process_instagram_export()