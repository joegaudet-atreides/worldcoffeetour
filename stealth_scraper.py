#!/usr/bin/env python3
"""
Stealth Instagram Scraper using undetected-chromedriver
This is the most effective method to bypass Instagram's anti-bot detection
"""

import undetected_chromedriver as uc
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class StealthInstagramScraper:
    def __init__(self):
        self.driver = None
        self.posts_found = []

    def setup_driver(self):
        """Setup undetected Chrome driver"""
        try:
            options = uc.ChromeOptions()
            
            # Stealth options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Faster loading
            options.add_argument("--disable-javascript")  # We'll enable selectively
            
            # Mobile user agent for less detection
            options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1")
            
            # Window size
            options.add_argument("--window-size=375,812")  # iPhone size
            
            # Create undetected driver
            self.driver = uc.Chrome(options=options)
            
            # Additional stealth measures
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up stealth driver: {e}")
            return False

    def scrape_profile_completely(self, username="joegaudet"):
        """Scrape complete profile using stealth browser"""
        print(f"🕵️ Stealth scraping @{username} for #worldcoffeetour...")
        
        try:
            # Navigate to profile
            profile_url = f"https://www.instagram.com/{username}/"
            print(f"   Loading {profile_url}")
            self.driver.get(profile_url)
            
            # Wait for page to load
            time.sleep(random.uniform(3, 5))
            
            # Handle login popup if it appears
            self.dismiss_popups()
            
            # Scroll to load all posts
            total_posts = self.scroll_and_load_all_posts()
            print(f"   Loaded {total_posts} total posts")
            
            # Extract all post links
            post_links = self.extract_all_post_links()
            print(f"   Found {len(post_links)} post links")
            
            # Process each post to check for coffee hashtag
            coffee_posts = []
            for i, link in enumerate(post_links, 1):
                print(f"   Processing post {i}/{len(post_links)}...")
                
                post_data = self.scrape_individual_post(link)
                
                if post_data and '#worldcoffeetour' in post_data.get('caption', '').lower():
                    coffee_posts.append(post_data)
                    print(f"   ✅ Coffee post found: {post_data['title'][:30]}...")
                else:
                    print(f"   ⏭️  Not a coffee post")
                
                # Random delay to avoid detection
                time.sleep(random.uniform(1, 3))
            
            return coffee_posts
            
        except Exception as e:
            print(f"   ❌ Error during scraping: {e}")
            return []

    def dismiss_popups(self):
        """Dismiss login and other popups"""
        try:
            # Common popup selectors
            popup_selectors = [
                "button:contains('Not Now')",
                "button:contains('Maybe Later')",
                "[aria-label='Close']",
                ".piCiT",  # Close button
            ]
            
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        elements[0].click()
                        time.sleep(1)
                except:
                    pass
                    
        except Exception as e:
            print(f"   Popup handling error: {e}")

    def scroll_and_load_all_posts(self):
        """Scroll down to load all posts on profile"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            posts_loaded = 0
            
            while True:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content
                time.sleep(random.uniform(2, 4))
                
                # Count posts
                current_posts = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']"))
                
                if current_posts > posts_loaded:
                    posts_loaded = current_posts
                    print(f"   Loaded {posts_loaded} posts...")
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Try scrolling a bit more in case of lazy loading
                    for _ in range(3):
                        self.driver.execute_script("window.scrollBy(0, 500);")
                        time.sleep(1)
                    
                    final_height = self.driver.execute_script("return document.body.scrollHeight")
                    if final_height == last_height:
                        break
                
                last_height = new_height
            
            return posts_loaded
            
        except Exception as e:
            print(f"   Scrolling error: {e}")
            return 0

    def extract_all_post_links(self):
        """Extract all post links from loaded page"""
        try:
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
            
            links = []
            for element in post_elements:
                href = element.get_attribute('href')
                if href and href not in links:
                    links.append(href)
            
            return links
            
        except Exception as e:
            print(f"   Link extraction error: {e}")
            return []

    def scrape_individual_post(self, post_url):
        """Scrape individual post data"""
        try:
            # Navigate to post
            self.driver.get(post_url)
            time.sleep(random.uniform(2, 4))
            
            # Extract post data from page source
            page_source = self.driver.page_source
            
            # Extract data using multiple methods
            post_data = self.extract_post_data_from_source(page_source, post_url)
            
            return post_data
            
        except Exception as e:
            print(f"   Error scraping {post_url}: {e}")
            return None

    def extract_post_data_from_source(self, html, post_url):
        """Extract post data from HTML source"""
        try:
            # Extract shortcode from URL
            shortcode_match = re.search(r'/p/([A-Za-z0-9_-]+)/', post_url)
            shortcode = shortcode_match.group(1) if shortcode_match else ""
            
            # Method 1: Try to extract from JSON data in HTML
            json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    post_data = self.parse_post_from_shared_data(data, shortcode)
                    if post_data:
                        post_data['instagram_url'] = post_url
                        return post_data
                except:
                    pass
            
            # Method 2: Extract from meta tags and HTML structure
            caption = self.extract_caption_from_html(html)
            image_url = self.extract_image_from_html(html)
            
            if not caption:
                return None
            
            # Create title from caption
            lines = [line.strip() for line in caption.split('\n') if line.strip()]
            title = ""
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
                'date': datetime.now().isoformat(),  # We'll use current date since it's hard to extract
                'image_url': image_url,
                'location': {},
                'instagram_url': post_url
            }
            
        except Exception as e:
            print(f"   Data extraction error: {e}")
            return None

    def parse_post_from_shared_data(self, data, shortcode):
        """Parse post from window._sharedData"""
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
            print(f"   Shared data parsing error: {e}")
            return None

    def extract_caption_from_html(self, html):
        """Extract caption from HTML using various methods"""
        
        # Method 1: Meta description
        meta_match = re.search(r'<meta property="og:description" content="([^"]*)"', html)
        if meta_match:
            return meta_match.group(1)
        
        # Method 2: JSON-LD structured data
        json_ld_match = re.search(r'<script type="application/ld\+json">({.+?})</script>', html, re.DOTALL)
        if json_ld_match:
            try:
                data = json.loads(json_ld_match.group(1))
                if 'description' in data:
                    return data['description']
            except:
                pass
        
        # Method 3: Look for caption in HTML structure
        caption_patterns = [
            r'"caption":"([^"]*)"',
            r'"text":"([^"]*)"',
            r'<meta name="description" content="([^"]*)"'
        ]
        
        for pattern in caption_patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return ""

    def extract_image_from_html(self, html):
        """Extract image URL from HTML"""
        
        # Method 1: Open Graph image
        og_match = re.search(r'<meta property="og:image" content="([^"]*)"', html)
        if og_match:
            return og_match.group(1)
        
        # Method 2: Display URL in JSON
        display_match = re.search(r'"display_url":"([^"]*)"', html)
        if display_match:
            return display_match.group(1)
        
        return ""

    def close_driver(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

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
                        'Asia': ['japan', 'tokyo', 'kyoto', 'asia', 'china', 'korea', 'thailand', 'vietnam'],
                        'Europe': ['france', 'italy', 'spain', 'europe', 'paris', 'rome', 'london', 'berlin'],
                        'Americas': ['usa', 'america', 'canada', 'mexico', 'brazil', 'new york', 'portland'],
                        'Oceania': ['australia', 'new zealand', 'melbourne', 'sydney'],
                        'Africa': ['africa', 'south africa', 'morocco', 'cape town']
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
☕ Stealth Instagram Scraper
============================
Using undetected-chromedriver for maximum stealth
This method has the highest success rate!
""")
    
    scraper = StealthInstagramScraper()
    
    try:
        print("🚀 Setting up stealth browser...")
        if not scraper.setup_driver():
            return
        
        print("✅ Stealth browser ready!")
        
        # Scrape all posts
        posts = scraper.scrape_profile_completely()
        
        if posts:
            print(f"\n🎉 Found {len(posts)} coffee tour posts!")
            
            # Show preview
            for i, post in enumerate(posts[:3], 1):
                print(f"\n{i}. {post['title']}")
                if post['location'].get('name'):
                    print(f"   📍 {post['location']['name']}")
                if post['notes']:
                    print(f"   📝 {post['notes'][:80]}...")
            
            if len(posts) > 3:
                print(f"\n... and {len(posts) - 3} more posts")
            
            # Save posts
            created = scraper.save_posts_to_jekyll(posts)
            print(f"\n💾 Created {created} Jekyll posts!")
            print("🔄 Check http://localhost:4000 to see your complete coffee tour!")
            
        else:
            print("\n❌ No coffee posts found")
            print("This could mean:")
            print("- No posts have #worldcoffeetour hashtag")
            print("- Profile is private")
            print("- Instagram's structure changed")
            print("- Detection systems are very aggressive")
        
    finally:
        print("\n🔒 Closing stealth browser...")
        scraper.close_driver()

if __name__ == "__main__":
    main()