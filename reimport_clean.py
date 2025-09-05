#!/usr/bin/env python3
"""
Clean re-import of Instagram posts with strict coffee filtering.
This script will:
1. Clear the existing database
2. Re-import only posts that explicitly mention coffee or have #worldcoffeetour
"""

import sys
import os
from pathlib import Path
from coffee_db import CoffeeDatabase

def clear_database():
    """Clear all posts from the database"""
    db = CoffeeDatabase()
    
    # Get current count
    current_count = db.get_post_count()
    print(f"Current database has {current_count} posts")
    
    # Clear all posts
    db.cursor.execute("DELETE FROM posts")
    db.conn.commit()
    
    # Verify empty
    new_count = db.get_post_count()
    print(f"Database cleared. Now has {new_count} posts")
    
    db.close()
    return current_count

def main():
    print("=" * 60)
    print("CLEAN RE-IMPORT WITH STRICT COFFEE FILTERING")
    print("=" * 60)
    print("\nThis will:")
    print("1. Clear the existing database")
    print("2. Import ONLY posts with coffee mentions or #worldcoffeetour")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Step 1: Clear database
    print("\n📄 Step 1: Clearing database...")
    old_count = clear_database()
    
    # Step 2: Re-import with strict filtering
    print("\n📥 Step 2: Re-importing with strict filtering...")
    from import_instagram_full import InstagramImporter
    
    importer = InstagramImporter()
    success = importer.import_posts()
    
    if success:
        print("\n✅ Re-import complete!")
        print(f"   Previous posts: {old_count}")
        importer.show_stats()
        
        # Step 3: Regenerate Jekyll posts
        print("\n🔄 Step 3: Regenerating Jekyll posts...")
        importer.regenerate_jekyll_posts()
    else:
        print("\n❌ Re-import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()