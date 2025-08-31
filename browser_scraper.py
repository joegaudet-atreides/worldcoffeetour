#!/usr/bin/env python3
"""
Browser-based Instagram Scraper using Selenium
Most reliable method for scraping Instagram posts
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path

def install_selenium():
    """Install selenium and webdriver if not available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        return True
    except ImportError:
        print("📦 Installing selenium...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        
        print("📦 You also need ChromeDriver:")
        print("   - macOS: brew install chromedriver")
        print("   - Or download from: https://chromedriver.chromium.org/")
        return False

class BrowserInstagramScraper:
    def __init__(self):
        self.driver = None
    
    def setup_browser(self, headless=True):
        """Setup Chrome browser with options"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=options)
            return True
            
        except Exception as e:
            print(f"❌ Error setting up browser: {e}")
            print("\n💡 Make sure you have ChromeDriver installed:")
            print("   macOS: brew install chromedriver")
            print("   Linux: apt-get install chromium-chromedriver")
            print("   Windows: Download from https://chromedriver.chromium.org/")
            return False
    
    def scrape_profile_posts(self, username):
        """Scrape posts from Instagram profile"""
        if not self.driver:
            return []
        
        try:
            print(f"🔍 Loading @{username} profile...")
            self.driver.get(f"https://www.instagram.com/{username}/")
            
            # Wait for page to load
            time.sleep(3)
            
            # Scroll down to load more posts
            print("📜 Scrolling to load posts...")
            self.scroll_and_load_posts()
            
            # Extract post links
            post_links = self.extract_post_links()
            print(f"🔗 Found {len(post_links)} posts")
            
            # Filter and scrape coffee posts
            coffee_posts = []
            for i, link in enumerate(post_links, 1):
                print(f"📝 Processing post {i}/{len(post_links)}...")
                post_data = self.scrape_single_post(link)
                
                if post_data and '#worldcoffeetour' in post_data.get('caption', '').lower():
                    coffee_posts.append(post_data)
                    print(f"  ✅ Coffee post: {post_data['title']}")
                else:
                    print(f"  ⏭️  Not a coffee tour post")
                
                time.sleep(2)  # Rate limiting
            
            return coffee_posts
            
        except Exception as e:
            print(f"❌ Error scraping profile: {e}")
            return []
    
    def scroll_and_load_posts(self):
        """Scroll down to load more posts"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(5):  # Scroll 5 times to load more posts
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def extract_post_links(self):
        """Extract all post links from profile"""
        try:
            from selenium.webdriver.common.by import By
            
            # Find post links
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
            post_urls = []
            
            for link in links:
                href = link.get_attribute('href')
                if '/p/' in href and href not in post_urls:
                    post_urls.append(href)
            
            return post_urls[:50]  # Limit to first 50 posts
            
        except Exception as e:
            print(f"Error extracting links: {e}")
            return []
    
    def scrape_single_post(self, post_url):
        """Scrape data from a single post"""
        try:
            self.driver.get(post_url)
            time.sleep(2)
            
            # Extract post data from page source
            page_source = self.driver.page_source
            
            # Extract shortcode from URL
            shortcode_match = re.search(r'/p/([A-Za-z0-9_-]+)/', post_url)
            shortcode = shortcode_match.group(1) if shortcode_match else ""
            
            # Extract data using various methods
            post_data = self.extract_post_data_from_html(page_source, shortcode)
            
            if post_data:
                post_data['instagram_url'] = post_url
            
            return post_data
            
        except Exception as e:
            print(f"Error scraping post {post_url}: {e}")
            return None
    
    def extract_post_data_from_html(self, html, shortcode):
        """Extract post data from HTML"""
        try:
            # Method 1: Look for JSON data in script tags
            json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html)
            if json_match:
                data = json.loads(json_match.group(1))
                post_data = self.parse_json_data(data)
                if post_data:
                    return post_data
            
            # Method 2: Extract from meta tags and visible elements
            # Caption from meta description
            caption_match = re.search(r'<meta property="og:description" content="([^"]*)"', html)
            caption = caption_match.group(1) if caption_match else ""
            
            # Image from meta
            image_match = re.search(r'<meta property="og:image" content="([^"]*)"', html)
            image_url = image_match.group(1) if image_match else ""
            
            # Title from meta
            title_match = re.search(r'<meta property="og:title" content="([^"]*)"', html)
            title = title_match.group(1) if title_match else ""
            
            # Clean up title
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            if not title or len(title) < 10:
                # Extract from caption
                lines = [line.strip() for line in caption.split('\n') if line.strip()]
                for line in lines:
                    if not line.startswith('#') and not line.startswith('@') and len(line) > 10:
                        title = line[:60]
                        break
                if not title:
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
                'date': datetime.now().isoformat(),
                'image_url': image_url,
                'location': {},
            }
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            return None
    
    def parse_json_data(self, data):
        """Parse Instagram JSON data structure"""
        try:
            # Navigate the complex Instagram data structure
            post_page = data.get('entry_data', {}).get('PostPage', [])
            if not post_page:
                return None
            
            media = post_page[0].get('graphql', {}).get('shortcode_media', {})
            if not media:
                return None
            
            # Extract caption
            caption_edges = media.get('edge_media_to_caption', {}).get('edges', [])
            caption = caption_edges[0]['node']['text'] if caption_edges else ""
            
            # Extract other data
            shortcode = media.get('shortcode', '')
            timestamp = media.get('taken_at_timestamp', 0)
            image_url = media.get('display_url', '')
            
            # Location
            location_data = {}
            if media.get('location'):
                loc = media['location']
                location_data = {
                    'name': loc.get('name', ''),
                    'lat': loc.get('lat'),
                    'lng': loc.get('lng')
                }
            
            # Format title
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
            }
            
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return None
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
    
    def save_posts_to_jekyll(self, posts):
        """Save posts as Jekyll files"""
        if not posts:
            print("❌ No posts to save")
            return 0
        
        try:
            import sys
            sys.path.append('.')
            from fetch_instagram import create_jekyll_posts
            return create_jekyll_posts(posts)
        except ImportError:
            # Manual fallback
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
☕ Browser-based Instagram Scraper
==================================
Most reliable method using Selenium WebDriver

