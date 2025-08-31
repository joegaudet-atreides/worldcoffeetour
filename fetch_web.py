#!/usr/bin/env python3
"""
Alternative Instagram fetcher using web scraping
Note: This is for demonstration. Instagram's ToS should be respected.
"""

import json
import re
from datetime import datetime
from pathlib import Path

def create_sample_posts():
    """Create sample posts to demonstrate the site"""
    print("\n☕ Creating sample coffee posts for demonstration")
    print("=" * 60)
    
    # Sample posts data (you can manually add your real posts here)
    sample_posts = [
        {
            "title": "Perfect Pour Over in Tokyo",
            "date": "2024-11-15",
            "city": "Tokyo",
            "country": "Japan",
            "region": "Asia",
            "latitude": 35.6762,
            "longitude": 139.6503,
            "cafe_name": "Blue Bottle Coffee Shibuya",
            "coffee_type": "Pour Over",
            "rating": 5,
            "notes": "Incredible attention to detail. The barista explained each step of the brewing process. Ethiopian single origin with notes of blueberry and chocolate.",
            "image_url": "https://images.unsplash.com/photo-1545665225-b23b99e4d45e?w=800"
        },
        {
            "title": "Morning Espresso in Rome",
            "date": "2024-10-22",
            "city": "Rome",
            "country": "Italy",
            "region": "Europe",
            "latitude": 41.9028,
            "longitude": 12.4964,
            "cafe_name": "Sant'Eustachio Il Caffè",
            "coffee_type": "Espresso",
            "rating": 5,
            "notes": "The legendary Sant'Eustachio. Standing at the bar like a local, downing a perfect espresso with that famous crema. This is coffee culture at its finest.",
            "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800"
        },
        {
            "title": "Flat White Excellence in Melbourne",
            "date": "2024-09-10",
            "city": "Melbourne",
            "country": "Australia",
            "region": "Oceania",
            "latitude": -37.8136,
            "longitude": 144.9631,
            "cafe_name": "Proud Mary",
            "coffee_type": "Flat White",
            "rating": 5,
            "notes": "Melbourne's coffee scene is unmatched. Proud Mary's flat white is silky smooth with perfect microfoam. The beans are roasted on-site.",
            "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800"
        },
        {
            "title": "Cold Brew in Portland",
            "date": "2024-08-05",
            "city": "Portland",
            "country": "USA",
            "region": "Americas",
            "latitude": 45.5152,
            "longitude": -122.6784,
            "cafe_name": "Stumptown Coffee Roasters",
            "coffee_type": "Cold Brew",
            "rating": 4,
            "notes": "The original Portland roaster. Their cold brew is smooth and chocolatey, perfect for a summer day. The industrial-chic vibe is quintessential Portland.",
            "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=800"
        },
        {
            "title": "Café de Olla in Mexico City",
            "date": "2024-07-18",
            "city": "Mexico City",
            "country": "Mexico",
            "region": "Americas",
            "latitude": 19.4326,
            "longitude": -99.1332,
            "cafe_name": "Café de Tacuba",
            "coffee_type": "Café de Olla",
            "rating": 5,
            "notes": "Traditional Mexican coffee with cinnamon and piloncillo. Served in a clay mug at this historic café that's been around since 1912. A unique coffee experience.",
            "image_url": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800"
        },
        {
            "title": "Vietnamese Coffee in Saigon",
            "date": "2024-06-25",
            "city": "Ho Chi Minh City",
            "country": "Vietnam",
            "region": "Asia",
            "latitude": 10.8231,
            "longitude": 106.6297,
            "cafe_name": "The Workshop Coffee",
            "coffee_type": "Vietnamese Iced Coffee",
            "rating": 5,
            "notes": "Strong, sweet, and served over ice. The perfect antidote to Saigon's heat. Watching it slowly drip through the phin filter is meditative.",
            "image_url": "https://images.unsplash.com/photo-1558591710-4bac9de5d604?w=800"
        }
    ]
    
    # Create posts directory
    posts_dir = Path("_coffee_posts")
    posts_dir.mkdir(exist_ok=True)
    
    # Clear existing sample posts
    for old_post in posts_dir.glob("*.md"):
        old_post.unlink()
    
    # Create Jekyll posts
    for post in sample_posts:
        date_str = post["date"]
        slug = re.sub(r'[^\w\s-]', '', post["title"].lower())
        slug = re.sub(r'[-\s]+', '-', slug)[:50]
        
        filename = f"{date_str}-{slug}.md"
        filepath = posts_dir / filename
        
        post_content = f"""---
layout: post
title: "{post['title']}"
date: {date_str}
city: "{post['city']}"
country: "{post['country']}"
region: "{post['region']}"
latitude: {post['latitude']}
longitude: {post['longitude']}
cafe_name: "{post['cafe_name']}"
coffee_type: "{post['coffee_type']}"
rating: {post['rating']}
notes: "{post['notes']}"
image_url: "{post['image_url']}"
instagram_url: "https://www.instagram.com/p/example/"
---"""
        
        filepath.write_text(post_content)
        print(f"  ✓ Created: {filename}")
    
    print(f"\n✅ Created {len(sample_posts)} sample posts!")
    print("\n📝 To add your real Instagram posts:")
    print("1. Edit the posts in _coffee_posts/ with your actual data")
    print("2. Or use the manual entry mode in fetch_instagram_posts.py")
    print("3. Instagram API requires authentication for fetching posts")

def main():
    print("""
☕ World Coffee Tour - Demo Posts Creator
=========================================
""")
    
    create_sample_posts()
    
    print("\n🎉 Done! Next steps:")
    print("1. Run: bundle exec jekyll serve")
    print("2. Visit: http://localhost:4000")
    print("\nYour site is ready with sample posts!")
    print("Replace them with your real Instagram posts when ready.")

if __name__ == "__main__":
    main()