#!/usr/bin/env python3
"""
Find and remove true duplicate posts based on invariant characteristics
"""

from coffee_db import CoffeeDatabase
import json
from collections import defaultdict
from datetime import datetime

def normalize_image_url(url):
    """Normalize image URL to find duplicates even if URL format changed"""
    if not url:
        return None
    # Extract the key part of Instagram image URLs
    # E.g., /assets/images/posts/202508/536615345_18530599181840_2049318723423062212_n.jpg
    # The important part is the numeric ID like 536615345_18530599181840_2049318723423062212_n
    
    if '/assets/images/posts/' in url:
        # Local image path
        parts = url.split('/')
        if parts:
            filename = parts[-1]
            # Remove extension
            name_part = filename.rsplit('.', 1)[0]
            return name_part
    elif 'instagram.com' in url or 'cdninstagram.com' in url:
        # Instagram URL - extract the filename
        parts = url.split('/')
        for part in parts:
            if '_n.' in part or '_a.' in part:
                return part.rsplit('.', 1)[0]
    
    # For other URLs, use the full URL
    return url

def create_dedup_key(post):
    """Create a deduplication key based on invariant characteristics"""
    keys = []
    
    # Primary key: Image URL (most reliable)
    images = post.get('images', [])
    if images:
        if isinstance(images, str):
            try:
                images = json.loads(images)
            except:
                images = [images]
        if images and images[0]:
            normalized_img = normalize_image_url(images[0])
            if normalized_img:
                keys.append(('image', normalized_img))
    
    # Secondary key: Date + Location (for posts without images)
    date = post.get('date')
    city = post.get('city')
    country = post.get('country')
    
    if date:
        location_key = f"{date}|{city or 'unknown'}|{country or 'unknown'}"
        keys.append(('date_location', location_key))
    
    # Tertiary key: Instagram URL if available
    instagram_url = post.get('instagram_url')
    if instagram_url and 'instagram.com' in instagram_url:
        # Extract the post ID from URL
        parts = instagram_url.split('/')
        for i, part in enumerate(parts):
            if part == 'p' and i + 1 < len(parts):
                keys.append(('instagram_id', parts[i + 1]))
                break
    
    return keys

def find_duplicates():
    """Find all duplicate posts in the database"""
    db = CoffeeDatabase()
    posts = db.get_all_posts()
    
    print(f"📊 Analyzing {len(posts)} posts for duplicates...")
    
    # Group posts by their dedup keys
    image_groups = defaultdict(list)
    date_location_groups = defaultdict(list)
    instagram_groups = defaultdict(list)
    
    for post in posts:
        keys = create_dedup_key(post)
        for key_type, key_value in keys:
            if key_type == 'image':
                image_groups[key_value].append(post)
            elif key_type == 'date_location':
                date_location_groups[key_value].append(post)
            elif key_type == 'instagram_id':
                instagram_groups[key_value].append(post)
    
    # Find duplicate groups
    duplicate_groups = []
    processed_ids = set()
    
    # Check image duplicates (highest confidence)
    for img_key, group in image_groups.items():
        if len(group) > 1:
            group_ids = [p['id'] for p in group]
            if not any(pid in processed_ids for pid in group_ids):
                duplicate_groups.append(('image', group))
                processed_ids.update(group_ids)
    
    # Check Instagram ID duplicates
    for ig_key, group in instagram_groups.items():
        if len(group) > 1:
            group_ids = [p['id'] for p in group]
            if not any(pid in processed_ids for pid in group_ids):
                duplicate_groups.append(('instagram', group))
                processed_ids.update(group_ids)
    
    # Check date+location duplicates (lower confidence, need manual review)
    potential_duplicates = []
    for dl_key, group in date_location_groups.items():
        if len(group) > 1 and 'unknown' not in dl_key.lower():
            group_ids = [p['id'] for p in group]
            if not any(pid in processed_ids for pid in group_ids):
                # These might be different cafes visited on the same day in same city
                potential_duplicates.append(('date_location', group))
    
    return duplicate_groups, potential_duplicates

def select_best_post(posts):
    """Select the best post from a group of duplicates"""
    # Score each post
    scored_posts = []
    
    for post in posts:
        score = 0
        
        # Prefer posts with cafe names
        if post.get('cafe_name') and post['cafe_name'] not in ['Unknown', 'None', 'worldcoffee', 'Worldcoffeetour']:
            score += 10
        
        # Prefer posts with locations
        if post.get('city') and post['city'] != 'Unknown':
            score += 5
        if post.get('country') and post['country'] != 'Unknown':
            score += 5
        
        # Prefer posts with coordinates
        if post.get('latitude') and post.get('longitude'):
            score += 8
        
        # Prefer posts with notes
        if post.get('notes'):
            score += len(post['notes']) // 100  # Longer notes = better
        
        # Prefer posts with ratings
        if post.get('rating'):
            score += 3
        
        # Prefer posts with Instagram URLs
        if post.get('instagram_url'):
            score += 2
        
        # Prefer newer database entries (likely more complete)
        score += post.get('id', 0) / 1000  # Small boost for newer IDs
        
        scored_posts.append((score, post))
    
    # Sort by score (highest first)
    scored_posts.sort(key=lambda x: x[0], reverse=True)
    
    return scored_posts[0][1]  # Return the best post

def remove_duplicates(dry_run=True):
    """Remove duplicate posts from the database"""
    duplicate_groups, potential_duplicates = find_duplicates()
    
    if not duplicate_groups:
        print("✅ No confirmed duplicates found!")
        return
    
    print(f"\n🔍 Found {len(duplicate_groups)} groups of confirmed duplicates")
    
    posts_to_delete = []
    
    for dup_type, group in duplicate_groups:
        print(f"\n{'='*60}")
        print(f"Duplicate group ({dup_type} match):")
        
        # Select the best post to keep
        best_post = select_best_post(group)
        
        for post in group:
            is_best = post['id'] == best_post['id']
            marker = "✅ KEEP" if is_best else "❌ DELETE"
            
            print(f"  {marker} ID {post['id']}: {post.get('cafe_name', 'No name')[:40]}")
            print(f"       Date: {post.get('date')}, City: {post.get('city', 'Unknown')}")
            
            if not is_best:
                posts_to_delete.append(post['id'])
    
    if potential_duplicates:
        print(f"\n⚠️  Found {len(potential_duplicates)} potential duplicate groups (same date+location)")
        print("These might be different cafes visited on the same day - manual review recommended:")
        
        for dup_type, group in potential_duplicates[:5]:  # Show first 5
            print(f"\n  Same date+location group:")
            for post in group:
                print(f"    ID {post['id']}: {post.get('cafe_name', 'No name')[:40]} ({post.get('date')})")
    
    print(f"\n{'='*60}")
    print(f"Summary: {len(posts_to_delete)} posts will be deleted")
    
    if not dry_run and posts_to_delete:
        print("\n🗑️  Deleting duplicate posts...")
        db = CoffeeDatabase()
        for post_id in posts_to_delete:
            db.cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
            print(f"  Deleted post ID {post_id}")
        db.conn.commit()
        print(f"✅ Deleted {len(posts_to_delete)} duplicate posts")
    elif dry_run:
        print("\n⚠️  DRY RUN - No posts were deleted")
        print("Run with --no-dry-run to actually delete duplicates")

if __name__ == "__main__":
    import sys
    dry_run = '--no-dry-run' not in sys.argv
    remove_duplicates(dry_run=dry_run)