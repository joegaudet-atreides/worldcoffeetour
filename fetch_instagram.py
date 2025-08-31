#!/usr/bin/env python3
"""
Instagram World Coffee Tour Posts Fetcher
Fetches posts from @joegaudet with #worldcoffeetour hashtag
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
import instaloader

# Configuration
INSTAGRAM_USERNAME = "joegaudet"
HASHTAG = "worldcoffeetour"
POSTS_DIR = "_coffee_posts"

def fetch_instagram_posts():
    """Fetch posts using Instaloader"""
    print("\n☕ Fetching Instagram posts with #worldcoffeetour from @joegaudet")
    print("=" * 60)
    
    # Initialize Instaloader
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False
    )
    
    # Note: For public profiles, we can try without login first
    print("\nAttempting to fetch public posts...")
    
    try:
        # Get profile
        profile = instaloader.Profile.from_username(L.context, INSTAGRAM_USERNAME)
        
        posts_data = []
        count = 0
        
        print(f"Scanning posts from @{INSTAGRAM_USERNAME} for #{HASHTAG}...")
        
        # Iterate through posts
        for post in profile.get_posts():
            # Check if post has the hashtag
            if post.caption and f"#{HASHTAG}" in post.caption.lower():
                print(f"  ✓ Found post from {post.date_utc.strftime('%Y-%m-%d')}")
                
                # Extract location data if available
                location_data = {}
                if hasattr(post, 'location') and post.location:
                    location_data = {
                        'name': post.location.name,
                        'lat': post.location.lat if hasattr(post.location, 'lat') else None,
                        'lng': post.location.lng if hasattr(post.location, 'lng') else None
                    }
                
                # Parse caption for coffee details
                caption = post.caption or ""
                
                # Clean caption - remove multiple line breaks and extra spaces
                clean_caption = re.sub(r'\n\n+', '\n', caption).strip()
                
                # Try to extract cafe name (looks for @ mentions or quoted names)
                cafe_match = re.search(r'@(\w+)|"([^"]+)"|at\s+([A-Z][^.,\n]+)', caption)
                cafe_name = ""
                if cafe_match:
                    cafe_name = cafe_match.group(1) or cafe_match.group(2) or cafe_match.group(3) or ""
                
                # Extract first meaningful line as title (skip emojis-only lines)
                lines = [line.strip() for line in caption.split('\n') if line.strip()]
                title = ""
                for line in lines:
                    # Skip lines that are just hashtags or emojis
                    if not re.match(r'^[#@\s]*$', re.sub(r'[^\w\s#@]', '', line)):
                        title = line[:50]
                        break
                
                if not title and location_data.get('name'):
                    title = f"Coffee in {location_data['name'].split(',')[0]}"
                elif not title:
                    title = "Coffee Stop"
                
                # Extract full caption as notes (removing hashtags from the end)
                notes = clean_caption
                # Remove hashtag blocks at the end
                notes = re.sub(r'(#\w+\s*)+$', '', notes).strip()
                # Remove mentions at the beginning
                notes = re.sub(r'^(@\w+\s*)+', '', notes).strip()
                
                posts_data.append({
                    'shortcode': post.shortcode,
                    'caption': caption,
                    'date': post.date_utc.isoformat(),
                    'image_url': post.url,
                    'location': location_data,
                    'instagram_url': f"https://www.instagram.com/p/{post.shortcode}/",
                    'title': title,
                    'cafe_name': cafe_name,
                    'notes': notes  # Add the cleaned notes
                })
                
                count += 1
                
                # Limit to prevent rate limiting
                if count >= 50:
                    print(f"\n  Reached limit of {count} posts")
                    break
        
        if count == 0:
            print(f"\n⚠️  No posts found with #{HASHTAG}")
            print("Make sure your posts include the hashtag #worldcoffeetour")
        else:
            # Save to JSON
            os.makedirs('_data', exist_ok=True)
            with open('_data/instagram_posts.json', 'w') as f:
                json.dump(posts_data, f, indent=2)
            
            print(f"\n✅ Found {count} coffee tour posts!")
            print(f"   Data saved to _data/instagram_posts.json")
            
            # Convert to Jekyll posts
            create_jekyll_posts(posts_data)
            
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"❌ Profile @{INSTAGRAM_USERNAME} not found")
    except instaloader.exceptions.LoginRequiredException:
        print("\n⚠️  Login required to fetch more posts")
        print("For more posts, you'll need to login:")
        print("1. Run: instaloader --login YOUR_USERNAME")
        print("2. Then run this script again")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTip: If rate limited, try again in a few minutes")

def create_jekyll_posts(posts_data):
    """Convert Instagram posts to Jekyll markdown files"""
    print("\n📝 Creating Jekyll posts...")
    
    posts_dir = Path(POSTS_DIR)
    posts_dir.mkdir(exist_ok=True)
    
    # Region mapping based on common cities/countries
    region_map = {
        'europe': ['paris', 'london', 'rome', 'berlin', 'amsterdam', 'barcelona', 'vienna', 
                   'prague', 'lisbon', 'madrid', 'athens', 'budapest', 'copenhagen', 'dublin',
                   'france', 'italy', 'spain', 'germany', 'uk', 'greece', 'portugal'],
        'asia': ['tokyo', 'kyoto', 'osaka', 'seoul', 'bangkok', 'singapore', 'hong kong', 
                 'taipei', 'shanghai', 'beijing', 'delhi', 'mumbai', 'japan', 'china', 
                 'korea', 'thailand', 'india', 'vietnam', 'indonesia'],
        'americas': ['new york', 'portland', 'seattle', 'san francisco', 'los angeles', 
                     'chicago', 'boston', 'miami', 'mexico city', 'buenos aires', 'são paulo',
                     'usa', 'united states', 'canada', 'mexico', 'brazil', 'argentina'],
        'oceania': ['melbourne', 'sydney', 'auckland', 'wellington', 'brisbane', 'perth',
                    'australia', 'new zealand'],
        'africa': ['cape town', 'marrakech', 'cairo', 'nairobi', 'johannesburg',
                   'south africa', 'morocco', 'egypt', 'kenya']
    }
    
    def get_region(location_name):
        """Determine region from location name"""
        if not location_name:
            return "World"
        
        location_lower = location_name.lower()
        for region, places in region_map.items():
            if any(place in location_lower for place in places):
                return region.capitalize()
        return "World"
    
    # Clear existing sample posts
    for old_post in posts_dir.glob("*.md"):
        if "2024-" in str(old_post):  # Remove sample posts
            old_post.unlink()
    
    created_count = 0
    for post in posts_data:
        # Parse date
        date = datetime.fromisoformat(post['date'].replace('Z', '+00:00'))
        date_str = date.strftime("%Y-%m-%d")
        
        # Create slug from title
        title = post.get('title', 'Coffee Stop')
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)[:50]
        
        filename = f"{date_str}-{slug}.md"
        filepath = posts_dir / filename
        
        # Extract location details
        location = post.get('location', {})
        location_name = location.get('name', '')
        
        # Parse city and country from location name
        city = "Unknown"
        country = "Unknown"
        if location_name:
            parts = location_name.split(',')
            city = parts[0].strip()
            country = parts[-1].strip() if len(parts) > 1 else parts[0].strip()
        
        # Determine region
        region = get_region(location_name)
        
        # Use the notes we already extracted, or fall back to cleaned caption
        notes = post.get('notes', '')
        if not notes:
            caption = post.get('caption', '')
            # Remove hashtags from the end
            notes = re.sub(r'#\w+\s*', '', caption).strip()
            # Take first paragraph
            notes = notes.split('\n\n')[0]
        
        # Extract coffee type from caption (look for common coffee terms)
        coffee_terms = ['espresso', 'cappuccino', 'latte', 'flat white', 'pour over', 
                       'cold brew', 'americano', 'macchiato', 'cortado', 'v60', 'chemex']
        coffee_type = ""
        caption_lower = caption.lower()
        for term in coffee_terms:
            if term in caption_lower:
                coffee_type = term.title()
                break
        
        # Create post content
        post_content = f"""---
layout: post
title: "{title}"
date: {date_str}
city: "{city}"
country: "{country}"
region: "{region}"
latitude: {location.get('lat') or 'null'}
longitude: {location.get('lng') or 'null'}
cafe_name: "{post.get('cafe_name', '')}"
coffee_type: "{coffee_type}"
rating: 
notes: "{notes}"
image_url: "{post.get('image_url', '')}"
instagram_url: "{post.get('instagram_url', '')}"
---"""
        
        filepath.write_text(post_content)
        created_count += 1
        print(f"  ✓ Created: {filename}")
    
    print(f"\n✅ Created {created_count} Jekyll posts in {POSTS_DIR}/")
    return created_count

def main():
    print("""
☕ World Coffee Tour - Instagram Fetcher
========================================
Fetching posts from @joegaudet with #worldcoffeetour
""")
    
    # Fetch posts
    fetch_instagram_posts()
    
    print("\n🎉 Done! Next steps:")
    print("1. Review the posts in _coffee_posts/")
    print("2. Run: bundle exec jekyll serve")
    print("3. Visit: http://localhost:4000")
    print("\nTo update posts later, just run this script again!")

if __name__ == "__main__":
    main()