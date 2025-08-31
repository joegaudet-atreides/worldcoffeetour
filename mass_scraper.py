#!/usr/bin/env python3
"""
Mass Instagram Scraper for hundreds of posts
Multiple aggressive techniques to extract all #worldcoffeetour posts
"""

import requests
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

class MassInstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        self.posts_found = []
        
        # Rotate through different user agents
        self.user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 10; Mobile; rv:81.0) Gecko/81.0 Firefox/81.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.setup_session()

    def setup_session(self):
        """Setup session with rotating headers"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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

    def method_1_hashtag_scraping(self):
        """Method 1: Scrape from hashtag page"""
        print("🔍 Method 1: Scraping #worldcoffeetour hashtag page...")
        
        try:
            url = "https://www.instagram.com/explore/tags/worldcoffeetour/"
            response = self.session.get(url)
            
            if response.status_code == 200:
                posts = self.extract_posts_from_hashtag_html(response.text)
                print(f"   Found {len(posts)} posts from hashtag page")
                return posts
            else:
                print(f"   Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        return []

    def method_2_profile_deep_scrape(self, username="joegaudet"):
        """Method 2: Deep scrape profile with pagination"""
        print(f"🔍 Method 2: Deep scraping @{username} profile...")
        
        try:
            # Get initial profile page
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url)
            
            if response.status_code != 200:
                print(f"   Failed: HTTP {response.status_code}")
                return []
            
            # Extract initial posts
            posts = self.extract_posts_from_profile_html(response.text)
            
            # Try to get more posts using pagination
            more_posts = self.paginate_profile_posts(response.text, username)
            posts.extend(more_posts)
            
            print(f"   Found {len(posts)} total posts from profile")
            return posts
            
        except Exception as e:
            print(f"   Error: {e}")
            return []

    def method_3_rss_feeds(self, username="joegaudet"):
        """Method 3: Try RSS/JSON feeds and proxies"""
        print(f"🔍 Method 3: Trying RSS feeds for @{username}...")
        
        services = [
            f"https://www.instagram.com/{username}/?__a=1&__d=dis",
            f"https://www.picuki.com/profile/{username}",
            f"https://imginn.com/{username}/",
            f"https://bibliogram.art/u/{username}",
            f"https://www.instadp.com/fullsize/{username}",
        ]
        
        all_posts = []
        for service_url in services:
            try:
                print(f"   Trying: {service_url}")
                response = self.session.get(service_url, timeout=10)
                
                if response.status_code == 200:
                    if "application/json" in response.headers.get('content-type', ''):
                        data = response.json()
                        posts = self.extract_posts_from_json_feed(data)
                    else:
                        posts = self.extract_posts_from_service_html(response.text, service_url)
                    
                    if posts:
                        print(f"   ✅ Found {len(posts)} posts from {service_url}")
                        all_posts.extend(posts)
                        break
                    else:
                        print(f"   ❌ No posts found")
                else:
                    print(f"   ❌ HTTP {response.status_code}")
                    
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        return all_posts

    def method_4_individual_post_urls(self):
        """Method 4: If you can provide post URLs, scrape them individually"""
        print("🔍 Method 4: Individual post URL scraping...")
        print("   If you have specific post URLs, we can scrape them individually")
        return []

    def extract_posts_from_hashtag_html(self, html):
        """Extract posts from hashtag page HTML"""
        posts = []
        
        # Look for post data in script tags
        script_matches = re.findall(r'<script[^>]*>window\._sharedData\s*=\s*({.+?});</script>', html, re.DOTALL)
        
        for script_content in script_matches:
            try:
                data = json.loads(script_content)
                
                # Navigate hashtag data structure
                hashtag_page = data.get('entry_data', {}).get('TagPage', [])
                if hashtag_page:
                    hashtag_data = hashtag_page[0].get('graphql', {}).get('hashtag', {})
                    media_edges = hashtag_data.get('edge_hashtag_to_media', {}).get('edges', [])
                    
                    for edge in media_edges:
                        node = edge.get('node', {})
                        post_data = self.format_post_from_node(node)
                        if post_data:
                            posts.append(post_data)
                            
            except json.JSONDecodeError:
                continue
        
        # Fallback: extract from HTML patterns
        if not posts:
            shortcode_pattern = r'"shortcode":"([^"]+)"[^}]*"display_url":"([^"]+)"'
            matches = re.findall(shortcode_pattern, html)
            
            for shortcode, image_url in matches:
                posts.append({
                    'shortcode': shortcode,
                    'image_url': image_url,
                    'title': 'Coffee Stop',
                    'caption': '',
                    'notes': '',
                    'date': datetime.now().isoformat(),
                    'location': {},
                    'instagram_url': f"https://www.instagram.com/p/{shortcode}/"
                })
        
        return posts

    def extract_posts_from_profile_html(self, html):
        """Extract posts from profile HTML"""
        posts = []
        
        # Method 1: window._sharedData
        shared_data_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html)
        if shared_data_match:
            try:
                data = json.loads(shared_data_match.group(1))
                posts = self.parse_profile_shared_data(data)
            except json.JSONDecodeError:
                pass
        
        # Method 2: Extract shortcodes and image URLs
        if not posts:
            pattern = r'"shortcode":"([^"]+)"[^}]*"display_url":"([^"]+)"[^}]*"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"([^"]*)"\}\}\]\}'
            matches = re.findall(pattern, html)
            
            for shortcode, image_url, caption in matches:
                if '#worldcoffeetour' in caption.lower():
                    posts.append(self.create_basic_post(shortcode, image_url, caption))
        
        return posts

    def paginate_profile_posts(self, html, username):
        """Try to get more posts using pagination"""
        posts = []
        
        try:
            # Extract pagination cursor
            cursor_match = re.search(r'"end_cursor":"([^"]*)"', html)
            if not cursor_match:
                return posts
                
            end_cursor = cursor_match.group(1)
            
            # Extract user ID
            user_id_match = re.search(r'"id":"(\d+)"[^}]*"username":"' + re.escape(username), html)
            if not user_id_match:
                return posts
                
            user_id = user_id_match.group(1)
            
            # Try GraphQL query for more posts
            query_hash = "e769aa130647d2354c40ea6a439bfc08"  # May need updating
            variables = {
                "id": user_id,
                "first": 50,
                "after": end_cursor
            }
            
            headers = {
                'x-requested-with': 'XMLHttpRequest',
            }
            
            url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables)}"
            
            for page in range(5):  # Try up to 5 pages
                response = self.session.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    page_posts = self.parse_graphql_posts(data)
                    posts.extend(page_posts)
                    
                    # Update cursor for next page
                    if 'data' in data and 'user' in data['data']:
                        page_info = data['data']['user'].get('edge_owner_to_timeline_media', {}).get('page_info', {})
                        if not page_info.get('has_next_page'):
                            break
                        end_cursor = page_info.get('end_cursor')
                        variables['after'] = end_cursor
                else:
                    break
                
                time.sleep(2)  # Rate limiting
                
        except Exception as e:
            print(f"   Pagination error: {e}")
        
        return posts

    def parse_graphql_posts(self, data):
        """Parse posts from GraphQL response"""
        posts = []
        
        try:
            edges = data.get('data', {}).get('user', {}).get('edge_owner_to_timeline_media', {}).get('edges', [])
            
            for edge in edges:
                node = edge.get('node', {})
                caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                caption = caption_edges[0]['node']['text'] if caption_edges else ""
                
                if '#worldcoffeetour' in caption.lower():
                    post_data = self.format_post_from_node(node, caption)
                    if post_data:
                        posts.append(post_data)
                        
        except Exception as e:
            print(f"Error parsing GraphQL: {e}")
        
        return posts

    def format_post_from_node(self, node, caption=""):
        """Format post data from Instagram node"""
        try:
            shortcode = node.get('shortcode', '')
            timestamp = node.get('taken_at_timestamp', 0)
            image_url = node.get('display_url', '')
            
            if not caption:
                caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                caption = caption_edges[0]['node']['text'] if caption_edges else ""
            
            # Location
            location_data = {}
            if node.get('location'):
                loc = node['location']
                location_data = {
                    'name': loc.get('name', ''),
                    'lat': loc.get('lat'),
                    'lng': loc.get('lng')
                }
            
            # Title from caption
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

    def create_basic_post(self, shortcode, image_url, caption):
        """Create basic post structure"""
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

    def run_all_methods(self, username="joegaudet"):
        """Run all scraping methods"""
        print(f"""
