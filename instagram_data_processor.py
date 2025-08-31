#!/usr/bin/env python3
"""
Instagram Data Export Processor
Process your official Instagram data download to extract coffee posts
This is the most reliable method to get ALL your posts with full data
"""

import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

class InstagramDataProcessor:
    def __init__(self):
        self.coffee_posts = []
        
    def process_instagram_export(self, export_path):
        """Process Instagram data export (ZIP file or folder)"""
        print("☕ Processing Instagram Data Export...")
        print("=" * 50)
        
        if zipfile.is_zipfile(export_path):
            return self.process_zip_export(export_path)
        else:
            return self.process_folder_export(export_path)
    
    def process_zip_export(self, zip_path):
        """Process ZIP file export"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Look for posts.json or content.json
                json_files = [f for f in zip_file.namelist() if f.endswith('.json') and ('post' in f.lower() or 'content' in f.lower())]
                
                print(f"Found {len(json_files)} JSON files in export")
                
                for json_file in json_files:
                    print(f"Processing {json_file}...")
                    
                    with zip_file.open(json_file) as f:
                        try:
                            data = json.load(f)
                            posts = self.extract_posts_from_export_data(data)
                            self.coffee_posts.extend(posts)
                            print(f"  ✅ Found {len(posts)} posts in {json_file}")
                        except json.JSONDecodeError as e:
                            print(f"  ❌ Error parsing {json_file}: {e}")
                
                return self.coffee_posts
                
        except Exception as e:
            print(f"❌ Error processing ZIP: {e}")
            return []
    
    def process_folder_export(self, folder_path):
        """Process folder export"""
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"❌ Folder not found: {folder_path}")
            return []
        
        # Look for JSON files
        json_files = list(folder.rglob('*.json'))
        
        print(f"Found {len(json_files)} JSON files in export folder")
        
        for json_file in json_files:
            if 'post' in json_file.name.lower() or 'content' in json_file.name.lower():
                print(f"Processing {json_file.name}...")
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        posts = self.extract_posts_from_export_data(data)
                        self.coffee_posts.extend(posts)
                        print(f"  ✅ Found {len(posts)} posts in {json_file.name}")
                except Exception as e:
                    print(f"  ❌ Error parsing {json_file.name}: {e}")
        
        return self.coffee_posts
    
    def extract_posts_from_export_data(self, data):
        """Extract posts from export JSON data"""
        posts = []
        
        # Instagram export format can vary, try different structures
        possible_keys = ['posts', 'content', 'media', 'data', 'items']
        
        posts_data = None
        
        # Try to find posts data
        if isinstance(data, list):
            posts_data = data
        elif isinstance(data, dict):
            for key in possible_keys:
                if key in data:
                    posts_data = data[key]
                    break
        
        if not posts_data:
            print("    No posts data found in this file")
            return []
        
        # Process each post
        for item in posts_data:
            if isinstance(item, dict):
                post = self.process_export_post(item)
                if post:
                    posts.append(post)
        
        return posts
    
    def process_export_post(self, post_data):
        """Process individual post from export"""
        try:
            # Extract caption
            caption = ""
            
            # Try different caption field names
            caption_fields = ['caption', 'text', 'title', 'description', 'string_map_data']
            
            for field in caption_fields:
                if field in post_data:
                    if isinstance(post_data[field], str):
                        caption = post_data[field]
                        break
                    elif isinstance(post_data[field], dict):
                        # Handle nested caption data
                        caption = post_data[field].get('value', '') or post_data[field].get('text', '')
                        break
                    elif isinstance(post_data[field], list) and post_data[field]:
                        caption = post_data[field][0] if isinstance(post_data[field][0], str) else ""
                        break
            
            # Skip if no caption or doesn't contain our hashtag
            if not caption or '#worldcoffeetour' not in caption.lower():
                return None
            
            # Extract timestamp
            timestamp_fields = ['creation_timestamp', 'timestamp', 'taken_at', 'created_at', 'date']
            timestamp = None
            
            for field in timestamp_fields:
                if field in post_data and post_data[field]:
                    timestamp = post_data[field]
                    break
            
            # Convert timestamp to ISO format
            if timestamp:
                if isinstance(timestamp, (int, float)):
                    date = datetime.fromtimestamp(timestamp).isoformat()
                elif isinstance(timestamp, str):
                    try:
                        # Try parsing different date formats
                        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).isoformat()
                    except:
                        date = datetime.now().isoformat()
                else:
                    date = datetime.now().isoformat()
            else:
                date = datetime.now().isoformat()
            
            # Extract media URL
            media_url = ""
            media_fields = ['url', 'uri', 'media_url', 'display_url', 'image_url']
            
            for field in media_fields:
                if field in post_data and post_data[field]:
                    media_url = post_data[field]
                    break
            
            # If no direct URL, look in media array
            if not media_url and 'media' in post_data:
                media_items = post_data['media']
                if isinstance(media_items, list) and media_items:
                    for field in media_fields:
                        if field in media_items[0]:
                            media_url = media_items[0][field]
                            break
            
            # Extract location
            location_data = {}
            if 'location' in post_data and post_data['location']:
                loc = post_data['location']
                if isinstance(loc, dict):
                    location_data = {
                        'name': loc.get('name', ''),
                        'lat': loc.get('latitude') or loc.get('lat'),
                        'lng': loc.get('longitude') or loc.get('lng') or loc.get('long')
                    }
                elif isinstance(loc, str):
                    location_data = {'name': loc, 'lat': None, 'lng': None}
            
            # Generate title from caption
            lines = [line.strip() for line in caption.split('\n') if line.strip()]
            title = ""
            for line in lines:
                if not line.startswith('#') and not line.startswith('@') and len(line) > 10:
                    title = line[:60]
                    break
            
            if not title and location_data.get('name'):
                title = f"Coffee in {location_data['name'].split(',')[0]}"
            elif not title:
                title = "Coffee Stop"
            
            # Clean notes
            notes = re.sub(r'#\w+\s*', '', caption).strip()
            notes = re.sub(r'@\w+\s*', '', notes).strip()
            notes = re.sub(r'\n\n+', '\n', notes).strip()
            
            # Extract shortcode if available
            shortcode = post_data.get('shortcode', '') or post_data.get('id', '') or f"post_{int(datetime.now().timestamp())}"
            
            return {
                'shortcode': shortcode,
                'title': title,
                'caption': caption,
                'notes': notes,
                'date': date,
                'image_url': media_url,
                'location': location_data,
                'instagram_url': f"https://www.instagram.com/p/{shortcode}/" if shortcode.startswith(('A', 'B', 'C')) else ""
            }
            
        except Exception as e:
            print(f"    Error processing post: {e}")
            return None
    
    def save_posts_to_jekyll(self, posts):
        """Save posts as Jekyll files"""
        if not posts:
            print("❌ No posts to save")
            return 0
        
        posts_dir = Path("_coffee_posts")
        posts_dir.mkdir(exist_ok=True)
        
        # Remove old sample posts
        for old_post in posts_dir.glob("2024-*.md"):
            old_post.unlink()
        
        count = 0
        for post in posts:
            try:
                date_str = post['date'][:10]
                title = post['title']
                slug = re.sub(r'[^\w\s-]', '', title.lower())
                slug = re.sub(r'[-\s]+', '-', slug)[:30]
                
                filename = f"{date_str}-{slug}-{post['shortcode']}.md"
                filepath = posts_dir / filename
                
                # Parse location
                location = post.get('location', {})
                city = "Unknown"
                country = "Unknown"  
                region = "World"
                
                if location.get('name'):
                    parts = location['name'].split(',')
                    city = parts[0].strip()
                    if len(parts) > 1:
                        country = parts[-1].strip()
                    
                    # Determine region
                    location_lower = location['name'].lower()
                    region_map = {
                        'Asia': ['japan', 'tokyo', 'kyoto', 'asia', 'china', 'korea', 'thailand', 'vietnam', 'singapore', 'hong kong'],
                        'Europe': ['france', 'italy', 'spain', 'europe', 'paris', 'rome', 'london', 'berlin', 'amsterdam', 'barcelona'],
                        'Americas': ['usa', 'america', 'canada', 'mexico', 'brazil', 'new york', 'portland', 'seattle', 'los angeles'],
                        'Oceania': ['australia', 'new zealand', 'melbourne', 'sydney', 'auckland'],
                        'Africa': ['africa', 'south africa', 'morocco', 'cape town', 'marrakech']
                    }
                    
                    for reg, places in region_map.items():
                        if any(place in location_lower for place in places):
                            region = reg
                            break
                
                post_content = f"""---
