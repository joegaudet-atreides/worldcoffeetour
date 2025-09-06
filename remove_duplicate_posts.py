#!/usr/bin/env python3
"""
Remove duplicate posts, keeping the version with images when available
"""

import json
from coffee_db import CoffeeDatabase
from collections import defaultdict

def remove_duplicates():
    """Remove duplicate posts, preferring ones with images"""
    db = CoffeeDatabase()
    posts = db.get_all_posts()
    
    print(f"📊 Total posts before deduplication: {len(posts)}")
    
    # Group posts by date and similar title
    groups = defaultdict(list)
    
    for post in posts:
        # Create a key based on date and first 40 chars of title (normalized)
        date = post.get('date', '')
        title = post.get('title', '').lower().strip()
        # Remove common variations that might cause duplicates
        title = title.replace('iâve', 'i ve').replace('âve', ' ve')
        title = title.replace('doesnât', 'doesn t').replace('âs', ' s')
        title = title.replace('#worldcoffeetour', 'worldcoffeetour')
        title = title.replace('@', '').replace('#', '')
        
        key = f"{date}_{title[:40]}"
        groups[key].append(post)
    
    # Find groups with duplicates
    duplicates_found = 0
    posts_to_remove = []
    
    for key, post_group in groups.items():
        if len(post_group) > 1:
            duplicates_found += 1
            print(f"\n🔍 Found {len(post_group)} duplicates for: {key}")
            
            # Sort by preference: posts with images first, then by ID
            def sort_preference(post):
                has_images = False
                image_count = 0
                
                if post.get('images'):
                    try:
                        images = json.loads(post['images']) if isinstance(post['images'], str) else post['images']
                        if images and len(images) > 0:
                            has_images = True
                            image_count = len(images)
                    except:
                        pass
                
                # Priority: has_images (higher is better), then image_count, then lower ID (older)
                return (-int(has_images), -image_count, post['id'])
            
            sorted_posts = sorted(post_group, key=sort_preference)
            
            # Keep the first (best) post, remove the rest
            keep_post = sorted_posts[0]
            remove_posts = sorted_posts[1:]
            
            keep_images = 0
            if keep_post.get('images'):
                try:
                    images = json.loads(keep_post['images']) if isinstance(keep_post['images'], str) else keep_post['images']
                    keep_images = len(images) if images else 0
                except:
                    pass
            
            print(f"  ✅ KEEPING: ID {keep_post['id']} - {keep_post['title'][:60]}... ({keep_images} images)")
            
            for remove_post in remove_posts:
                remove_images = 0
                if remove_post.get('images'):
                    try:
                        images = json.loads(remove_post['images']) if isinstance(remove_post['images'], str) else remove_post['images']
                        remove_images = len(images) if images else 0
                    except:
                        pass
                
                print(f"  ❌ REMOVING: ID {remove_post['id']} - {remove_post['title'][:60]}... ({remove_images} images)")
                posts_to_remove.append(remove_post['id'])
    
    print(f"\n📊 Duplicate Analysis:")
    print(f"  Groups with duplicates: {duplicates_found}")
    print(f"  Posts to remove: {len(posts_to_remove)}")
    
    if posts_to_remove:
        print(f"\n🗑️  Removing {len(posts_to_remove)} duplicate posts...")
        for post_id in posts_to_remove:
            try:
                db.delete_post(post_id)
            except Exception as e:
                print(f"Error removing post {post_id}: {e}")
    
    # Final stats
    final_posts = db.get_all_posts()
    final_with_images = 0
    
    for post in final_posts:
        if post.get('images'):
            try:
                images = json.loads(post['images']) if isinstance(post['images'], str) else post['images']
                if images and len(images) > 0:
                    final_with_images += 1
            except:
                pass
    
    print(f"\n✅ Deduplication Complete:")
    print(f"  Final total posts: {len(final_posts)}")
    print(f"  Posts with images: {final_with_images}")
    print(f"  Posts without images: {len(final_posts) - final_with_images}")
    
    db.close()

if __name__ == "__main__":
    remove_duplicates()