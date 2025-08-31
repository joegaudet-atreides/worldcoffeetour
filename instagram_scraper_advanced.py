#!/usr/bin/env python3
"""
Advanced Instagram Scraper for World Coffee Tour
Based on techniques from scrapfly.io/blog/posts/how-to-scrape-instagram
"""

import requests
import json
import re
import time
import base64
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

class AdvancedInstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        
        self.setup_session()
    
    def setup_session(self):
        """Setup session with proper headers"""
        import random
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })

    def get_csrf_token(self):
        """Get CSRF token from Instagram"""
        try:
            response = self.session.get('https://www.instagram.com/')
            csrf_token = re.search(r'"csrf_token":"([^"]*)"', response.text)
            if csrf_token:
                return csrf_token.group(1)
        except:
            pass
        return None

    def scrape_profile_posts(self, username):
        """Scrape posts from profile using web endpoint"""
        print(f"🔍 Scraping profile @{username}")
        
        try:
            # First, get the profile page
            profile_url = f"https://www.instagram.com/{username}/"
            response = self.session.get(profile_url)
            response.raise_for_status()
            
            # Extract initial data
            posts = self.extract_posts_from_html(response.text)
            
            if posts:
                print(f"✅ Found {len(posts)} posts from profile page")
                return self.filter_coffee_posts(posts)
            
            # If no posts found, try the GraphQL approach
            return self.scrape_with_graphql(username, response.text)
            
        except Exception as e:
            print(f"❌ Error scraping profile: {e}")
            return []

    def extract_posts_from_html(self, html):
        """Extract posts from HTML using multiple patterns"""
        posts = []
        
        # Pattern 1: window._sharedData
        shared_data_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html)
        if shared_data_match:
            try:
                data = json.loads(shared_data_match.group(1))
                posts.extend(self.parse_shared_data(data))
            except:
                pass
        
        # Pattern 2: Script tags with application/ld+json
        ld_json_matches = re.findall(r'<script type="application/ld\+json">({.+?})</script>', html, re.DOTALL)
        for match in ld_json_matches:
            try:
                data = json.loads(match)
                posts.extend(self.parse_ld_json(data))
            except:
                pass
        
        # Pattern 3: Modern Instagram structure
        additional_data = re.findall(r'"shortcode":"([^"]+)".*?"display_url":"([^"]+)".*?"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"([^"]+)"\}\}\]\}', html)
        for shortcode, image_url, caption in additional_data:
            if '#worldcoffeetour' in caption.lower():
                posts.append(self.format_basic_post(shortcode, image_url, caption))
        
        return posts

    def parse_shared_data(self, data):
        """Parse posts from window._sharedData"""
        posts = []
        
        try:
            # Navigate the data structure
            profile_page = data.get('entry_data', {}).get('ProfilePage', [])
            if profile_page:
                user_data = profile_page[0].get('graphql', {}).get('user', {})
                media_edges = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                
                for edge in media_edges:
                    node = edge.get('node', {})
                    caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                    caption = caption_edges[0]['node']['text'] if caption_edges else ""
                    
                    if '#worldcoffeetour' in caption.lower():
                        post_data = self.format_post_from_node(node, caption)
                        if post_data:
                            posts.append(post_data)
        except Exception as e:
            print(f"Error parsing shared data: {e}")
        
        return posts

    def format_post_from_node(self, node, caption):
        """Format post data from Instagram node"""
        try:
            shortcode = node.get('shortcode', '')
            timestamp = node.get('taken_at_timestamp', 0)
            image_url = node.get('display_url', '')
            
            # Location data
            location_data = {}
            if node.get('location'):
                loc = node['location']
                location_data = {
                    'name': loc.get('name', ''),
                    'lat': loc.get('lat'),
                    'lng': loc.get('lng')
                }
            
            # Clean caption
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
            
            return {
                'shortcode': shortcode,
                'title': title,
                'caption': caption,
                'notes': notes,
                'date': datetime.fromtimestamp(timestamp).isoformat() if timestamp else datetime.now().isoformat(),
                'image_url': image_url,
                'location': location_data,
                'instagram_url': f"https://www.instagram.com/p/{shortcode}/"
            }
            
        except Exception as e:
            print(f"Error formatting post: {e}")
            return None

    def scrape_with_graphql(self, username, html):
        """Try to use Instagram's GraphQL API"""
        print("🔍 Trying GraphQL approach...")
        
        try:
            # Extract user ID from HTML
            user_id_match = re.search(r'"id":"(\d+)"[^}]*"username":"' + re.escape(username), html)
            if not user_id_match:
                return []
            
            user_id = user_id_match.group(1)
            print(f"Found user ID: {user_id}")
            
            # GraphQL query for user posts
            query_hash = "e769aa130647d2354c40ea6a439bfc08"  # This may need updating
            variables = {
                "id": user_id,
                "first": 50
            }
            
            csrf_token = self.get_csrf_token()
            if not csrf_token:
                return []
            
            headers = {
                'x-csrftoken': csrf_token,
                'x-requested-with': 'XMLHttpRequest',
            }
            
            url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables)}"
            
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_graphql_response(data)
            else:
                print(f"GraphQL request failed: {response.status_code}")
                
        except Exception as e:
            print(f"GraphQL error: {e}")
        
        return []

    def scrape_individual_posts(self, post_urls):
        """Scrape individual posts by URL"""
        print(f"🔍 Scraping {len(post_urls)} individual posts")
        
        posts = []
        for url in post_urls:
            try:
                # Extract shortcode
                shortcode_match = re.search(r'/p/([A-Za-z0-9_-]+)/', url)
                if not shortcode_match:
                    continue
                
                shortcode = shortcode_match.group(1)
                
                # Get post page
                post_response = self.session.get(url)
                post_response.raise_for_status()
                
                # Extract post data
                post_data = self.extract_single_post_data(post_response.text, shortcode)
                if post_data and '#worldcoffeetour' in post_data.get('caption', '').lower():
                    posts.append(post_data)
                    print(f"  ✅ {post_data['title']}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error scraping {url}: {e}")
        
        return posts

    def extract_single_post_data(self, html, shortcode):
        """Extract data from single post HTML"""
        try:
            # Look for post data in HTML
            shared_data_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html)
            if shared_data_match:
                data = json.loads(shared_data_match.group(1))
                
                # Navigate to post data
                post_page = data.get('entry_data', {}).get('PostPage', [])
                if post_page:
                    media = post_page[0].get('graphql', {}).get('shortcode_media', {})
                    caption_edges = media.get('edge_media_to_caption', {}).get('edges', [])
                    caption = caption_edges[0]['node']['text'] if caption_edges else ""
                    
                    return self.format_post_from_node(media, caption)
            
            # Fallback: extract basic info from HTML
            image_match = re.search(r'"display_url":"([^"]+)"', html)
            caption_match = re.search(r'"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"([^"]+)"\}\}\]\}', html)
            
            if image_match and caption_match:
                return self.format_basic_post(shortcode, image_match.group(1), caption_match.group(1))
        
        except Exception as e:
            print(f"Error extracting single post: {e}")
        
        return None

    def format_basic_post(self, shortcode, image_url, caption):
        """Format basic post data"""
        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        title = lines[0][:60] if lines else "Coffee Stop"
        
        notes = re.sub(r'#\w+\s*', '', caption).strip()
        
        return {
            'shortcode': shortcode,
            'title': title,
            'caption': caption,
            'notes': notes,
            'date': datetime.now().isoformat(),
            'image_url': image_url,
            'location': {},
            'instagram_url': f"https://www.instagram.com/p/{shortcode}/"
        }

    def filter_coffee_posts(self, posts):
        """Filter posts that contain #worldcoffeetour"""
        coffee_posts = []
        for post in posts:
            caption = post.get('caption', '').lower()
            if '#worldcoffeetour' in caption:
                coffee_posts.append(post)
        
        return coffee_posts

    def save_posts_to_jekyll(self, posts):
        """Save posts as Jekyll files"""
        if not posts:
            print("❌ No posts to save")
            return 0
        
        try:
            # Import the function from our existing script
            import sys
            sys.path.append('.')
            from fetch_instagram import create_jekyll_posts
            return create_jekyll_posts(posts)
        except ImportError:
            # Fallback: create posts manually
            return self.create_jekyll_posts_fallback(posts)

    def create_jekyll_posts_fallback(self, posts):
        """Fallback method to create Jekyll posts"""
        posts_dir = Path("_coffee_posts")
        posts_dir.mkdir(exist_ok=True)
        
        count = 0
        for post in posts:
            try:
                date_str = post['date'][:10]
                title = post['title']
                slug = re.sub(r'[^\w\s-]', '', title.lower())
                slug = re.sub(r'[-\s]+', '-', slug)[:30]
                
                filename = f"{date_str}-{slug}.md"
                filepath = posts_dir / filename
                
                # Determine region and location
                location = post.get('location', {})
                city = location.get('name', '').split(',')[0] if location.get('name') else "Unknown"
                country = location.get('name', '').split(',')[-1].strip() if location.get('name') else "Unknown"
                
                post_content = f"""---
layout: post
title: "{title}"
date: {date_str}
city: "{city}"
country: "{country}"
region: "World"
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
                
            except Exception as e:
                print(f"Error creating post: {e}")
        
        return count

def main():
    print("""
