#!/usr/bin/env python3
"""
Interactive cafe lookup interface for World Coffee Tour posts
Helps identify missing cafe names and locations
"""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time

def load_posts():
    """Load Instagram export posts"""
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
    
    return coffee_posts

def extract_location_from_caption(caption: str) -> Optional[str]:
    """Extract likely location mentions from caption"""
    # Common location patterns
    location_patterns = [
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "in Vancouver" 
        r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "at Whistler"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+stop',  # "Vancouver stop"
        r'([A-Z][a-z]+),\s*([A-Z][a-z]+)',  # "Vancouver, BC"
    ]
    
    locations = []
    for pattern in location_patterns:
        matches = re.findall(pattern, caption)
        for match in matches:
            if isinstance(match, tuple):
                locations.extend(match)
            else:
                locations.append(match)
    
    # Filter out common false positives
    false_positives = {'Coffee', 'Tour', 'Stop', 'Day', 'Good', 'Great', 'Amazing', 'Fantastic'}
    locations = [loc for loc in locations if loc not in false_positives and len(loc) > 2]
    
    return locations[0] if locations else None

def geocode_location(location: str) -> Optional[Tuple[float, float, str, str, str]]:
    """Geocode a location using OpenStreetMap Nominatim"""
    try:
        # Build URL with parameters
        params = urllib.parse.urlencode({
            'q': location,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        })
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        
        # Create request with headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'WorldCoffeeTour/1.0 (https://worldcoffeetour.joegaudet.com)')
        
        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                
                # Extract address components
                address = result.get('address', {})
                city = (address.get('city') or 
                       address.get('town') or 
                       address.get('village') or 
                       location)
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
                
                return lat, lon, city, country, continent
                
    except Exception as e:
        print(f"    ❌ Geocoding error for '{location}': {e}")
    
    return None

def find_cafe_at_location(latitude: float, longitude: float, retries: int = 2) -> Optional[str]:
    """Find cafe names near coordinates using Overpass API"""
    for attempt in range(retries):
        try:
            # Search for cafes and restaurants within 100m
            overpass_query = f"""
            [out:json][timeout:10];
            (
              node["amenity"~"^(cafe|restaurant)$"](around:100,{latitude},{longitude});
              way["amenity"~"^(cafe|restaurant)$"](around:100,{latitude},{longitude});
            );
            out center;
            """
            
            # Create request
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
                    
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            if attempt < retries - 1:
                print(f"    ⚠️ Overpass API attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
            else:
                print(f"    ❌ Overpass API error: {e}")
    
    return None

def analyze_posts():
    """Analyze posts and provide interactive lookup interface"""
    posts = load_posts()
    print(f"\n☕ Found {len(posts)} coffee tour posts")
    print("=" * 60)
    
    missing_locations = []
    missing_cafes = []
    
    for i, post in enumerate(posts, 1):
        timestamp = post.get('creation_timestamp', 0)
        date = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        caption = post.get('title', '')
        
        print(f"\n[{i:2d}] {date.strftime('%Y-%m-%d')}")
        print(f"Caption: {caption[:100]}{'...' if len(caption) > 100 else ''}")
        
        # Try to extract location from caption
        location_hint = extract_location_from_caption(caption)
        if location_hint:
            print(f"📍 Detected location: {location_hint}")
            
            # Try to geocode
            geo_result = geocode_location(location_hint)
            if geo_result:
                lat, lon, city, country, continent = geo_result
                print(f"🌍 Geocoded: {city}, {country} ({continent}) - {lat:.4f}, {lon:.4f}")
                
                # Try to find cafe
                cafe = find_cafe_at_location(lat, lon)
                if cafe:
                    print(f"☕ Found cafe: {cafe}")
                else:
                    print("☕ No cafe found at location")
                    missing_cafes.append({
                        'index': i,
                        'date': date.strftime('%Y-%m-%d'),
                        'location': location_hint,
                        'coordinates': (lat, lon),
                        'city': city,
                        'country': country,
                        'caption': caption
                    })
            else:
                print("❌ Could not geocode location")
                missing_locations.append({
                    'index': i,
                    'date': date.strftime('%Y-%m-%d'),
                    'location': location_hint,
                    'caption': caption
                })
        else:
            print("❓ No location detected in caption")
            missing_locations.append({
                'index': i,
                'date': date.strftime('%Y-%m-%d'),
                'location': None,
                'caption': caption
            })
        
        # Add delay to be respectful to APIs
        if i % 5 == 0:
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total posts: {len(posts)}")
    print(f"Missing locations: {len(missing_locations)}")
    print(f"Missing cafes: {len(missing_cafes)}")
    
    if missing_locations:
        print(f"\n❓ POSTS MISSING LOCATION DATA:")
        for item in missing_locations[:10]:  # Show first 10
            print(f"  [{item['index']:2d}] {item['date']} - {item['caption'][:80]}...")
    
    if missing_cafes:
        print(f"\n☕ POSTS MISSING CAFE DATA:")
        for item in missing_cafes[:10]:  # Show first 10
            loc = item['location'] if item['location'] else f"{item['city']}, {item['country']}"
            print(f"  [{item['index']:2d}] {item['date']} - {loc}")
    
    return missing_locations, missing_cafes

def interactive_lookup():
    """Interactive mode to manually lookup specific posts"""
    posts = load_posts()
    
    while True:
        print("\n" + "=" * 60)
        print("🔍 INTERACTIVE CAFE LOOKUP")
        print("=" * 60)
        print("1. Analyze all posts")
        print("2. Lookup specific post by index")
        print("3. Search location manually")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            analyze_posts()
        elif choice == '2':
            try:
                index = int(input("Enter post index (1-49): ")) - 1
                if 0 <= index < len(posts):
                    post = posts[index]
                    caption = post.get('title', '')
                    print(f"\nPost {index + 1}: {caption}")
                    
                    location = input("Enter location to lookup (or press Enter to extract from caption): ").strip()
                    if not location:
                        location = extract_location_from_caption(caption)
                        if not location:
                            print("❌ No location detected")
                            continue
                    
                    print(f"Looking up: {location}")
                    geo_result = geocode_location(location)
                    if geo_result:
                        lat, lon, city, country, continent = geo_result
                        print(f"🌍 Location: {city}, {country} ({continent})")
                        print(f"📍 Coordinates: {lat:.6f}, {lon:.6f}")
                        
                        cafe = find_cafe_at_location(lat, lon)
                        if cafe:
                            print(f"☕ Cafe found: {cafe}")
                        else:
                            print("☕ No cafe found")
                    else:
                        print("❌ Could not geocode location")
                else:
                    print("❌ Invalid post index")
            except ValueError:
                print("❌ Invalid input")
        elif choice == '3':
            location = input("Enter location to search: ").strip()
            if location:
                geo_result = geocode_location(location)
                if geo_result:
                    lat, lon, city, country, continent = geo_result
                    print(f"🌍 Location: {city}, {country} ({continent})")
                    print(f"📍 Coordinates: {lat:.6f}, {lon:.6f}")
                    
                    cafe = find_cafe_at_location(lat, lon)
                    if cafe:
                        print(f"☕ Cafe found: {cafe}")
                    else:
                        print("☕ No cafe found")
                else:
                    print("❌ Could not geocode location")
        elif choice == '4':
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    print("""
☕ World Coffee Tour - Cafe Lookup Interface
===========================================
This tool helps identify missing cafe names and locations
for your Instagram coffee tour posts.
""")
    
    interactive_lookup()