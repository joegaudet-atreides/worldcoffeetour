#!/usr/bin/env python3
"""
Fix image import - properly match images to coffee posts from Instagram export
"""

import json
import os
import shutil
from pathlib import Path
from coffee_db import CoffeeDatabase
import hashlib

def is_coffee_related(title):
    """Check if a post is coffee-related"""
    if not title:
        return False
    
    title_lower = title.lower()
    
    # Check for #worldcoffeetour variants
    worldcoffeetour_variants = [
        '#worldcoffeetour', '#worldcoffee', '#worldcofee', '#worldcoffe',
        'worldcoffeetour', 'worldcoffee', 'worldcofee', 'worldcoffe'
    ]
    
    has_worldcoffeetour = any(variant in title_lower for variant in worldcoffeetour_variants)
    
    # Core coffee words
    core_coffee_words = [
        'coffee', 'cafe', 'café', 'espresso', 'latte', 'cappuccino', 
        'americano', 'macchiato', 'cortado', 'mocha', 'cofee', 'coffe'
    ]
    
    has_coffee_mention = any(word in title_lower for word in core_coffee_words)
    
    return has_worldcoffeetour or has_coffee_mention

def copy_and_convert_image(source_path, dest_dir, post_id, index):
    """Copy image and convert HEIC to JPG if needed"""
    source = Path(source_path)
    if not source.exists():
        return None
    
    # Create filename based on post ID and index
    if source.suffix.lower() == '.heic':
        dest_filename = f"post_{post_id}_{index}.jpg"
        dest_path = dest_dir / dest_filename
        
        # Convert HEIC to JPG using system tools if available
        try:
            import subprocess
            # Try using ImageMagick convert
            result = subprocess.run(['convert', str(source), str(dest_path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return f"/assets/images/posts/{dest_filename}"
        except:
            pass
        
        # If conversion fails, try copying as is and let browser handle
        dest_filename = f"post_{post_id}_{index}.heic"
        dest_path = dest_dir / dest_filename
    else:
        dest_filename = f"post_{post_id}_{index}{source.suffix}"
        dest_path = dest_dir / dest_filename
    
    try:
        shutil.copy2(source, dest_path)
        return f"/assets/images/posts/{dest_filename}"
    except Exception as e:
        print(f"Error copying {source} to {dest_path}: {e}")
        return None

def main():
    # Load Instagram posts
    posts_file = Path("instagram-export-folder/your_instagram_activity/media/posts_1.json")
    if not posts_file.exists():
        print("Instagram posts file not found!")
        return
    
    with open(posts_file, 'r', encoding='utf-8') as f:
        instagram_posts = json.load(f)
    
    print(f"Loaded {len(instagram_posts)} Instagram posts")
    
    # Create assets directory
    assets_dir = Path("assets/images/posts")
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    db = CoffeeDatabase()
    
    # Process each Instagram post
    coffee_posts_processed = 0
    images_copied = 0
    
    for i, ig_post in enumerate(instagram_posts):
        title = ig_post.get('title', '')
        
        # Skip non-coffee posts
        if not is_coffee_related(title):
            continue
        
        print(f"Processing coffee post {coffee_posts_processed + 1}: {title[:50]}...")
        
        # Get media from this post
        media_items = ig_post.get('media', [])
        if not media_items:
            continue
        
        # Copy images and build image URLs list
        image_urls = []
        for idx, media in enumerate(media_items):
            media_uri = media.get('uri', '')
            if not media_uri:
                continue
            
            # Full path to the image
            source_path = Path("instagram-export-folder") / media_uri
            
            if source_path.exists():
                # Copy image to assets
                dest_url = copy_and_convert_image(
                    source_path, 
                    assets_dir, 
                    f"ig{i}", 
                    idx
                )
                if dest_url:
                    image_urls.append(dest_url)
                    images_copied += 1
        
        if image_urls:
            # Try to find matching post in database by title similarity
            all_posts = db.get_all_posts()
            best_match = None
            best_score = 0
            
            for post in all_posts:
                post_title = post.get('title', '') or post.get('notes', '')
                if post_title:
                    # Simple similarity based on common words
                    ig_words = set(title.lower().split())
                    post_words = set(post_title.lower().split())
                    
                    if ig_words and post_words:
                        common_words = ig_words.intersection(post_words)
                        score = len(common_words) / max(len(ig_words), len(post_words))
                        
                        if score > best_score and score > 0.3:  # At least 30% similarity
                            best_score = score
                            best_match = post
            
            if best_match:
                # Update the post with images
                post_id = best_match['id']
                images_json = json.dumps(image_urls)
                
                db.cursor.execute(
                    "UPDATE posts SET images = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (images_json, post_id)
                )
                db.conn.commit()
                
                print(f"  → Updated post {post_id} ({best_match.get('cafe_name', 'Unknown')}) with {len(image_urls)} images (similarity: {best_score:.2f})")
            else:
                print(f"  → No matching post found in database for: {title[:50]}")
        
        coffee_posts_processed += 1
        
    
    print(f"\n✅ Processed {coffee_posts_processed} coffee posts")
    print(f"✅ Copied {images_copied} images")
    print(f"✅ Images saved to: {assets_dir}")

if __name__ == "__main__":
    main()