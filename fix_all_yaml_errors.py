#!/usr/bin/env python3
"""
Fix YAML control character errors in ALL posts
"""

import re
from pathlib import Path

def fix_control_characters():
    posts_dir = Path("_coffee_posts")
    
    # Get all markdown files in the posts directory
    all_posts = list(posts_dir.glob("*.md"))
    fixed_count = 0
    
    for filepath in all_posts:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply the same fixes as the clean_text function
            replacements = {
                'ð': 'train',  # Train emoji that gets corrupted
                'life-¦': 'life',
                'found-¦.': 'found.',
                'found-¦': 'found',
                "don-'t": "don't",
                "it-'s": "it's"
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            # Remove any remaining control characters except newline and tab
            content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', content)
            
            # Only write if content changed
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed: {filepath.name}")
                fixed_count += 1
                
        except Exception as e:
            print(f"  ❌ Error processing {filepath.name}: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == "__main__":
    print("🔧 Fixing YAML control character errors in ALL posts...")
    fix_control_characters()