#!/usr/bin/env python3
"""
Fix posts with generic titles by extracting proper cafe names from content or using location info
"""

from coffee_db import CoffeeDatabase
import re

def extract_cafe_name_from_content(notes, title):
    """Try to extract a proper cafe name from the content"""
    if not notes:
        return None
    
    # Look for patterns like "at [Cafe Name]", "visited [Cafe Name]", etc.
    patterns = [
        r'at ([A-Z][^.!?]+?(?:coffee|cafe|roasters?|roastery|espresso|bar))',
        r'(?:visited|found|discovered) ([A-Z][^.!?]+?(?:coffee|cafe|roasters?|roastery|espresso|bar))',
        r'([A-Z][^.!?]+?(?:coffee|cafe|roasters?|roastery|espresso|bar))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, notes, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up common issues
            name = re.sub(r'\s+', ' ', name)  # Multiple spaces
            name = name.split(' on ')[0]  # Remove " on the worldcoffeetour" etc
            name = name.split(' for ')[0]  # Remove " for the first time" etc
            if len(name) > 5 and len(name) < 50:  # Reasonable length
                return name
    
    return None

def fix_generic_titles():
    db = CoffeeDatabase()
    posts = db.get_all_posts()
    
    generic_titles = ['Worldcoffeetour', 'Tinaaluu', 'None', 'worldcoffeetour', 'tinaaluu', None]
    posts_to_fix = [p for p in posts if p.get('cafe_name') in generic_titles or p.get('title') in generic_titles]
    
    print(f"Found {len(posts_to_fix)} posts with generic titles to fix")
    
    fixed_count = 0
    for post in posts_to_fix:
        post_id = post['id']
        current_name = post.get('cafe_name', post.get('title', 'Unknown'))
        notes = post.get('notes', '')
        city = post.get('city', '')
        country = post.get('country', '')
        
        # Try to extract a proper cafe name
        extracted_name = extract_cafe_name_from_content(notes, current_name)
        
        if extracted_name:
            print(f"ID {post_id}: '{current_name}' -> '{extracted_name}'")
            # Update in database
            db.update_post(post_id, {'cafe_name': extracted_name})
            fixed_count += 1
        else:
            # Use location as fallback
            location_name = f"Coffee in {city}" if city else f"Coffee Post {post_id}"
            print(f"ID {post_id}: '{current_name}' -> '{location_name}' (fallback)")
            db.update_post(post_id, {'cafe_name': location_name})
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} posts with generic titles")

if __name__ == "__main__":
    fix_generic_titles()