#!/usr/bin/env python3
"""
Clean non-coffee posts from database
Removes posts that don't contain coffee-related terms
"""

from coffee_db import CoffeeDatabase
import sys

def clean_non_coffee_posts():
    """Remove posts that don't contain coffee terms"""
    db = CoffeeDatabase()
    
    # Coffee terms to look for
    coffee_terms = [
        'coffee', 'cafe', 'café', 'worldcoffeetour', 'espresso', 'latte', 
        'cappuccino', 'americano', 'macchiato', 'cortado', 'mocha', 
        'cofee', 'coffe', 'barista', 'roast', 'beans', 'brew', 'roastery'
    ]
    
    posts = db.get_all_posts()
    print(f"📊 Current total posts: {len(posts)}")
    
    # Identify non-coffee posts
    non_coffee_posts = []
    coffee_posts = []
    geocoded_removed = 0
    
    for post in posts:
        title = post.get('title', '').lower()
        notes = post.get('notes', '').lower() if post.get('notes') else ''
        text_to_check = title + ' ' + notes
        
        has_coffee = any(term in text_to_check for term in coffee_terms)
        
        if has_coffee:
            coffee_posts.append(post)
        else:
            non_coffee_posts.append(post)
            # Check if we're removing a geocoded post
            if post.get('latitude') and post.get('longitude'):
                geocoded_removed += 1
    
    print(f"☕ Coffee posts to keep: {len(coffee_posts)}")
    print(f"❌ Non-coffee posts to remove: {len(non_coffee_posts)}")
    
    if geocoded_removed > 0:
        print(f"⚠️  WARNING: {geocoded_removed} geocoded posts will be removed!")
        
        # Show geocoded posts that would be removed
        print("\n🌍 Geocoded posts that would be removed:")
        for post in non_coffee_posts:
            if post.get('latitude') and post.get('longitude'):
                print(f"  {post['date']} - {post['title'][:60]}... (lat: {post['latitude']}, lng: {post['longitude']})")
    
    # Remove non-coffee posts
    removed_count = 0
    for post in non_coffee_posts:
        try:
            db.delete_post(post['id'])
            removed_count += 1
        except Exception as e:
            print(f"Error removing post {post['id']}: {e}")
    
    print(f"\n✅ Removed {removed_count} non-coffee posts")
    print(f"📊 Remaining posts: {len(coffee_posts)}")
    
    # Show updated stats
    remaining_posts = db.get_all_posts()
    geocoded = [p for p in remaining_posts if p.get('latitude') and p.get('longitude')]
    print(f"🌍 Geocoded posts remaining: {len(geocoded)}")
    
    db.close()

if __name__ == "__main__":
    clean_non_coffee_posts()