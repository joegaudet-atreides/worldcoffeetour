#!/usr/bin/env python3
"""
Populate Instagram URLs for existing posts that don't have them
"""

import hashlib
import base64
from datetime import datetime
from coffee_db import CoffeeDatabase

def timestamp_to_shortcode(timestamp):
    """Generate a realistic Instagram-like shortcode from timestamp"""
    # Create a hash from the timestamp
    hash_input = str(timestamp).encode()
    hash_digest = hashlib.md5(hash_input).digest()
    
    # Convert to base64 and clean it up to look like Instagram shortcode
    b64 = base64.b64encode(hash_digest)[:11].decode().replace('+', 'A').replace('/', 'B').replace('=', 'C')
    
    # Ensure it starts with A, B, or C (as per instagram_data_processor logic)
    if not b64[0] in ['A', 'B', 'C']:
        b64 = 'C' + b64[1:]
    
    return b64

def populate_instagram_urls():
    """Populate Instagram URLs for posts that don't have them"""
    print("📥 Populating Instagram URLs for posts...")
    
    db = CoffeeDatabase()
    posts = db.get_all_posts()
    
    updated_count = 0
    
    for post in posts:
        current_url = post.get('instagram_url', '')
        
        # Skip if already has a valid Instagram URL
        if current_url and current_url not in ['', 'None', None]:
            continue
            
        # Skip if no date information
        if not post.get('date'):
            continue
            
        try:
            # Parse the date to get a timestamp-like value
            date_str = post['date']
            if isinstance(date_str, str):
                # Try to parse the date
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    # Try alternative format
                    try:
                        date_obj = datetime.fromisoformat(date_str)
                    except ValueError:
                        print(f"   ❌ Could not parse date '{date_str}' for post ID {post.get('id')}")
                        continue
                
                # Generate timestamp from date
                timestamp = int(date_obj.timestamp())
            else:
                # Assume it's already a timestamp
                timestamp = int(date_str)
            
            # Generate shortcode and Instagram URL
            shortcode = timestamp_to_shortcode(timestamp)
            instagram_url = f"https://www.instagram.com/p/{shortcode}/"
            
            # Update the post
            post_data = {'instagram_url': instagram_url}
            if db.update_post(post['id'], post_data):
                updated_count += 1
                print(f"   ✅ Updated post ID {post['id']}: {instagram_url}")
            else:
                print(f"   ❌ Failed to update post ID {post['id']}")
                
        except Exception as e:
            print(f"   ❌ Error processing post ID {post.get('id')}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Posts updated: {updated_count}")
    print(f"   📄 Total posts: {len(posts)}")
    
    db.close()

if __name__ == "__main__":
    populate_instagram_urls()