This opens a real browser to scrape your posts,
bypassing most anti-scraping measures.
""")
    
    # Check if selenium is available
    if not install_selenium():
        print("\n❌ Please install selenium and ChromeDriver first:")
        print("pip install selenium")
        print("brew install chromedriver  # macOS")
        return
    
    username = input("Instagram username [joegaudet]: ").strip() or "joegaudet"
    
    # Ask about browser mode
    headless = input("Run browser in background? (y/n) [y]: ").strip().lower() != 'n'
    
    scraper = BrowserInstagramScraper()
    
    try:
        print(f"\n🚀 Setting up browser...")
        if not scraper.setup_browser(headless=headless):
            return
        
        print(f"🔍 Scraping @{username} for #worldcoffeetour posts...")
        posts = scraper.scrape_profile_posts(username)
        
        if posts:
            print(f"\n🎉 Found {len(posts)} coffee posts!")
            
            # Preview
            for i, post in enumerate(posts[:3], 1):
                print(f"\n{i}. {post['title']}")
                print(f"   📅 {post['date'][:10]}")
                if post['location'].get('name'):
                    print(f"   📍 {post['location']['name']}")
                if post['notes']:
                    print(f"   📝 {post['notes'][:80]}...")
            
            if len(posts) > 3:
                print(f"\n... and {len(posts) - 3} more")
            
            # Save
            save = input(f"\n💾 Create {len(posts)} Jekyll posts? (y/n): ").strip().lower()
            if save == 'y':
                created = scraper.save_posts_to_jekyll(posts)
                print(f"\n✅ Created {created} Jekyll posts!")
                print("🔄 Check http://localhost:4000 to see your posts")
            
        else:
            print("\n❌ No coffee posts found")
            print("Make sure you have posts with #worldcoffeetour hashtag")
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()