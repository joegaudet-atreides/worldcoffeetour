#!/usr/bin/env python3
"""
Fix incorrect dates on imported posts by reprocessing Instagram data
"""

import json
import re
from datetime import datetime
from pathlib import Path

def fix_post_dates():
    # Load Instagram data
    with open('instagram-export-folder/your_instagram_activity/media/posts_1.json', 'r') as f:
        instagram_data = json.load(f)
    
    # Create a mapping of image filenames to timestamps
    image_to_timestamp = {}
    
    for item in instagram_data:
        if isinstance(item, dict) and 'media' in item:
            for media_item in item['media']:
                uri = media_item.get('uri', '')
                timestamp = media_item.get('creation_timestamp')
                
                if uri and timestamp:
                    # Extract just the filename from the URI
                    filename = Path(uri).name
                    image_to_timestamp[filename] = timestamp
    
    print(f"📍 Found {len(image_to_timestamp)} images with timestamps")
    
    # Now fix all posts in _coffee_posts
    posts_dir = Path("_coffee_posts")
    fixed_count = 0
    
    for post_file in posts_dir.glob("*.md"):
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract the image filename from the post
            image_match = re.search(r'image_url: "/assets/images/posts/\d+/([^"]+)"', content)
            if not image_match:
                continue
            
            image_filename = image_match.group(1)
            
            # Look up the correct timestamp for this image
            if image_filename in image_to_timestamp:
                timestamp = image_to_timestamp[image_filename]
                correct_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                # Update the date in the post
                updated_content = re.sub(
                    r'^date: \d{4}-\d{2}-\d{2}',
                    f'date: {correct_date}',
                    content,
                    flags=re.MULTILINE
                )
                
                # Only write if content changed
                if updated_content != content:
                    with open(post_file, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    print(f"  ✅ Fixed {post_file.name}: {correct_date}")
                    fixed_count += 1
                    
        except Exception as e:
            print(f"  ❌ Error processing {post_file.name}: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} post dates")

if __name__ == "__main__":
    print("🔧 Fixing post dates from Instagram timestamps...")
    fix_post_dates()