☕ Mass Instagram Scraper
========================
Target: @{username} with #worldcoffeetour
Looking for hundreds of posts...
""")
        
        all_posts = []
        
        # Method 1: Hashtag scraping
        hashtag_posts = self.method_1_hashtag_scraping()
        if hashtag_posts:
            all_posts.extend(hashtag_posts)
        
        # Method 2: Profile deep scrape
        profile_posts = self.method_2_profile_deep_scrape(username)
        if profile_posts:
            all_posts.extend(profile_posts)
        
        # Method 3: RSS/alternative services
        rss_posts = self.method_3_rss_feeds(username)
        if rss_posts:
            all_posts.extend(rss_posts)
        
        # Remove duplicates
        seen_shortcodes = set()
        unique_posts = []
        for post in all_posts:
            shortcode = post.get('shortcode', '')
            if shortcode and shortcode not in seen_shortcodes:
                seen_shortcodes.add(shortcode)
                unique_posts.append(post)
        
        # Filter for coffee posts
        coffee_posts = [post for post in unique_posts if '#worldcoffeetour' in post.get('caption', '').lower()]
        
        print(f"\n🎉 RESULTS:")
        print(f"   Total posts found: {len(all_posts)}")
        print(f"   Coffee tour posts: {len(coffee_posts)}")
        
        return coffee_posts

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
                
                filename = f"{date_str}-{slug}-{post['shortcode']}.md"  # Include shortcode to avoid duplicates
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
                    if any(place in location_lower for place in ['japan', 'tokyo', 'kyoto', 'asia', 'china', 'korea', 'thailand']):
                        region = "Asia"
                    elif any(place in location_lower for place in ['france', 'italy', 'spain', 'europe', 'paris', 'rome', 'london']):
                        region = "Europe"
                    elif any(place in location_lower for place in ['usa', 'america', 'canada', 'mexico', 'brazil', 'new york', 'portland']):
                        region = "Americas"
                    elif any(place in location_lower for place in ['australia', 'new zealand', 'melbourne', 'sydney']):
                        region = "Oceania"
                    elif any(place in location_lower for place in ['africa', 'south africa', 'morocco', 'cape town']):
                        region = "Africa"
                
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
    scraper = MassInstagramScraper()
    
    # Run all methods
    posts = scraper.run_all_methods()
    
    if posts:
        print(f"\n📋 Preview of {len(posts)} coffee posts:")
        for i, post in enumerate(posts[:5], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   📅 {post['date'][:10]}")
            if post['location'].get('name'):
                print(f"   📍 {post['location']['name']}")
            if post['notes']:
                print(f"   📝 {post['notes'][:80]}...")
        
        if len(posts) > 5:
            print(f"\n... and {len(posts) - 5} more posts")
        
        # Save all posts
        created = scraper.save_posts_to_jekyll(posts)
        print(f"\n💾 Created {created} Jekyll posts!")
        print("🔄 Check http://localhost:4000 to see your coffee tour!")
        
    else:
        print("\n❌ No coffee posts found")
        print("\nPossible reasons:")
        print("- Instagram is blocking all requests")
        print("- Profile is private") 
        print("- No posts have #worldcoffeetour hashtag")
        print("- Instagram changed their HTML structure")
        
        print("\nNext steps:")
        print("1. Try with selenium: python3 browser_scraper.py")
        print("2. Use Instagram Data Export (Settings → Privacy → Data Download)")
        print("3. Export posts manually using third-party tools")

if __name__ == "__main__":
    main()