layout: post
title: "{title}"
date: {date_str}
city: "{city}"
country: "{country}"
region: "{region}"
latitude: {location.get('lat', 'null')}
longitude: {location.get('lng', 'null')}
cafe_name: ""
coffee_type: ""
rating: 
notes: "{post['notes']}"
image_url: "{post['image_url']}"
instagram_url: "{post['instagram_url']}"
---"""
                
                filepath.write_text(post_content)
                count += 1
                print(f"  ✅ Created: {filename}")
                
            except Exception as e:
                print(f"  ❌ Error creating post: {e}")
        
        return count

def main():
    print("""
☕ Instagram Data Export Processor
==================================

STEP 1: Get Your Instagram Data Export
1. Open Instagram app/website
2. Go to Settings → Privacy and Security
3. Click "Download Your Information"
4. Select format: JSON
5. Select data: Posts, Stories, etc.
6. Click "Request Download"
7. Wait for email (can take 48 hours)
8. Download the ZIP file

STEP 2: Process Your Data
""")
    
    # Always use the instagram-export-folder
    export_path = "instagram-export-folder"
    print(f"Using export folder: {export_path}")
    
    processor = InstagramDataProcessor()
    posts = processor.process_instagram_export(export_path)
    
    if posts:
        print(f"\n🎉 Found {len(posts)} coffee tour posts!")
        
        # Show preview
        for i, post in enumerate(posts[:5], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   📅 {post['date'][:10]}")
            if post['location'].get('name'):
                print(f"   📍 {post['location']['name']}")
            if post['notes']:
                print(f"   📝 {post['notes'][:80]}...")
        
        if len(posts) > 5:
            print(f"\n... and {len(posts) - 5} more posts")
        
        # Save posts
        created = processor.save_posts_to_jekyll(posts)
        print(f"\n💾 Created {created} Jekyll posts!")
        print("🔄 Check http://localhost:4000 to see your complete coffee tour!")
        
    else:
        print("\n❌ No coffee posts found in export")
        print("\nPossible reasons:")
        print("- No posts have #worldcoffeetour hashtag")
        print("- Export format is different than expected")
        print("- Export is incomplete")
        
        print("\nTroubleshooting:")
        print("1. Make sure you selected 'Posts' in the export")
        print("2. Try exporting in HTML format instead of JSON")
        print("3. Check that your posts actually have #worldcoffeetour")

if __name__ == "__main__":
    main()