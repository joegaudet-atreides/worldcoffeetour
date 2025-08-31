#!/usr/bin/env python3
"""
Interactive Coffee Post Creator
Add your Instagram coffee posts manually with this helper script
"""

import re
import json
from datetime import datetime
from pathlib import Path

def get_region(location):
    """Determine region from location"""
    location_lower = location.lower()
    
    regions = {
        'Europe': ['france', 'italy', 'spain', 'germany', 'uk', 'greece', 'portugal', 'netherlands', 'belgium', 'switzerland', 'austria', 'czech', 'hungary', 'poland', 'denmark', 'sweden', 'norway', 'ireland', 'paris', 'london', 'rome', 'berlin', 'amsterdam', 'barcelona', 'vienna', 'prague', 'lisbon', 'madrid', 'athens', 'budapest', 'copenhagen', 'dublin'],
        'Asia': ['japan', 'china', 'korea', 'thailand', 'vietnam', 'indonesia', 'singapore', 'malaysia', 'philippines', 'india', 'tokyo', 'kyoto', 'osaka', 'seoul', 'bangkok', 'hong kong', 'taipei', 'shanghai', 'beijing', 'delhi', 'mumbai', 'saigon', 'ho chi minh'],
        'Americas': ['usa', 'united states', 'canada', 'mexico', 'brazil', 'argentina', 'colombia', 'peru', 'chile', 'new york', 'portland', 'seattle', 'san francisco', 'los angeles', 'chicago', 'boston', 'miami', 'mexico city', 'buenos aires', 'são paulo', 'rio'],
        'Oceania': ['australia', 'new zealand', 'melbourne', 'sydney', 'auckland', 'wellington', 'brisbane', 'perth'],
        'Africa': ['south africa', 'morocco', 'egypt', 'kenya', 'ethiopia', 'tanzania', 'cape town', 'marrakech', 'cairo', 'nairobi', 'johannesburg']
    }
    
    for region, locations in regions.items():
        if any(loc in location_lower for loc in locations):
            return region
    return 'World'

def create_post():
    print("\n☕ Add a Coffee Post")
    print("=" * 40)
    
    # Basic info
    print("\n📍 LOCATION DETAILS:")
    city = input("City: ").strip()
    country = input("Country: ").strip()
    
    # Try to get coordinates
    print("\n🗺️ COORDINATES (optional - press Enter to skip):")
    print("Tip: Right-click on Google Maps and select 'What's here?' to get coordinates")
    lat = input("Latitude (e.g., 48.8566): ").strip()
    lng = input("Longitude (e.g., 2.3522): ").strip()
    
    # Coffee details
    print("\n☕ COFFEE DETAILS:")
    cafe_name = input("Café name: ").strip()
    coffee_type = input("Coffee type (Espresso, Pour Over, etc.): ").strip()
    
    # Rating
    while True:
        rating = input("Rating (1-5): ").strip()
        if rating in ['1', '2', '3', '4', '5']:
            rating = int(rating)
            break
        elif rating == '':
            rating = None
            break
        print("Please enter a number 1-5, or press Enter to skip")
    
    # Post content
    print("\n📝 POST CONTENT:")
    print("Paste your Instagram caption (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == '' and lines and lines[-1] == '':
            break
        lines.append(line)
    
    caption = '\n'.join(lines).strip()
    
    # Extract title from caption or create one
    title_lines = [line.strip() for line in caption.split('\n') if line.strip() and not line.strip().startswith('#')]
    title = title_lines[0][:50] if title_lines else f"Coffee in {city}"
    
    # Clean notes (remove hashtags)
    notes = re.sub(r'#\w+\s*', '', caption).strip()
    notes = re.sub(r'\n\n+', '\n', notes).strip()
    
    # Date
    print("\n📅 DATE:")
    date_str = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Image URL
    print("\n🖼️ IMAGE:")
    print("Options:")
    print("1. Paste an image URL")
    print("2. Use a placeholder")
    image_choice = input("Choice (1 or 2): ").strip()
    
    if image_choice == '1':
        image_url = input("Image URL: ").strip()
    else:
        # Placeholder images
        placeholders = [
            "https://images.unsplash.com/photo-1545665225-b23b99e4d45e?w=800",
            "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800",
            "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800",
            "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=800",
            "https://images.unsplash.com/photo-1558591710-4bac9de5d604?w=800",
        ]
        import random
        image_url = random.choice(placeholders)
    
    # Instagram URL
    instagram_url = input("\nInstagram post URL (optional): ").strip() or "https://www.instagram.com/p/example/"
    
    # Determine region
    region = get_region(f"{city} {country}")
    
    # Create filename
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)[:30]
    filename = f"{date_str}-{slug}.md"
    
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
rating: {rating if rating else ''}
notes: "{notes}"
image_url: "{image_url}"
instagram_url: "{instagram_url}"
---"""
    
    # Save post
    posts_dir = Path("_coffee_posts")
    posts_dir.mkdir(exist_ok=True)
    filepath = posts_dir / filename
    
    print("\n📄 Preview:")
    print("-" * 40)
    print(post_content)
    print("-" * 40)
    
    confirm = input("\n💾 Save this post? (y/n): ").strip().lower()
    if confirm == 'y':
        filepath.write_text(post_content)
        print(f"✅ Saved to {filepath}")
        return True
    else:
        print("❌ Post not saved")
        return False

def batch_add():
    """Add multiple posts"""
    print("\n☕ Batch Add Coffee Posts")
    print("=" * 40)
    print("This will help you add multiple posts quickly.")
    
    count = 0
    while True:
        if create_post():
            count += 1
        
        another = input("\n➕ Add another post? (y/n): ").strip().lower()
        if another != 'y':
            break
    
    print(f"\n✅ Added {count} coffee posts!")

def main():
    print("""
☕ World Coffee Tour - Post Manager
===================================

Choose an option:
1. Add a single coffee post
2. Batch add multiple posts
3. List existing posts
4. Exit
""")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        create_post()
        print("\n🔄 Run 'bundle exec jekyll build' to update the site")
    elif choice == '2':
        batch_add()
        print("\n🔄 Run 'bundle exec jekyll build' to update the site")
    elif choice == '3':
        posts_dir = Path("_coffee_posts")
        if posts_dir.exists():
            posts = sorted(posts_dir.glob("*.md"), reverse=True)
            print(f"\n📝 Found {len(posts)} posts:")
            for post in posts[:10]:  # Show last 10
                print(f"  - {post.name}")
            if len(posts) > 10:
                print(f"  ... and {len(posts) - 10} more")
        else:
            print("\n❌ No posts found")
    elif choice == '4':
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice")

if __name__ == "__main__":
    main()