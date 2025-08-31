#!/usr/bin/env python3
"""
Process Instagram export for World Coffee Tour
Handles the actual Instagram export format with photos
"""

import json
import re
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse
import time

def extract_location_from_caption(caption):
    """Extract location information from Instagram caption"""
    locations_found = []
    
    # Enhanced location patterns
    location_patterns = [
        r'in\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|\n|#|@|\s+\w+:)',
        r'at\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|\n|#|@|\s+\w+:)',
        r'from\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|\n|#|@|\s+\w+:)',
        r'^([A-Z][a-zA-Z\s]+?)(?:\.|,|\n|#)',  # Start of caption
        r'(?:stop|visit|cafe|coffee)\s+(?:on\s+the\s+\w+\s+)?in\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|\n|#)',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, caption, re.MULTILINE)
        for match in matches:
            location = match.strip()
            # Filter out common false positives
            if (len(location) > 3 and 
                not location.lower() in ['instagram', 'worldcoffeetour', 'coffee', 'cafe', 'the', 'this', 'that'] and
                not location.startswith('@')):
                locations_found.append(location)
    
    return locations_found

def geocode_location(location_name, retries=3):
    """Get coordinates for a location using Nominatim (OpenStreetMap)"""
    if not location_name:
        return None
    
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': location_name,
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    for attempt in range(retries):
        try:
            # Be respectful to Nominatim - add delay
            time.sleep(1)
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'WorldCoffeeTour/1.0 (https://worldcoffeetour.joegaudet.com)')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if data:
                    result = data[0]
                    address = result.get('address', {})
                    
                    # Extract hierarchical location info
                    city = (address.get('city') or 
                           address.get('town') or 
                           address.get('village') or 
                           address.get('municipality') or
                           location_name.split(',')[0].strip())
                    
                    country = address.get('country', 'Unknown')
                    country_code = address.get('country_code', '').upper()
                    
                    # Determine continent from country
                    continent = get_continent_from_country(country, country_code)
                    
                    return {
                        'lat': float(result['lat']),
                        'lng': float(result['lon']),
                        'city': city,
                        'country': country,
                        'continent': continent,
                        'display_name': result.get('display_name', location_name)
                    }
        
        except Exception as e:
            print(f"    Geocoding attempt {attempt + 1} failed for '{location_name}': {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return None

def get_continent_from_country(country, country_code=''):
    """Map country to continent"""
    continent_mapping = {
        # North America
        'united states': 'North America', 'usa': 'North America', 'us': 'North America',
        'canada': 'North America', 'mexico': 'North America',
        
        # South America  
        'brazil': 'South America', 'argentina': 'South America', 'chile': 'South America',
        'colombia': 'South America', 'peru': 'South America', 'venezuela': 'South America',
        'uruguay': 'South America', 'bolivia': 'South America',
        
        # Europe
        'france': 'Europe', 'italy': 'Europe', 'spain': 'Europe', 'germany': 'Europe',
        'united kingdom': 'Europe', 'uk': 'Europe', 'england': 'Europe', 'scotland': 'Europe',
        'netherlands': 'Europe', 'belgium': 'Europe', 'switzerland': 'Europe', 
        'portugal': 'Europe', 'greece': 'Europe', 'poland': 'Europe',
        
        # Asia
        'japan': 'Asia', 'china': 'Asia', 'india': 'Asia', 'south korea': 'Asia',
        'thailand': 'Asia', 'vietnam': 'Asia', 'singapore': 'Asia', 'malaysia': 'Asia',
        'philippines': 'Asia', 'indonesia': 'Asia',
        
        # Oceania
        'australia': 'Oceania', 'new zealand': 'Oceania',
        
        # Africa
        'south africa': 'Africa', 'morocco': 'Africa', 'egypt': 'Africa'
    }
    
    country_lower = country.lower()
    if country_lower in continent_mapping:
        return continent_mapping[country_lower]
    
    # Fallback by country code
    country_code_mapping = {
        'US': 'North America', 'CA': 'North America', 'MX': 'North America',
        'BR': 'South America', 'AR': 'South America', 'CL': 'South America',
        'FR': 'Europe', 'IT': 'Europe', 'ES': 'Europe', 'DE': 'Europe', 'GB': 'Europe',
        'JP': 'Asia', 'CN': 'Asia', 'IN': 'Asia', 'KR': 'Asia',
        'AU': 'Oceania', 'NZ': 'Oceania'
    }
    
    if country_code in country_code_mapping:
        return country_code_mapping[country_code]
    
    return 'Unknown'

def find_cafe_at_location(latitude, longitude, retries=2):
    """Find cafe names near the given coordinates using Nominatim reverse geocoding and Overpass API"""
    if not latitude or not longitude:
        return None
    
    try:
        # Use Overpass API to find cafes/restaurants near the location
        # This is free and doesn't require API keys
        radius = 50  # Search within 50 meters
        
        overpass_query = f"""
        [out:json][timeout:10];
        (
          node["amenity"~"^(cafe|restaurant)$"](around:{radius},{latitude},{longitude});
          way["amenity"~"^(cafe|restaurant)$"](around:{radius},{latitude},{longitude});
          relation["amenity"~"^(cafe|restaurant)$"](around:{radius},{latitude},{longitude});
        );
        out center;
        """
        
        url = "https://overpass-api.de/api/interpreter"
        data = overpass_query.encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('User-Agent', 'WorldCoffeeTour/1.0 (https://worldcoffeetour.joegaudet.com)')
        
        # Add delay to be respectful
        time.sleep(1)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            
            elements = result.get('elements', [])
            cafes = []
            
            for element in elements:
                tags = element.get('tags', {})
                name = tags.get('name')
                amenity = tags.get('amenity')
                
                if name and amenity in ['cafe', 'restaurant']:
                    # Calculate rough distance (not perfect but good enough)
                    lat_diff = abs(element.get('lat', 0) - latitude)
                    lon_diff = abs(element.get('lon', 0) - longitude)
                    distance = (lat_diff + lon_diff) * 111000  # Rough meters
                    
                    cafes.append({
                        'name': name,
                        'type': amenity,
                        'distance': distance
                    })
            
            # Sort by distance and prefer cafes over restaurants
            cafes.sort(key=lambda x: (x['distance'], 0 if x['type'] == 'cafe' else 1))
            
            if cafes:
                best_match = cafes[0]
                print(f"    ☕ Found cafe: {best_match['name']} ({best_match['type']}, ~{int(best_match['distance'])}m away)")
                return best_match['name']
        
    except Exception as e:
        print(f"    ❌ Cafe lookup failed: {e}")
    
    return None

def yaml_safe_string(text):
    """Make a string safe for YAML by properly escaping it"""
    if not text:
        return '""'
    
    # Clean up the text first
    text = str(text)
    
    # Fix UTF-8 encoding issues first - handle byte sequences
    # Handle the specific byte sequences found in Instagram exports
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
    """Process your Instagram export with photos"""
    
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
            
            # Get image path - use the first media item
            image_path = ""
            if post.get('media') and len(post['media']) > 0:
                # Get the URI from the first media item
                media_uri = post['media'][0].get('uri', '')
                if media_uri:
                    # Convert the path to be relative to our site root
                    # The URI is like "media/posts/202508/filename.jpg"
                    # We've copied the media folder to our root
                    image_path = f"/{media_uri}"
            
            # Extract and geocode location from caption
            latitude = None
            longitude = None
            city = "Unknown"
            country = "Unknown"
            continent = "World"
            
            print(f"    🔍 Analyzing location in: {caption[:80]}...")
            
            # Extract potential locations from caption
            potential_locations = extract_location_from_caption(caption)
            geo_data = None
            
            if potential_locations:
                print(f"    📍 Found potential locations: {potential_locations}")
                
                # Try to geocode the first/best location
                for location in potential_locations[:2]:  # Try max 2 to avoid too many API calls
                    print(f"    🌍 Geocoding: {location}")
                    geo_data = geocode_location(location)
                    if geo_data:
                        print(f"    ✅ Found coordinates: {geo_data['city']}, {geo_data['country']}")
                        latitude = geo_data['lat']
                        longitude = geo_data['lng'] 
                        city = geo_data['city']
                        country = geo_data['country']
                        continent = geo_data['continent']
                        break
                    else:
                        print(f"    ❌ Could not geocode: {location}")
            
            if not geo_data:
                print(f"    ⚠️ No geographic data found, using defaults")
                
                # Fallback to static location map for known places
                location_map = {
                    'valparaiso': ('Valparaiso', 'Chile', 'South America', -33.0472, -71.6127),
                    'valpoloco': ('Valparaiso', 'Chile', 'South America', -33.0472, -71.6127),
                    'santiago': ('Santiago', 'Chile', 'South America', -33.4489, -70.6693),
                    'buenos aires': ('Buenos Aires', 'Argentina', 'South America', -34.6118, -58.3960),
                    'tokyo': ('Tokyo', 'Japan', 'Asia', 35.6762, 139.6503),
                    'kyoto': ('Kyoto', 'Japan', 'Asia', 35.0116, 135.7681),
                    'paris': ('Paris', 'France', 'Europe', 48.8566, 2.3522),
                    'rome': ('Rome', 'Italy', 'Europe', 41.9028, 12.4964),
                    'portland': ('Portland', 'United States', 'North America', 45.5152, -122.6784),
                    'seattle': ('Seattle', 'United States', 'North America', 47.6062, -122.3321),
                    'melbourne': ('Melbourne', 'Australia', 'Oceania', -37.8136, 144.9631),
                    'sydney': ('Sydney', 'Australia', 'Oceania', -33.8688, 151.2093),
                    'revelstoke': ('Revelstoke', 'Canada', 'North America', 50.9981, -118.1957),
                    'kamloops': ('Kamloops', 'Canada', 'North America', 50.6745, -120.3273),
                    'whistler': ('Whistler', 'Canada', 'North America', 50.1163, -122.9574),
                    'toronto': ('Toronto', 'Canada', 'North America', 43.6532, -79.3832),
                    'brooklyn': ('Brooklyn', 'United States', 'North America', 40.6782, -73.9442),
                    'bushwick': ('Brooklyn', 'United States', 'North America', 40.6975, -73.9156),
                    'cdmx': ('Mexico City', 'Mexico', 'North America', 19.4326, -99.1332),
                    'mexico city': ('Mexico City', 'Mexico', 'North America', 19.4326, -99.1332),
                    'invermere': ('Invermere', 'Canada', 'North America', 50.5067, -116.0350),
                }
                
                caption_lower = caption.lower()
                for location_key, (city_name, country_name, continent_name, lat, lng) in location_map.items():
                    if location_key in caption_lower:
                        city = city_name
                        country = country_name
                        continent = continent_name
                        latitude = lat
                        longitude = lng
                        print(f"    📌 Using static location: {city}, {country}")
                        break
            
            # Look up cafe name if we have coordinates
            cafe_name = ""
            if latitude is not None and longitude is not None:
                print(f"    🔍 Looking up cafe at coordinates: {latitude}, {longitude}")
                cafe_name = find_cafe_at_location(latitude, longitude)
                if not cafe_name:
                    print(f"    ❌ No cafe found at location")
            
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
☕ Processing Your Instagram Export
===================================
""")
    process_instagram_export()