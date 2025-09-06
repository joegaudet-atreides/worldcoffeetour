#!/usr/bin/env python3
"""
Backfill database with metadata from GitHub repository posts
"""

import requests
import re
import json
from datetime import datetime
from coffee_db import CoffeeDatabase

class GitHubBackfiller:
    def __init__(self):
        self.db = CoffeeDatabase()
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
        # GitHub raw content base URL
        self.base_url = "https://raw.githubusercontent.com/joegaudet-atreides/worldcoffeetour/main/_coffee_posts/"
        
    def get_github_post_list(self):
        """Get list of all posts from GitHub API"""
        api_url = "https://api.github.com/repos/joegaudet-atreides/worldcoffeetour/contents/_coffee_posts"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            files = response.json()
            
            # Filter for markdown files
            md_files = [f['name'] for f in files if f['name'].endswith('.md')]
            print(f"📁 Found {len(md_files)} posts on GitHub")
            return md_files
            
        except Exception as e:
            print(f"❌ Error fetching post list: {e}")
            return []
    
    def fetch_post_content(self, filename):
        """Fetch post content from GitHub"""
        url = self.base_url + filename
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Error fetching {filename}: {e}")
            return None
    
    def parse_frontmatter(self, content):
        """Parse YAML frontmatter from post content"""
        if not content.startswith('---'):
            return None
            
        # Split content into frontmatter and body
        parts = content.split('---', 2)
        if len(parts) < 2:
            return None
            
        frontmatter_text = parts[1].strip()
        
        # Simple YAML-like parsing for our specific format
        data = {}
        
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Handle special cases
                if key == 'latitude' or key == 'longitude':
                    try:
                        data[key] = float(value) if value else None
                    except:
                        data[key] = None
                elif key == 'published':
                    data[key] = value == '1' or value.lower() == 'true'
                elif key == 'images':
                    # Skip images parsing for now - we have better images from import
                    continue  
                else:
                    data[key] = value if value else None
        
        return data
    
    def find_matching_db_post(self, github_data):
        """Find matching post in database"""
        title = github_data.get('title', '')
        date = github_data.get('date', '')
        
        if not title or not date:
            return None
            
        # Get posts from database and try to match
        posts = self.db.get_all_posts()
        
        for post in posts:
            # Try exact date match first
            if post.get('date') == date:
                # Check title similarity
                db_title = post.get('title', '').lower()
                gh_title = title.lower()
                
                # Simple fuzzy matching - check if key words match
                if any(word in db_title for word in gh_title.split()[:3]):
                    return post
            
            # Also try matching by cafe name if available
            if github_data.get('cafe_name'):
                if github_data['cafe_name'].lower() in post.get('title', '').lower():
                    return post
                    
        return None
    
    def update_db_post(self, db_post, github_data):
        """Update database post with GitHub metadata"""
        update_data = {}
        
        # Fields to update from GitHub (only if DB value is empty/Unknown)
        update_fields = {
            'city': 'city',
            'country': 'country', 
            'continent': 'continent',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'cafe_name': 'cafe_name',
            'notes': 'notes',
            'instagram_url': 'instagram_url'
        }
        
        for db_field, gh_field in update_fields.items():
            existing_value = db_post.get(db_field)
            new_value = github_data.get(gh_field)
            
            if new_value and (not existing_value or existing_value in ['Unknown', '', None, 'unknown']):
                update_data[db_field] = new_value
        
        # Update the post if we have new data
        if update_data:
            try:
                self.db.update_post(db_post['id'], update_data)
                print(f"  ✅ Updated: {update_data}")
                return True
            except Exception as e:
                print(f"  ❌ Error updating: {e}")
                return False
        else:
            print(f"  ⏭️  No updates needed")
            return False
    
    def backfill_all(self):
        """Backfill all posts from GitHub"""
        print("🔄 Starting GitHub backfill process...")
        
        # Get list of posts from GitHub
        github_files = self.get_github_post_list()
        
        if not github_files:
            print("❌ No posts found on GitHub")
            return
        
        print(f"📥 Processing {len(github_files)} posts...")
        
        for i, filename in enumerate(github_files, 1):
            print(f"\n[{i}/{len(github_files)}] Processing: {filename}")
            
            # Fetch post content
            content = self.fetch_post_content(filename)
            if not content:
                self.error_count += 1
                continue
                
            # Parse frontmatter
            github_data = self.parse_frontmatter(content)
            if not github_data:
                print("  ⚠️  No valid frontmatter found")
                self.skipped_count += 1
                continue
            
            print(f"  📍 GitHub: {github_data.get('cafe_name', 'Unknown')} in {github_data.get('city', 'Unknown')}")
            
            # Find matching post in database
            db_post = self.find_matching_db_post(github_data)
            if not db_post:
                print(f"  ❓ No matching post found in database")
                self.skipped_count += 1
                continue
                
            print(f"  🎯 Matched DB post ID {db_post['id']}: {db_post['title'][:50]}...")
            
            # Update database post
            if self.update_db_post(db_post, github_data):
                self.updated_count += 1
            else:
                self.skipped_count += 1
        
        # Print summary
        print(f"\n📊 Backfill Summary:")
        print(f"  ✅ Updated: {self.updated_count} posts")
        print(f"  ⏭️  Skipped: {self.skipped_count} posts") 
        print(f"  ❌ Errors: {self.error_count} posts")
        
        self.db.close()

def main():
    backfiller = GitHubBackfiller()
    backfiller.backfill_all()

if __name__ == "__main__":
    main()