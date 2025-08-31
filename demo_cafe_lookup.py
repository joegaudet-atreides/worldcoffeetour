#!/usr/bin/env python3
"""
Demo cafe lookup for posts with missing location data
"""

import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

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

def extract_locations_from_caption(caption: str):
    """Extract potential location hints from caption"""
    # Look for "Fahrenheit Coffee" in the caption
    locations = []
    
    # Common patterns
    patterns = [
        r'([A-Z][a-zA-Z\s]+Coffee)',  # "[Name] Coffee"
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "in Location"
        r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "at Location"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})',  # "City, ST"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, caption)
        for match in matches:
            if isinstance(match, tuple):
                locations.extend([m for m in match if m])
            else:
                locations.append(match)
    
    return locations

def geocode_location(location: str):
    """Simple geocoding test"""
    try:
        params = urllib.parse.urlencode({
            'q': location,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        })
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'WorldCoffeeTour/1.0 (demo)')
        
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
                       location)
                country = address.get('country', 'Unknown')
                
                return {
                    'latitude': lat,
                    'longitude': lon,
                    'city': city,
                    'country': country,
                    'display_name': result.get('display_name', '')
                }
    except Exception as e:
        print(f"Error geocoding '{location}': {e}")
    
    return None

def demo_lookup():
    """Demonstrate lookup for specific problematic posts"""
    posts = load_posts()
    
    print("🔍 Looking for posts with missing location data...\n")
    
    for i, post in enumerate(posts, 1):
        caption = post.get('title', '')
        
        # Focus on the Fahrenheit Coffee post
        if 'fahrenheit coffee' in caption.lower():
            print(f"🎯 Found problematic post #{i}:")
            print(f"Caption: {caption}")
            print()
            
            # Try to extract location hints
            locations = extract_locations_from_caption(caption)
            print(f"📍 Location hints found: {locations}")
            
            if locations:
                for location in locations:
                    print(f"\n🔎 Trying to geocode: '{location}'")
                    result = geocode_location(location)
                    
                    if result:
                        print(f"✅ Found: {result['city']}, {result['country']}")
                        print(f"📍 Coordinates: {result['latitude']:.4f}, {result['longitude']:.4f}")
                        print(f"🌍 Full address: {result['display_name']}")
                    else:
                        print("❌ No results found")
                        
                        # Try just "Fahrenheit" without "Coffee"
                        if 'coffee' in location.lower():
                            base_name = location.replace(' Coffee', '').replace(' coffee', '')
                            print(f"🔄 Trying without 'Coffee': '{base_name}'")
                            result = geocode_location(base_name)
                            if result:
                                print(f"✅ Found: {result['city']}, {result['country']}")
                                print(f"📍 Coordinates: {result['latitude']:.4f}, {result['longitude']:.4f}")
            
            print("-" * 60)
            break

if __name__ == "__main__":
    demo_lookup()