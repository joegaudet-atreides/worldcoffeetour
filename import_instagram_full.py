#!/usr/bin/env python3
"""
Comprehensive Instagram import script that restores all 104 posts with multiple image support.
This script processes the original Instagram export and imports everything into SQLite database.
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import hashlib
import re
from coffee_db import CoffeeDatabase

class InstagramImporter:
    def __init__(self):
        self.db = CoffeeDatabase()
        self.imported_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        
    def find_export_files(self):
        """Find Instagram export files in common locations"""
        possible_paths = [
            Path('.'),  # Current directory
            Path('export'),
            Path('instagram-export'),
            Path('instagram-export-folder'),
            Path('instagram-export-folder/your_instagram_activity'),
            Path('instagram-export-folder/your_instagram_activity/media'),
            Path('data'),
            Path('../export'),
        ]
        
        export_files = {
            'posts': None,
            'media': None,
            'directory': None
        }
        
        for base_path in possible_paths:
            if not base_path.exists():
                continue
                
            # Look for posts.json or posts_1.json
            for posts_file in ['posts.json', 'posts_1.json', 'content/posts_1.json']:
                posts_path = base_path / posts_file
                if posts_path.exists():
                    export_files['posts'] = posts_path
                    export_files['directory'] = base_path
                    break
                    
            # Look for media.json
            for media_file in ['media.json', 'media_1.json', 'content/media_1.json']:
                media_path = base_path / media_file
                if media_path.exists():
                    export_files['media'] = media_path
                    break
                    
            if export_files['posts']:
                break
        
        return export_files
    
    def load_instagram_data(self, export_files):
        """Load Instagram posts from export files"""
        posts_data = []
        media_data = {}
        
        # Load posts
        if export_files['posts']:
            print(f"Loading posts from: {export_files['posts']}")
            with open(export_files['posts'], 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    posts_data = data
                elif isinstance(data, dict) and 'posts' in data:
                    posts_data = data['posts']
                else:
                    print("Unknown posts file format")
                    return [], {}
        
        # Load media
        if export_files['media']:
            print(f"Loading media from: {export_files['media']}")
            with open(export_files['media'], 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if 'uri' in item:
                            media_data[item['uri']] = item
                elif isinstance(data, dict) and 'photos' in data:
                    for item in data['photos']:
                        if 'uri' in item:
                            media_data[item['uri']] = item
        
        print(f"Loaded {len(posts_data)} posts and {len(media_data)} media items")
        return posts_data, media_data
    
    def extract_location_from_text(self, text):
        """Extract location information from post text"""
        if not text:
            return None, None, None
            
        # Common patterns for coffee shops
        coffee_patterns = [
            r'@([a-zA-Z0-9._]+)',  # Instagram mentions
            r'#([a-zA-Z0-9_]+)',   # Hashtags
            r'at ([^,\n]+)',       # "at Location"
            r'in ([^,\n]+)',       # "in City"
        ]
        
        # Try to extract cafe name from text
        cafe_name = None
        for pattern in coffee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                if len(potential_name) > 3:  # Avoid too short matches
                    cafe_name = potential_name.replace('_', ' ').title()
                    break
        
        return cafe_name, None, None  # City and country would need geocoding
    
    def is_coffee_related(self, title):
        """Check if a post is coffee-related - STRICT filtering"""
        if not title:
            return False
            
        title_lower = title.lower()
        
        # Primary requirement: Must have #worldcoffeetour or mention coffee explicitly
        # Check for #worldcoffeetour variants (including misspellings)
        worldcoffeetour_variants = [
            '#worldcoffeetour', '#worldcoffee', '#worldcofee', '#worldcoffe',
            'worldcoffeetour', 'worldcoffee', 'worldcofee', 'worldcoffe'
        ]
        
        has_worldcoffeetour = any(variant in title_lower for variant in worldcoffeetour_variants)
        
        # Core coffee words that MUST be present if worldcoffeetour isn't
        core_coffee_words = [
            'coffee', 'cafe', 'café', 'espresso', 'latte', 'cappuccino', 
            'americano', 'macchiato', 'cortado', 'mocha', 'cofee', 'coffe'  # Include misspellings
        ]
        
        has_coffee_mention = any(word in title_lower for word in core_coffee_words)
        
        # Only include if it has worldcoffeetour hashtag OR explicitly mentions coffee
        return has_worldcoffeetour or has_coffee_mention

    def process_post(self, post, media_data, base_path):
        """Process a single Instagram post"""
        try:
            # Extract basic info
            creation_timestamp = post.get('creation_timestamp', 0)
            post_date = datetime.fromtimestamp(creation_timestamp).strftime('%Y-%m-%d') if creation_timestamp else None
            
            # Get post data
            title = post.get('title', '')
            if not title and 'data' in post and post['data']:
                # Try to get title from first data item
                first_data = post['data'][0] if isinstance(post['data'], list) else post['data']
                title = first_data.get('title', '')
            
            # Skip non-coffee posts
            if not self.is_coffee_related(title):
                return None
            
            # Extract images
            images = []
            attachments = post.get('attachments', [])
            
            for attachment in attachments:
                if 'data' in attachment:
                    for data_item in attachment['data']:
                        if 'media' in data_item:
                            media_info = data_item['media']
                            if 'uri' in media_info:
                                # Convert relative path to full path
                                media_path = base_path / media_info['uri']
                                if media_path.exists():
                                    # Use relative path from project root
                                    relative_path = str(media_path.relative_to(Path.cwd()))
                                    images.append(f"/{relative_path}")
                                else:
                                    # Try to find the file in media directory
                                    filename = Path(media_info['uri']).name
                                    for media_dir in ['media', 'photos', 'content']:
                                        search_path = base_path / media_dir
                                        if search_path.exists():
                                            for img_file in search_path.rglob(filename):
                                                relative_path = str(img_file.relative_to(Path.cwd()))
                                                images.append(f"/{relative_path}")
                                                break
            
            # Also check direct media references
            if 'media' in post:
                media_list = post['media'] if isinstance(post['media'], list) else [post['media']]
                for media_item in media_list:
                    if 'uri' in media_item:
                        media_path = base_path / media_item['uri']
                        if media_path.exists():
                            relative_path = str(media_path.relative_to(Path.cwd()))
                            images.append(f"/{relative_path}")
            
            # Remove duplicates while preserving order
            images = list(dict.fromkeys(images))
            
            # Extract location info from title/text
            cafe_name, city, country = self.extract_location_from_text(title)
            
            # Build post data
            post_data = {
                'title': title[:200] if title else f"Instagram post from {post_date}",
                'date': post_date,
                'cafe_name': cafe_name,
                'city': city or 'Unknown',
                'country': country or 'Unknown', 
                'continent': 'Unknown',  # Would need geocoding
                'latitude': None,
                'longitude': None,
                'rating': None,
                'notes': title if len(title) > 50 else None,  # Store full text as notes if long
                'images': json.dumps(images) if images else json.dumps([]),
                'instagram_url': None,  # Could extract if available
                'published': True,  # Default to published
                'metadata': json.dumps({
                    'instagram_timestamp': creation_timestamp,
                    'instagram_id': post.get('id'),
                    'original_attachments': len(attachments)
                })
            }
            
            # Generate hash for deduplication
            hash_data = {
                'title': post_data['title'],
                'date': post_data['date'],
                'notes': post_data['notes'],
                'images': images[0] if images else None
            }
            post_hash = self.db.generate_hash(hash_data)
            post_data['hash'] = post_hash
            
            return post_data
            
        except Exception as e:
            print(f"Error processing post: {e}")
            return None
    
    def import_posts(self):
        """Import all Instagram posts"""
        print("🔍 Searching for Instagram export files...")
        
        export_files = self.find_export_files()
        
        if not export_files['posts']:
            print("❌ No Instagram export files found!")
            print("Expected files: posts.json, posts_1.json, or content/posts_1.json")
            print("Please ensure your Instagram export is in the current directory or a subdirectory.")
            return False
        
        print(f"📁 Found export directory: {export_files['directory']}")
        
        # Load Instagram data
        posts_data, media_data = self.load_instagram_data(export_files)
        
        if not posts_data:
            print("❌ No posts found in export files!")
            return False
        
        print(f"📸 Processing {len(posts_data)} Instagram posts...")
        
        # Process each post
        for i, post in enumerate(posts_data, 1):
            print(f"Processing post {i}/{len(posts_data)}", end='\\r')
            
            post_data = self.process_post(post, media_data, export_files['directory'])
            if not post_data:
                self.skipped_count += 1
                continue
            
            # Try to insert or update
            try:
                existing_post = self.db.get_post_by_hash(post_data['hash'])
                if existing_post:
                    # Update existing post
                    self.db.update_post(existing_post['id'], post_data)
                    self.updated_count += 1
                else:
                    # Insert new post
                    self.db.insert_post(post_data)
                    self.imported_count += 1
                    
            except Exception as e:
                print(f"\\nError saving post {i}: {e}")
                self.skipped_count += 1
        
        print(f"\\n✅ Import complete!")
        print(f"   📥 Imported: {self.imported_count} new posts")
        print(f"   🔄 Updated: {self.updated_count} existing posts") 
        print(f"   ⚠️  Skipped: {self.skipped_count} posts")
        print(f"   📊 Total in database: {self.db.get_post_count()}")
        
        return True
    
    def show_stats(self):
        """Show database statistics"""
        print("\\n📊 Database Statistics:")
        stats = self.db.get_statistics()
        
        total = stats.get('total_posts', 0)
        published = stats.get('published_posts', 0)
        unpublished = total - published
        
        print(f"   Total posts: {total}")
        print(f"   Published: {published}")
        print(f"   Unpublished: {unpublished}")
        print(f"   With images: {stats.get('posts_with_images', 0)}")
        print(f"   With location: {stats.get('posts_with_location', 0)}")
        print(f"   With cafe names: {stats.get('posts_with_cafe_names', 0)}")
        
        # Show continent breakdown
        continents = self.db.get_continents()
        if continents:
            print("\\n🌍 By Continent:")
            for continent in continents:
                count = self.db.get_posts_by_continent(continent)
                print(f"   {continent}: {len(count)}")
    
    def regenerate_jekyll_posts(self):
        """Regenerate all Jekyll posts from database"""
        print("\\n🔄 Regenerating Jekyll posts from database...")
        
        try:
            from regenerate_posts import regenerate_all_posts
            regenerate_all_posts()
            print("✅ Jekyll posts regenerated successfully!")
        except ImportError:
            print("⚠️  regenerate_posts.py not found, skipping Jekyll regeneration")
        except Exception as e:
            print(f"❌ Error regenerating Jekyll posts: {e}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Instagram Import Script for World Coffee Tour

Usage:
    python3 import_instagram_full.py [--stats-only] [--no-jekyll]

Options:
    --stats-only    Only show database statistics, don't import
    --no-jekyll     Don't regenerate Jekyll posts after import
    --help          Show this help message

This script will:
1. Search for Instagram export files (posts.json, media.json)
2. Import all posts with multiple image support
3. Handle deduplication using content hashes
4. Support idempotent re-runs (safe to run multiple times)
5. Regenerate Jekyll posts from the database

Expected Instagram export structure:
- posts.json or posts_1.json (post data)
- media.json or media_1.json (media metadata)  
- photos/ or media/ directory (actual image files)
        """)
        return
    
    importer = InstagramImporter()
    
    # Check if only showing stats
    if len(sys.argv) > 1 and '--stats-only' in sys.argv:
        importer.show_stats()
        return
    
    # Import posts
    success = importer.import_posts()
    
    if success:
        importer.show_stats()
        
        # Regenerate Jekyll posts unless disabled
        if '--no-jekyll' not in sys.argv:
            importer.regenerate_jekyll_posts()
    else:
        print("❌ Import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()