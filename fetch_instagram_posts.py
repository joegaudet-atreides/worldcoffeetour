#!/usr/bin/env python3
"""
Instagram World Coffee Tour Posts Fetcher
Run this script to fetch your Instagram posts with #worldcoffeetour hashtag
and create Jekyll posts for your website.

Requirements:
    pip install instaloader pyyaml

Usage:
    python fetch_instagram_posts.py
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path

# Configuration
INSTAGRAM_USERNAME = "joegaudet"
HASHTAG = "worldcoffeetour"
POSTS_DIR = "_coffee_posts"

def manual_entry_mode():
    """Manually enter coffee post data"""
    print("\n=== Manual Coffee Post Entry ===")
    
    # Get post details
    title = input("Post title (e.g., 'Morning Brew in Rome'): ")
    city = input("City: ")
    country = input("Country: ")
    region = input("Region (Europe/Asia/Americas/Africa/Oceania): ")
    cafe_name = input("Café name: ")
    coffee_type = input("Coffee type (e.g., Espresso, Cappuccino, Pour Over): ")
    rating = input("Rating (1-5): ")
    notes = input("Notes about the experience: ")
    
    # Get coordinates (optional)
    lat = input("Latitude (optional, press Enter to skip): ")
    lng = input("Longitude (optional, press Enter to skip): ")
    
    # Instagram URLs
    instagram_url = input("Instagram post URL: ")
    image_url = input("Image URL (or press Enter to use placeholder): ")
    
    # Generate filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = "-".join(title.lower().split()[:4])
    filename = f"{date_str}-{slug}.md"
    filepath = Path(POSTS_DIR) / filename
    
    # Create post content
    post_content = f"""---
layout: post
title: "{title}"
date: {date_str}
city: "{city}"
country: "{country}"
region: "{region}"
latitude: {lat if lat else 'null'}
longitude: {lng if lng else 'null'}
cafe_name: "{cafe_name}"
coffee_type: "{coffee_type}"
rating: {rating}
notes: "{notes}"
image_url: "{image_url if image_url else ''}"
instagram_url: "{instagram_url}"
---"""
    
    # Save post
    filepath.parent.mkdir(exist_ok=True)
    filepath.write_text(post_content)
    print(f"✅ Created post: {filepath}")

def fetch_with_instaloader():
    """Fetch posts using Instaloader (requires login)"""
    try:
        import instaloader
        
        print("\n=== Fetching Instagram Posts with Instaloader ===")
        print("Note: This requires Instagram login credentials")
        
        L = instaloader.Instaloader()
        
        # Login (required for hashtag search)
        username = input("Instagram username: ")
        password = input("Instagram password: ")
        
        try:
            L.login(username, password)
        except Exception as e:
            print(f"Login failed: {e}")
            return
        
        # Fetch posts with hashtag
        posts_data = []
        hashtag = instaloader.Hashtag.from_name(L.context, HASHTAG)
        
        count = 0
        for post in hashtag.get_posts():
            if post.owner_username == INSTAGRAM_USERNAME:
                # Extract location data if available
                location = {}
                if post.location:
                    location = {
                        'name': post.location.name,
                        'lat': post.location.lat,
                        'lng': post.location.lng
                    }
                
                posts_data.append({
                    'shortcode': post.shortcode,
                    'caption': post.caption,
                    'date': post.date_utc.isoformat(),
                    'image_url': post.url,
                    'location': location,
                    'instagram_url': f"https://www.instagram.com/p/{post.shortcode}/"
                })
                
                count += 1
                if count >= 20:  # Limit to recent 20 posts
                    break
        
        # Save to JSON
        with open('_data/instagram_posts.json', 'w') as f:
            json.dump(posts_data, f, indent=2)
        
        print(f"✅ Fetched {count} posts and saved to _data/instagram_posts.json")
        print("Now run: python fetch_instagram_posts.py --process")
        
    except ImportError:
        print("Instaloader not installed. Run: pip install instaloader")

def process_json_to_posts():
    """Process JSON data into Jekyll posts"""
    json_file = Path('_data/instagram_posts.json')
    
    if not json_file.exists():
        print("No instagram_posts.json found. Fetch posts first.")
        return
    
    with open(json_file) as f:
        posts = json.load(f)
    
    posts_dir = Path(POSTS_DIR)
    posts_dir.mkdir(exist_ok=True)
    
    # Region mapping based on common cities
    region_map = {
        'europe': ['paris', 'london', 'rome', 'berlin', 'amsterdam', 'barcelona', 'vienna', 'prague'],
        'asia': ['tokyo', 'kyoto', 'seoul', 'bangkok', 'singapore', 'hong kong', 'taipei', 'shanghai'],
        'americas': ['new york', 'portland', 'seattle', 'san francisco', 'mexico city', 'buenos aires'],
        'oceania': ['melbourne', 'sydney', 'auckland', 'wellington'],
        'africa': ['cape town', 'marrakech', 'cairo', 'nairobi']
    }
    
    def get_region(city_name):
        city_lower = city_name.lower()
        for region, cities in region_map.items():
            if any(city in city_lower for city in cities):
                return region.capitalize()
        return "World"  # Default region
    
    for post in posts:
        # Parse caption for coffee details
        caption = post.get('caption', '')
        lines = caption.split('\n')
        title = lines[0] if lines else "Coffee Stop"
        
        # Extract location
        location = post.get('location', {})
        city = location.get('name', '').split(',')[0] if location else "Unknown"
        country = location.get('name', '').split(',')[-1].strip() if location else "Unknown"
        
        # Generate filename
        date = datetime.fromisoformat(post['date'].replace('Z', '+00:00'))
        date_str = date.strftime("%Y-%m-%d")
        slug = "-".join(title.lower().split()[:4])
        filename = f"{date_str}-{slug}.md"
        filepath = posts_dir / filename
        
        # Create post content
        post_content = f"""---
layout: post
title: "{title}"
date: {date_str}
city: "{city}"
country: "{country}"
region: "{get_region(city)}"
latitude: {location.get('lat', 'null')}
longitude: {location.get('lng', 'null')}
cafe_name: ""
coffee_type: ""
rating: 
notes: "{caption}"
image_url: "{post.get('image_url', '')}"
instagram_url: "{post.get('instagram_url', '')}"
---"""
        
        filepath.write_text(post_content)
        print(f"✅ Created post: {filepath}")

def main():
    print("""
☕ World Coffee Tour - Instagram Posts Fetcher
==============================================

Choose an option:
1. Manual entry (add single post)
2. Fetch with Instaloader (requires Instagram login)
3. Process existing JSON to Jekyll posts
4. Exit
""")
    
    choice = input("Enter choice (1-4): ")
    
    if choice == "1":
        manual_entry_mode()
        again = input("\nAdd another post? (y/n): ")
        if again.lower() == 'y':
            main()
    elif choice == "2":
        fetch_with_instaloader()
    elif choice == "3":
        process_json_to_posts()
    elif choice == "4":
        print("Goodbye! ☕")
    else:
        print("Invalid choice")
        main()

if __name__ == "__main__":
    # Create required directories
    Path(POSTS_DIR).mkdir(exist_ok=True)
    Path("_data").mkdir(exist_ok=True)
    
    # Check for command line args
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--process":
        process_json_to_posts()
    else:
        main()