#!/usr/bin/env python3
"""
Instagram Scraper for World Coffee Tour Posts
Multiple approaches to extract your Instagram posts with #worldcoffeetour
"""

import requests
import json
import re
from datetime import datetime
from pathlib import Path
import time

class InstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        })

    def scrape_profile_page(self, username):
        """Method 1: Scrape the profile page HTML"""
        print(f"🔍 Scraping profile page for @{username}")
        
        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extract JSON data from HTML
            json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', response.text)
            if not json_match:
                # Try newer pattern
                json_match = re.search(r'<script type="application/ld\+json">({.+?})</script>', response.text)
            
            if json_match:
                data = json.loads(json_match.group(1))
                return self.extract_posts_from_data(data, username)
            else:
                print("❌ Could not find JSON data in HTML")
                return []
                
        except Exception as e:
            print(f"❌ Error scraping profile: {e}")
            return []

    def scrape_with_proxy(self, username):
        """Method 2: Use Instagram's web API endpoints"""
        print(f"🔍 Trying web API for @{username}")
        
        try:
            # First get the profile page to get user ID
            profile_url = f"https://www.instagram.com/{username}/"
            response = self.session.get(profile_url)
            
            # Extract user ID from HTML
            user_id_match = re.search(r'"profilePage_(\d+)"', response.text)
            if not user_id_match:
                user_id_match = re.search(r'"id":"(\d+)".*?"username":"' + username, response.text)
            
            if user_id_match:
                user_id = user_id_match.group(1)
                print(f"Found user ID: {user_id}")
                
                # Now try to get posts using the user ID
                posts_url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/"
                posts_response = self.session.get(posts_url)
                
                if posts_response.status_code == 200:
                    posts_data = posts_response.json()
                    return self.extract_posts_from_api_data(posts_data)
                else:
                    print(f"❌ API request failed: {posts_response.status_code}")
                    
            return []
            
        except Exception as e:
            print(f"❌ Error with web API: {e}")
            return []

    def scrape_rss_alternative(self, username):
        """Method 3: Use third-party RSS/JSON services"""
        print(f"🔍 Trying alternative services for @{username}")
        
        # Try different services
        services = [
            f"https://www.instagram.com/{username}/?__a=1",
            f"https://bibliogram.art/u/{username}",
            f"https://imginn.com/{username}/"
        ]
        
        for service_url in services:
            try:
                print(f"  Trying: {service_url}")
                response = self.session.get(service_url, timeout=10)
                
                if response.status_code == 200:
                    if "application/json" in response.headers.get('content-type', ''):
                        # JSON response
                        data = response.json()
                        posts = self.extract_posts_from_data(data, username)
                        if posts:
                            return posts
                    else:
                        # HTML response - look for post data
                        posts = self.extract_posts_from_html(response.text, username)
                        if posts:
                            return posts
                            
            except Exception as e:
                print(f"  ❌ Service failed: {e}")
                continue
        
        return []

    def manual_input_mode(self):
        """Method 4: Manual input with URL parsing"""
        print("\n📝 Manual Input Mode")
        print("Enter Instagram post URLs one by one (empty line to finish)")
        
        posts = []
        while True:
            url = input("Instagram post URL: ").strip()
            if not url:
                break
                
            post_data = self.extract_single_post(url)
            if post_data:
                posts.append(post_data)
                print(f"  ✅ Added: {post_data['title']}")
            else:
                print(f"  ❌ Failed to extract post data")
        
        return posts

    def extract_single_post(self, url):
        """Extract data from a single Instagram post URL"""
        try:
            # Extract shortcode from URL
            shortcode_match = re.search(r'/p/([A-Za-z0-9_-]+)/', url)
            if not shortcode_match:
                return None
            
            shortcode = shortcode_match.group(1)
            
            # Try to get post data
            post_url = f"https://www.instagram.com/p/{shortcode}/"
            response = self.session.get(post_url)
            
            # Extract post data from HTML
            json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', response.text)
            if json_match:
                data = json.loads(json_match.group(1))
                # Parse the post data structure
                # This will vary based on Instagram's current HTML structure
                return self.parse_single_post_data(data, shortcode)
            
        except Exception as e:
            print(f"Error extracting post {url}: {e}")
            
        return None

    def extract_posts_from_data(self, data, username):
        """Extract posts from JSON data"""
        posts = []
        
        try:
            # Navigate through Instagram's data structure
            # This structure changes frequently, so we try multiple paths
            possible_paths = [
                ['entry_data', 'ProfilePage', 0, 'graphql', 'user', 'edge_owner_to_timeline_media', 'edges'],
                ['data', 'user', 'edge_owner_to_timeline_media', 'edges'],
                ['graphql', 'user', 'edge_owner_to_timeline_media', 'edges']
            ]
            
            for path in possible_paths:
                current = data
                try:
                    for key in path:
                        if isinstance(key, int):
                            current = current[key]
                        else:
                            current = current[key]
                    
                    # Found posts data
                    for edge in current:
                        post = edge.get('node', {})
                        caption_edges = post.get('edge_media_to_caption', {}).get('edges', [])
                        caption = caption_edges[0]['node']['text'] if caption_edges else ""
                        
                        # Check if post has our hashtag
                        if '#worldcoffeetour' in caption.lower():
                            post_data = self.format_post_data(post, caption)
                            if post_data:
                                posts.append(post_data)
                                
                    if posts:
                        break
                        
                except (KeyError, IndexError, TypeError):
                    continue
            
        except Exception as e:
            print(f"Error parsing data: {e}")
        
        return posts

    def format_post_data(self, post, caption):
        """Format Instagram post data into our structure"""
        try:
            # Extract basic info
            shortcode = post.get('shortcode', '')
            timestamp = post.get('taken_at_timestamp', 0)
            date = datetime.fromtimestamp(timestamp).isoformat() if timestamp else datetime.now().isoformat()
            
            # Get image URL
            image_url = ""
            if 'display_url' in post:
                image_url = post['display_url']
            elif 'thumbnail_src' in post:
                image_url = post['thumbnail_src']
            
            # Extract location if available
            location_data = {}
            if post.get('location'):
                location = post['location']
                location_data = {
                    'name': location.get('name', ''),
                    'lat': location.get('lat'),
                    'lng': location.get('lng')
                }
            
            # Clean caption for title and notes
            lines = [line.strip() for line in caption.split('\n') if line.strip()]
            title = ""
            for line in lines:
                if not line.startswith('#') and not line.startswith('@'):
                    title = line[:50]
                    break
            
            if not title:
                title = "Coffee Stop"
            
            # Clean notes
            notes = re.sub(r'#\w+\s*', '', caption).strip()
            notes = re.sub(r'\n\n+', '\n', notes).strip()
            
            return {
                'shortcode': shortcode,
                'title': title,
                'caption': caption,
                'notes': notes,
                'date': date,
                'image_url': image_url,
                'location': location_data,
                'instagram_url': f"https://www.instagram.com/p/{shortcode}/"
            }
            
        except Exception as e:
            print(f"Error formatting post: {e}")
            return None

    def save_posts_to_jekyll(self, posts):
        """Save posts as Jekyll markdown files"""
        if not posts:
            print("❌ No posts to save")
            return
        
        from fetch_instagram import create_jekyll_posts
        created = create_jekyll_posts(posts)
        print(f"✅ Created {created} Jekyll posts")

