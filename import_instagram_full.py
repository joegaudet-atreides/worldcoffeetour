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
        
        # Load posts - the main posts_1.json contains both post data AND media URIs
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
                    return []
        
        print(f"Loaded {len(posts_data)} posts from Instagram export")
        return posts_data
    
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
        """Check if a post is coffee-related - SIMPLE filtering for coffee and worldcoffeetour only"""
        if not title:
            return False
            
        title_lower = title.lower()
        
        # Simple requirement: Must contain "coffee" or "worldcoffeetour"
        coffee_terms = [
            'coffee', 'cafe', 'café', 'worldcoffeetour', 'espresso', 'latte', 'cappuccino', 
            'americano', 'macchiato', 'cortado', 'mocha', 'cofee', 'coffe',
            'barista', 'roast', 'beans', 'brew', 'roastery', 'coffeeshop'
        ]
        
        return any(term in title_lower for term in coffee_terms)

    def process_post(self, post, base_path):
        """Process a single Instagram post with correct structure handling"""
        try:
            # Extract basic info from the correct Instagram structure
            creation_timestamp = post.get('creation_timestamp', 0)
            post_date = datetime.fromtimestamp(creation_timestamp).strftime('%Y-%m-%d') if creation_timestamp else None
            
            # Get post title directly from post level (not from individual media items)
            title = post.get('title', '').strip()
            
            # Skip non-coffee posts
            if not self.is_coffee_related(title):
                return None
            
            # Extract images from media array
            images = []
            media_list = post.get('media', [])
            
            print(f"  Processing post with {len(media_list)} media items: {title[:50]}...")
            
            for media_item in media_list:
                if isinstance(media_item, dict) and 'uri' in media_item:
                    media_uri = media_item['uri']
                    
                    # Convert media URI to assets path
                    # media/posts/202508/image.jpg -> /assets/images/posts/202508/image.jpg
                    if media_uri.startswith('media/posts/'):
                        assets_path = media_uri.replace('media/posts/', 'assets/images/posts/')
                        full_assets_path = Path(assets_path)
                        if full_assets_path.exists():
                            images.append(f"/{assets_path}")
                        else:
                            # Try to find the file in the assets directory
                            filename = Path(media_uri).name
                            for img_file in Path('assets/images/posts').rglob(filename):
                                relative_path = str(img_file.relative_to(Path.cwd()))
                                images.append(f"/{relative_path}")
                                break
                    else:
                        # Handle alternative URI formats or direct paths
                        # Try to find file in the original export location first
                        original_path = base_path / media_uri
                        if original_path.exists():
                            # Copy to assets directory if needed
                            filename = Path(media_uri).name
                            # Extract year-month from path (e.g., 202508)
                            path_parts = Path(media_uri).parts
                            year_month = None
                            for part in path_parts:
                                if part.isdigit() and len(part) == 6:  # YYYYMM format
                                    year_month = part
                                    break
                            
                            if year_month:
                                assets_dir = Path(f'assets/images/posts/{year_month}')
                                assets_dir.mkdir(parents=True, exist_ok=True)
                                assets_path = assets_dir / filename
                                
                                # Copy file if it doesn't exist in assets
                                if not assets_path.exists():
                                    import shutil
                                    shutil.copy2(original_path, assets_path)
                                    print(f"    Copied {filename} to {assets_path}")
                                
                                images.append(f"/{str(assets_path)}")
                            else:
                                # Fallback - use relative path from current location
                                relative_path = str(original_path.relative_to(Path.cwd()))
                                images.append(f"/{relative_path}")
                        else:
                            # File not found - try searching for it
                            filename = Path(media_uri).name
                            found = False
                            for search_dir in [Path('assets/images/posts'), Path('instagram-export-folder')]:
                                if search_dir.exists():
                                    for img_file in search_dir.rglob(filename):
                                        relative_path = str(img_file.relative_to(Path.cwd()))
                                        images.append(f"/{relative_path}")
                                        found = True
                                        break
                                if found:
                                    break
                            
                            if not found:
                                print(f"    WARNING: Image not found: {media_uri}")
            
            # Remove duplicates while preserving order
            images = list(dict.fromkeys(images))
            
            print(f"  Found {len(images)} images for post")
            
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
                    'instagram_media_count': len(media_list),
                    'original_media_uris': [m.get('uri') for m in media_list if isinstance(m, dict)]
                })
            }
            
            # Generate hash for deduplication
            hash_data = {
                'title': post_data['title'] or '',
                'date': post_data['date'] or '',
                'notes': post_data['notes'] or '',
                'images': images  # Pass the full images list, not just first one
            }
            post_hash = self.db.generate_hash(hash_data)
            post_data['hash'] = post_hash
            
            return post_data
            
        except Exception as e:
            print(f"Error processing post: {e}")
            import traceback
            traceback.print_exc()
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
        posts_data = self.load_instagram_data(export_files)
        
        if not posts_data:
            print("❌ No posts found in export files!")
            return False
        
        print(f"📸 Processing {len(posts_data)} Instagram posts...")
        
        # Process each post
        for i, post in enumerate(posts_data, 1):
            print(f"Processing post {i}/{len(posts_data)}")
            
            post_data = self.process_post(post, export_files['directory'])
            if not post_data:
                self.skipped_count += 1
                continue
            
            # Try to insert or update (IDEMPOTENT - preserve existing geocoding and edits)
            try:
                existing_post = self.db.get_post_by_hash(post_data['hash'])
                if existing_post:
                    # IDEMPOTENT UPDATE: Only update missing fields, preserve existing geocoding
                    update_data = {}
                    
                    # Only update if current field is empty/missing - PRESERVE ALL USER EDITS
                    preserve_fields = ['cafe_name', 'city', 'country', 'continent', 'latitude', 'longitude', 'rating', 'notes']
                    
                    for field, new_value in post_data.items():
                        if field == 'hash':  # Skip hash field
                            continue
                        existing_value = existing_post.get(field)
                        
                        # NEVER overwrite geocoding or user-edited fields if they have real values
                        if field in preserve_fields and existing_value and existing_value not in ['Unknown', '', None, 'unknown']:
                            continue  # Keep user's existing data
                        
                        # Special handling for images field - update if empty array
                        if field == 'images':
                            # Check if existing images field is empty
                            existing_empty = False
                            if not existing_value or existing_value in ['', None]:
                                existing_empty = True
                            elif existing_value == '[]':  # JSON string empty array
                                existing_empty = True
                            elif isinstance(existing_value, list) and len(existing_value) == 0:  # Python empty list
                                existing_empty = True
                            elif isinstance(existing_value, str):
                                try:
                                    parsed = json.loads(existing_value)
                                    if isinstance(parsed, list) and len(parsed) == 0:
                                        existing_empty = True
                                except:
                                    pass
                            
                            # Check if new value has content
                            new_has_content = new_value and new_value != '[]'
                            if isinstance(new_value, str):
                                try:
                                    parsed = json.loads(new_value)
                                    new_has_content = isinstance(parsed, list) and len(parsed) > 0
                                except:
                                    new_has_content = bool(new_value)
                            elif isinstance(new_value, list):
                                new_has_content = len(new_value) > 0
                            
                            if existing_empty and new_has_content:
                                update_data[field] = new_value
                                print(f"    Updating images field: {len(json.loads(new_value) if isinstance(new_value, str) else new_value)} images")
                        else:
                            # Update only if existing is empty/None/Unknown and new has content
                            if (not existing_value or existing_value in ['Unknown', '', None]) and new_value and new_value != 'Unknown':
                                update_data[field] = new_value
                    
                    if update_data:
                        self.db.update_post(existing_post['id'], update_data)
                        self.updated_count += 1
                    else:
                        # No updates needed - post already has better data
                        pass
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