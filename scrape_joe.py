#!/usr/bin/env python3
"""
Quick Instagram scraper for @joegaudet with #worldcoffeetour
"""

import requests
import json
import re
from datetime import datetime
from pathlib import Path

def scrape_joegaudet_instagram():
    """Scrape @joegaudet's Instagram for #worldcoffeetour posts"""
    print("☕ Scraping @joegaudet for #worldcoffeetour posts...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
    })
    
    try:
        # Get profile page
        url = "https://www.instagram.com/joegaudet/"
        print(f"🔍 Fetching {url}")
        response = session.get(url)
        response.raise_for_status()
        
        # Extract post data
        posts = extract_posts_from_html(response.text)
        
        # Filter for coffee posts
        coffee_posts = [post for post in posts if '#worldcoffeetour' in post.get('caption', '').lower()]
        
        if coffee_posts:
            print(f"✅ Found {len(coffee_posts)} coffee posts!")
            
            # Show preview
            for i, post in enumerate(coffee_posts[:3], 1):
                print(f"\n{i}. {post['title']}")
                if post.get('location', {}).get('name'):
                    print(f"   📍 {post['location']['name']}")
                if post.get('notes'):
                    print(f"   📝 {post['notes'][:80]}...")
            
            if len(coffee_posts) > 3:
                print(f"\n... and {len(coffee_posts) - 3} more")
            
            # Save posts
            created = save_posts_to_jekyll(coffee_posts)
            print(f"\n💾 Created {created} Jekyll posts!")
            print("🔄 Check http://localhost:4000 to see your posts")
            
        else:
            print("❌ No posts found with #worldcoffeetour")
            print("Make sure your profile is public and has posts with that hashtag")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nThis might happen because:")
        print("- Instagram is blocking requests")
        print("- Profile is private")
        print("- Network connectivity issues")
        print("\nTry using the manual post creator instead:")
        print("python3 add_coffee_post.py")

def extract_posts_from_html(html):
    """Extract posts from Instagram HTML"""
    posts = []
    
    # Look for shared data
    shared_data_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html)
    if shared_data_match:
        try:
            data = json.loads(shared_data_match.group(1))
            
            # Navigate Instagram's data structure
            profile_page = data.get('entry_data', {}).get('ProfilePage', [])
            if profile_page:
                user_data = profile_page[0].get('graphql', {}).get('user', {})
                media_edges = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                
                for edge in media_edges:
                    node = edge.get('node', {})
                    caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                    caption = caption_edges[0]['node']['text'] if caption_edges else ""
                    
                    post_data = format_post_data(node, caption)
                    if post_data:
                        posts.append(post_data)
                        
        except json.JSONDecodeError:
            print("⚠️  Could not parse Instagram data")
    
    # Fallback: look for basic post data in HTML
    if not posts:
        shortcode_matches = re.findall(r'"shortcode":"([^"]+)"', html)
        image_matches = re.findall(r'"display_url":"([^"]+)"', html)
        
        for i, shortcode in enumerate(shortcode_matches[:10]):  # Limit to first 10
            image_url = image_matches[i] if i < len(image_matches) else ""
            posts.append({
                'shortcode': shortcode,
                'title': 'Coffee Stop',
                'caption': '',
                'notes': '',
                'date': datetime.now().isoformat(),
                'image_url': image_url,
                'location': {},
                'instagram_url': f"https://www.instagram.com/p/{shortcode}/"
            })
    
    return posts

def format_post_data(node, caption):
    """Format Instagram post data"""
    try:
        shortcode = node.get('shortcode', '')
        timestamp = node.get('taken_at_timestamp', 0)
        image_url = node.get('display_url', '')
        
        # Location
        location_data = {}
        if node.get('location'):
            loc = node['location']
            location_data = {
                'name': loc.get('name', ''),
                'lat': loc.get('lat'),
                'lng': loc.get('lng')
            }
        
        # Title from caption
        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        title = ""
        for line in lines:
            if not line.startswith('#') and not line.startswith('@') and len(line) > 10:
                title = line[:60]
                break
        
        if not title and location_data.get('name'):
            title = f"Coffee in {location_data['name'].split(',')[0]}"
        elif not title:
            title = "Coffee Stop"
        
        # Clean notes
        notes = re.sub(r'#\w+\s*', '', caption).strip()
        notes = re.sub(r'@\w+\s*', '', notes).strip()
        notes = re.sub(r'\n\n+', '\n', notes).strip()
        
        return {
            'shortcode': shortcode,
            'title': title,
            'caption': caption,
            'notes': notes,
            'date': datetime.fromtimestamp(timestamp).isoformat() if timestamp else datetime.now().isoformat(),
            'image_url': image_url,
            'location': location_data,
            'instagram_url': f"https://www.instagram.com/p/{shortcode}/"
        }
        
    except Exception as e:
        print(f"Error formatting post: {e}")
        return None

def save_posts_to_jekyll(posts):
    """Save posts as Jekyll markdown files"""
    posts_dir = Path("_coffee_posts")
    posts_dir.mkdir(exist_ok=True)
    
    # Remove old sample posts
    for old_post in posts_dir.glob("2024-*.md"):
        old_post.unlink()
    
    count = 0
    for post in posts:
        try:
            date_str = post['date'][:10]
            title = post['title']
            slug = re.sub(r'[^\w\s-]', '', title.lower())
            slug = re.sub(r'[-\s]+', '-', slug)[:30]
            
            filename = f"{date_str}-{slug}.md"
            filepath = posts_dir / filename
            
            # Parse location
            location = post.get('location', {})
            city = "Unknown"
            country = "Unknown"
            region = "World"
            
            if location.get('name'):
                parts = location['name'].split(',')
                city = parts[0].strip()
                if len(parts) > 1:
                    country = parts[-1].strip()
                
                # Determine region
                location_lower = location['name'].lower()
                if any(place in location_lower for place in ['japan', 'tokyo', 'kyoto', 'asia', 'china', 'korea', 'thailand']):
                    region = "Asia"
                elif any(place in location_lower for place in ['france', 'italy', 'spain', 'europe', 'paris', 'rome', 'london']):
                    region = "Europe"
                elif any(place in location_lower for place in ['usa', 'america', 'canada', 'mexico', 'brazil', 'new york', 'portland']):
                    region = "Americas"
                elif any(place in location_lower for place in ['australia', 'new zealand', 'melbourne', 'sydney']):
                    region = "Oceania"
                elif any(place in location_lower for place in ['africa', 'south africa', 'morocco', 'cape town']):
                    region = "Africa"
            
            post_content = f"""---
layout: post
title: "{title}"
date: {date_str}
city: "{city}"
country: "{country}"
region: "{region}"
latitude: {location.get('lat', 'null')}
longitude: {location.get('lng', 'null')}
cafe_name: ""
coffee_type: ""
rating: 
notes: "{post['notes']}"
image_url: "{post['image_url']}"
instagram_url: "{post['instagram_url']}"
---"""
            
            filepath.write_text(post_content)
            count += 1
            print(f"  ✅ Created: {filename}")
            
        except Exception as e:
            print(f"Error creating post: {e}")
    
    return count

if __name__ == "__main__":
    print("""
☕ Quick Instagram Scraper for @joegaudet
=========================================
Fetching posts with #worldcoffeetour automatically...
""")
    scrape_joegaudet_instagram()