def main():
    print("""
☕ Instagram Scraper for World Coffee Tour
==========================================

This script tries multiple methods to extract your Instagram posts:
1. Profile page scraping
2. Web API endpoints
3. Alternative services
4. Manual URL input

Choose a method or try all automatically.
""")
    
    username = input("Instagram username [joegaudet]: ").strip() or "joegaudet"
    scraper = InstagramScraper()
    
    print("\nChoose method:")
    print("1. Try all automatic methods")
    print("2. Profile page scraping only")
    print("3. Manual URL input")
    print("4. Exit")
    
    choice = input("Choice (1-4): ").strip()
    
    posts = []
    
    if choice == '1':
        print("\n🤖 Trying all automatic methods...")
        
        # Try each method
        methods = [
            scraper.scrape_profile_page,
            scraper.scrape_with_proxy,
            scraper.scrape_rss_alternative
        ]
        
        for method in methods:
            try:
                result = method(username)
                if result:
                    posts.extend(result)
                    print(f"✅ Found {len(result)} posts with this method")
                    break
                else:
                    print("❌ No posts found with this method")
            except Exception as e:
                print(f"❌ Method failed: {e}")
            
            time.sleep(2)  # Rate limiting
    
    elif choice == '2':
        posts = scraper.scrape_profile_page(username)
    
    elif choice == '3':
        posts = scraper.manual_input_mode()
    
    elif choice == '4':
        print("Goodbye! 👋")
        return
    
    else:
        print("Invalid choice")
        return
    
    if posts:
        print(f"\n🎉 Found {len(posts)} posts with #worldcoffeetour")
        
        # Show preview
        for i, post in enumerate(posts[:3], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   Date: {post['date'][:10]}")
            if post['location'].get('name'):
                print(f"   Location: {post['location']['name']}")
        
        if len(posts) > 3:
            print(f"\n... and {len(posts) - 3} more posts")
        
        save = input("\n💾 Save these posts to Jekyll? (y/n): ").strip().lower()
        if save == 'y':
            scraper.save_posts_to_jekyll(posts)
            print("\n🔄 Restart Jekyll to see your posts:")
            print("bundle exec jekyll serve")
        else:
            print("Posts not saved")
    else:
        print("\n❌ No posts found")
        print("\nTips:")
        print("- Make sure your profile is public")
        print("- Check that you have posts with #worldcoffeetour")
        print("- Try the manual URL input method")
        print("- Instagram may be blocking requests - try again later")

if __name__ == "__main__":
    main()