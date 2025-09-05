#!/usr/bin/env python3
"""
Fix posts with duplicate front matter sections
"""

import os
import re
from pathlib import Path

def fix_duplicate_frontmatter(file_path):
    """Fix a file with duplicate front matter"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False
    
    # Count YAML delimiters
    delimiter_count = content.count('---')
    
    if delimiter_count <= 2:
        return True  # Already good
    
    # Split on --- boundaries
    parts = content.split('---')
    
    if len(parts) < 4:
        return True  # Can't fix this one
    
    # The structure should be: [empty] [front_matter_1] [maybe_body] [front_matter_2] [body]
    # We want to merge the two front matter sections and keep the final body
    
    # Find the last meaningful section (the body)
    body = parts[-1] if len(parts) % 2 == 1 else ""
    
    # Extract front matter sections
    front_matter_sections = []
    for i in range(1, len(parts), 2):  # Odd indices are front matter
        section = parts[i].strip()
        if section and not section.isspace():
            front_matter_sections.append(section)
    
    if not front_matter_sections:
        print(f"❌ No valid front matter found in {file_path}")
        return False
    
    # Parse all front matter sections and merge them
    merged_fm = {}
    
    for section in front_matter_sections:
        for line in section.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                try:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Skip empty values unless it's the last section
                    if value and value not in ['null', 'None', '""', "''", 'Unknown']:
                        merged_fm[key] = value
                    elif key not in merged_fm:
                        merged_fm[key] = value
                except ValueError:
                    continue
    
    # Rebuild the file with single front matter
    new_content = "---\n"
    
    # Preferred order for fields
    field_order = [
        'layout', 'title', 'date', 'city', 'country', 'continent',
        'latitude', 'longitude', 'cafe_name', 'rating', 'notes',
        'image_url', 'images', 'instagram_url', 'published'
    ]
    
    # Add ordered fields first
    for field in field_order:
        if field in merged_fm:
            new_content += f"{field}: {merged_fm[field]}\n"
            del merged_fm[field]
    
    # Add any remaining fields
    for key, value in merged_fm.items():
        new_content += f"{key}: {value}\n"
    
    new_content += "---\n" + body
    
    # Write the fixed file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Fixed {file_path.name}")
        return True
    except Exception as e:
        print(f"❌ Error writing {file_path}: {e}")
        return False

def main():
    print("🔧 Fixing posts with duplicate front matter...")
    
    posts_dir = Path("_coffee_posts")
    if not posts_dir.exists():
        print("❌ _coffee_posts directory not found!")
        return 1
    
    fixed_count = 0
    error_count = 0
    
    # Find all posts with too many delimiters
    for post_file in posts_dir.glob("*.md"):
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            delimiter_count = content.count('---')
            if delimiter_count > 2:
                print(f"🔍 Found {delimiter_count} delimiters in {post_file.name}")
                if fix_duplicate_frontmatter(post_file):
                    fixed_count += 1
                else:
                    error_count += 1
                    
        except Exception as e:
            print(f"❌ Error processing {post_file}: {e}")
            error_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")
    if error_count > 0:
        print(f"❌ {error_count} files had errors")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    exit(main())