#!/usr/bin/env python3
"""
Advanced Instagram Scraper using Scrapfly techniques
Based on: https://scrapfly.io/blog/posts/how-to-scrape-instagram
"""

import requests
import json
import re
import time
import base64
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

class ScrapflyInstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        self.posts_found = []
        
        # Advanced anti-detection headers
        self.setup_anti_detection()

    def setup_anti_detection(self):
        """Setup advanced anti-detection measures"""
        # Use mobile user agents (Instagram is less restrictive on mobile)
        mobile_user_agents = [
            'Instagram 219.0.0.12.117 Android',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1 Instagram 196.0.0.29.118',
            'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(mobile_user_agents),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Instagram-AJAX': '1',
        })

    def get_instagram_web_api_data(self, username):
        """Method 1: Use Instagram's internal web API endpoints"""
        print(f"🔍 Trying Instagram Web API for @{username}...")
        
        try:
            # First get the main page to extract necessary tokens and IDs
            main_url = f"https://www.instagram.com/{username}/"
            response = self.session.get(main_url)
            
            if response.status_code != 200:
                print(f"   Failed to access profile: {response.status_code}")
                return []
            
            # Extract user ID and other data
            html = response.text
            
            # Method 1a: Extract from script tags
            user_data = self.extract_user_data_from_html(html)
            if not user_data:
                print("   Could not extract user data")
                return []
            
            user_id = user_data.get('id')
            if not user_id:
                print("   Could not find user ID")
                return []
            
            print(f"   Found user ID: {user_id}")
            
            # Method 1b: Use GraphQL API
            posts = self.scrape_with_graphql_api(user_id, html)
            return posts
            
        except Exception as e:
            print(f"   Error: {e}")
            return []

    def extract_user_data_from_html(self, html):
        """Extract user data from HTML using multiple patterns"""
        
        # Pattern 1: window._sharedData
        shared_data_match = re.search(r'window\._sharedData\s*=\s*({.*?});', html, re.DOTALL)
        if shared_data_match:
            try:
                shared_data = json.loads(shared_data_match.group(1))
                profile_page = shared_data.get('entry_data', {}).get('ProfilePage', [])
                if profile_page:
                    user_data = profile_page[0].get('graphql', {}).get('user', {})
                    if user_data:
                        return user_data
            except:
                pass
        
        # Pattern 2: Modern React structure
        script_matches = re.findall(r'<script[^>]*>(.+?)</script>', html, re.DOTALL)
        for script in script_matches:
            # Look for user ID patterns
            user_id_match = re.search(r'"profilePage_(\d+)"', script)
            if user_id_match:
                return {'id': user_id_match.group(1)}
            
            # Look for JSON data with user info
            json_match = re.search(r'({[^{}]*"username"[^{}]*"id"[^{}]*})', script)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    if 'id' in data:
                        return data
                except:
                    pass
        
        return {}

    def scrape_with_graphql_api(self, user_id, html):
        """Use Instagram's GraphQL API to get posts"""
        print("   Using GraphQL API...")
        
        try:
            # Extract necessary tokens from HTML
            csrf_token = self.extract_csrf_token(html)
            if not csrf_token:
                print("   Could not find CSRF token")
                return []
            
            # Update headers with tokens
            self.session.headers.update({
                'X-CSRFToken': csrf_token,
                'X-Instagram-AJAX': '1',
                'Referer': f'https://www.instagram.com/',
            })
            
            # GraphQL query hash for user media (this may need updating)
            query_hashes = [
                'e769aa130647d2354c40ea6a439bfc08',  # User posts
                'f2405b236d85e8296cf30347c9f08c2a',  # Alternative
                '58b6785bea111c67129decbe6a448951',  # Another alternative
            ]
            
            all_posts = []
            
            for query_hash in query_hashes:
                try:
                    # Initial request
                    variables = {
                        "id": user_id,
                        "first": 50
                    }
                    
                    url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables, separators=(',', ':'))}"
                    
                    response = self.session.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        posts = self.parse_graphql_response(data)
                        
                        if posts:
                            print(f"   ✅ Found {len(posts)} posts with query hash {query_hash}")
                            all_posts.extend(posts)
                            
                            # Try to get more pages
                            more_posts = self.paginate_graphql_posts(data, user_id, query_hash)
                            all_posts.extend(more_posts)
                            break
                        else:
                            print(f"   No posts found with query hash {query_hash}")
                    else:
                        print(f"   GraphQL request failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"   Error with query hash {query_hash}: {e}")
                    continue
                
                time.sleep(1)  # Rate limiting
            
            return all_posts
            
        except Exception as e:
            print(f"   GraphQL error: {e}")
            return []

    def extract_csrf_token(self, html):
        """Extract CSRF token from HTML"""
        patterns = [
            r'"csrf_token":"([^"]*)"',
            r'csrftoken["\s]*:["\s]*([^"]*)',
            r'name="csrfmiddlewaretoken"\s+value="([^"]*)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return None

    def parse_graphql_response(self, data):
        """Parse GraphQL response to extract posts"""
        posts = []
        
        try:
            # Different possible paths in GraphQL response
            possible_paths = [
                ['data', 'user', 'edge_owner_to_timeline_media', 'edges'],
                ['data', 'hashtag', 'edge_hashtag_to_media', 'edges'],
                ['data', 'shortcode_media'],
            ]
            
            edges = None
            for path in possible_paths:
                current = data
                try:
                    for key in path:
                        current = current[key]
                    
                    if isinstance(current, list):
                        edges = current
                        break
                    elif isinstance(current, dict) and 'edges' in current:
                        edges = current['edges']
                        break
                        
                except (KeyError, TypeError):
                    continue
            
            if not edges:
                return []
            
            for edge in edges:
                node = edge.get('node', {})
                
                # Extract caption
                caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                caption = caption_edges[0]['node']['text'] if caption_edges else ""
                
                # Only process coffee posts
                if '#worldcoffeetour' not in caption.lower():
                    continue
                
                post_data = self.format_post_from_graphql_node(node, caption)
                if post_data:
                    posts.append(post_data)
                    
        except Exception as e:
            print(f"   Error parsing GraphQL response: {e}")
        
        return posts

    def paginate_graphql_posts(self, initial_data, user_id, query_hash, max_pages=10):
        """Get more posts using pagination"""
        posts = []
        
        try:
            # Extract pagination info
            page_info = None
            possible_paths = [
                ['data', 'user', 'edge_owner_to_timeline_media', 'page_info'],
                ['data', 'hashtag', 'edge_hashtag_to_media', 'page_info'],
            ]
            
            for path in possible_paths:
                current = initial_data
                try:
                    for key in path:
                        current = current[key]
                    page_info = current
                    break
                except (KeyError, TypeError):
                    continue
            
            if not page_info or not page_info.get('has_next_page'):
                return []
            
            end_cursor = page_info.get('end_cursor')
            
            for page in range(max_pages):
                if not end_cursor:
                    break
                
                variables = {
                    "id": user_id,
                    "first": 50,
                    "after": end_cursor
                }
                
                url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables, separators=(',', ':'))}"
                
                time.sleep(random.uniform(1, 3))  # Random delay
                
                response = self.session.get(url)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                page_posts = self.parse_graphql_response(data)
                
                if not page_posts:
                    break
                
                posts.extend(page_posts)
                print(f"   📄 Page {page + 1}: Found {len(page_posts)} more posts")
                
                # Update pagination
                for path in possible_paths:
                    current = data
                    try:
                        for key in path:
                            current = current[key]
                        
                        if not current.get('has_next_page'):
                            end_cursor = None
                            break
                        
                        end_cursor = current.get('end_cursor')
                        break
                    except (KeyError, TypeError):
                        continue
                
                if not end_cursor:
                    break
            
        except Exception as e:
            print(f"   Pagination error: {e}")
        
        return posts

    def format_post_from_graphql_node(self, node, caption):
        """Format post from GraphQL node"""
        try:
            shortcode = node.get('shortcode', '')
            timestamp = node.get('taken_at_timestamp', 0)
            image_url = node.get('display_url', '')
            
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
            print(f"   Error formatting post: {e}")
            return None

    def scrape_hashtag_feed(self, hashtag="worldcoffeetour"):
        """Method 2: Scrape hashtag feed directly"""
        print(f"🔍 Scraping #{hashtag} hashtag feed...")
        
        try:
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            response = self.session.get(url)
            
            if response.status_code != 200:
                print(f"   Failed: HTTP {response.status_code}")
                return []
            
            # Extract hashtag data
            html = response.text
            posts = self.extract_hashtag_posts_from_html(html)
            
            if posts:
                print(f"   ✅ Found {len(posts)} posts from hashtag")
                
                # Try to get more posts using GraphQL
                more_posts = self.scrape_hashtag_with_graphql(hashtag, html)
                posts.extend(more_posts)
            
            return posts
            
        except Exception as e:
            print(f"   Error: {e}")
            return []

    def extract_hashtag_posts_from_html(self, html):
        """Extract posts from hashtag page HTML"""
        posts = []
        
        # Look for shared data
        shared_data_match = re.search(r'window\._sharedData\s*=\s*({.*?});', html, re.DOTALL)
        if shared_data_match:
            try:
                data = json.loads(shared_data_match.group(1))
                tag_page = data.get('entry_data', {}).get('TagPage', [])
                
                if tag_page:
                    hashtag_data = tag_page[0].get('graphql', {}).get('hashtag', {})
                    media_edges = hashtag_data.get('edge_hashtag_to_media', {}).get('edges', [])
                    
                    for edge in media_edges:
                        node = edge.get('node', {})
                        caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                        caption = caption_edges[0]['node']['text'] if caption_edges else ""
                        
                        post_data = self.format_post_from_graphql_node(node, caption)
                        if post_data:
                            posts.append(post_data)
                            
            except json.JSONDecodeError:
                pass
        
        return posts

    def scrape_hashtag_with_graphql(self, hashtag, html):
        """Get more hashtag posts using GraphQL"""
        print("   Getting more hashtag posts...")
        
        try:
            csrf_token = self.extract_csrf_token(html)
            if not csrf_token:
                return []
            
            # Update headers
            self.session.headers.update({
                'X-CSRFToken': csrf_token,
                'Referer': f'https://www.instagram.com/explore/tags/{hashtag}/',
            })
            
            # Hashtag GraphQL query hash
            query_hash = "f92f56d47dc7a55b606908374b43a314"  # May need updating
            
            variables = {
                "tag_name": hashtag,
                "first": 50
            }
            
            url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables, separators=(',', ':'))}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                posts = self.parse_graphql_response(data)
                print(f"   ✅ Found {len(posts)} more posts via GraphQL")
                return posts
            else:
                print(f"   GraphQL request failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   Error: {e}")
            return []

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
                        'Asia': ['japan', 'tokyo', 'kyoto', 'asia', 'china', 'korea', 'thailand', 'vietnam', 'singapore'],
                        'Europe': ['france', 'italy', 'spain', 'europe', 'paris', 'rome', 'london', 'berlin', 'amsterdam'],
                        'Americas': ['usa', 'america', 'canada', 'mexico', 'brazil', 'new york', 'portland', 'seattle'],
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
☕ Advanced Instagram Scraper (Scrapfly Method)
===============================================
Using advanced techniques from scrapfly.io
""")
    
    username = "joegaudet"
    scraper = ScrapflyInstagramScraper()
    
    all_posts = []
    
    # Method 1: Profile scraping with GraphQL
    profile_posts = scraper.get_instagram_web_api_data(username)
    if profile_posts:
        all_posts.extend(profile_posts)
    
    # Method 2: Hashtag scraping
    hashtag_posts = scraper.scrape_hashtag_feed("worldcoffeetour")
    if hashtag_posts:
        all_posts.extend(hashtag_posts)
    
    # Remove duplicates
    seen_shortcodes = set()
    unique_posts = []
    for post in all_posts:
        shortcode = post.get('shortcode', '')
        if shortcode and shortcode not in seen_shortcodes:
            seen_shortcodes.add(shortcode)
            unique_posts.append(post)
    
    if unique_posts:
        print(f"\n🎉 Found {len(unique_posts)} unique coffee posts!")
        
        # Show preview
        for i, post in enumerate(unique_posts[:5], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   📅 {post['date'][:10]}")
            if post['location'].get('name'):
                print(f"   📍 {post['location']['name']}")
            if post['notes']:
                print(f"   📝 {post['notes'][:80]}...")
        
        if len(unique_posts) > 5:
            print(f"\n... and {len(unique_posts) - 5} more posts")
        
        # Save all posts
        created = scraper.save_posts_to_jekyll(unique_posts)
        print(f"\n💾 Created {created} Jekyll posts!")
        print("🔄 Check http://localhost:4000 to see your complete coffee tour!")
        
    else:
        print("\n❌ No posts found")
        print("\nThis could mean:")
        print("- Instagram has updated their structure again")
        print("- Your posts don't have #worldcoffeetour hashtag")
        print("- Profile is private")
        print("- Rate limiting is in effect")
        
        print("\nFallback options:")
        print("1. Try the Instagram Data Export method:")
        print("   python3 instagram_data_processor.py")
        print("2. Try the browser automation method:")
        print("   python3 browser_scraper.py")

if __name__ == "__main__":
    main()