☕ Advanced Instagram Scraper
=============================
Based on scrapfly.io techniques

This scraper uses multiple methods:
1. Profile page HTML parsing
2. GraphQL API endpoints  
3. Individual post scraping
4. Pattern matching and data extraction
""")
    
    username = input("Instagram username [joegaudet]: ").strip() or "joegaudet"
    scraper = AdvancedInstagramScraper()
    
    print(f"\n🚀 Starting scrape for @{username}")
    print("This may take a few minutes...")
    
    # Method 1: Profile scraping
    posts = scraper.scrape_profile_posts(username)
    
    if not posts:
        print("\n❌ No posts found with automatic scraping")
        print("\n💡 Try manual mode:")
        print("1. Go to your Instagram profile")
        print("2. Copy URLs of posts with #worldcoffeetour")
        print("3. Paste them here (one per line, empty line to finish):")
        
        urls = []
        while True:
            url = input("Post URL: ").strip()
            if not url:
                break
            urls.append(url)
        
        if urls:
            posts = scraper.scrape_individual_posts(urls)
    
    if posts:
        print(f"\n🎉 Found {len(posts)} coffee posts!")
        
        # Show preview
        for i, post in enumerate(posts[:3], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   📅 {post['date'][:10]}")
            if post['location'].get('name'):
                print(f"   📍 {post['location']['name']}")
            if post['notes']:
                print(f"   📝 {post['notes'][:100]}...")
        
        if len(posts) > 3:
            print(f"\n... and {len(posts) - 3} more")
        
        # Save posts
        save = input("\n💾 Create Jekyll posts? (y/n): ").strip().lower()
        if save == 'y':
            created = scraper.save_posts_to_jekyll(posts)
            print(f"\n✅ Created {created} Jekyll posts!")
            print("\n🔄 Your site will auto-rebuild. Check http://localhost:4000")
        
    else:
        print("\n❌ No posts found")
        print("\nTroubleshooting:")
        print("- Ensure your profile is public")
        print("- Check posts have #worldcoffeetour hashtag")
        print("- Instagram may be blocking requests")
        print("- Try again later or use manual URL input")

if __name__ == "__main__":
    main()