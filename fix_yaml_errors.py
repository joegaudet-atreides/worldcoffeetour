#!/usr/bin/env python3
"""
Fix YAML control character errors in posts
"""

import re
from pathlib import Path

def fix_control_characters():
    posts_with_errors = [
        "2024-01-17-last-coffee-post-from-tokyo-am-post_1756817250.md",
        "2024-12-21-i-don-t-know-how-i-will-go-bac-post_1756817250.md", 
        "2024-11-16-second-last-day-in-to-before-i-post_1756817250.md"
    ]
    
    for filename in posts_with_errors:
        filepath = Path("_coffee_posts") / filename
        if not filepath.exists():
            print(f"❌ File not found: {filename}")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove/replace problematic characters
        # Replace train emoji with "train"
        content = content.replace('ð', 'train')
        
        # Replace other problematic characters  
        content = content.replace("don-'t", "don't")
        content = content.replace("it-'s", "it's")
        content = content.replace('life-¦', 'life')
        content = content.replace('found-¦.', 'found.')
        
        # Remove any remaining control characters except newline and tab
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"  ✅ Fixed: {filename}")

if __name__ == "__main__":
    print("🔧 Fixing YAML control character errors...")
    fix_control_characters()