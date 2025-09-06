#!/usr/bin/env python3
"""
Fix YAML encoding issues in post files that are causing Jekyll build failures
"""

import os
import re
from pathlib import Path

def fix_yaml_string(text):
    """Fix YAML string by properly escaping special characters"""
    if not text:
        return text
    
    # Replace smart quotes and other problematic characters
    replacements = {
        'â': "'",  # Right single quotation mark
        'â': "'",  # Left single quotation mark  
        'â': '"',  # Left double quotation mark
        'â': '"',  # Right double quotation mark
        'â¦': '...',  # Horizontal ellipsis
        'â': '-',  # En dash
        'â': '--', # Em dash
        'Â': '',   # Non-breaking space artifacts
        'Ã¢': "'", # UTF-8 encoding artifacts
        'âs': "'s",  # Common 's pattern
        'donât': "don't",
        'canât': "can't", 
        'wonât': "won't",
        'itâs': "it's",
        'Iâm': "I'm",
        'weâre': "we're",
        'theyâre': "they're",
        'youâre': "you're",
        'wasnât': "wasn't",
        'werenât': "weren't",
        'isnât': "isn't",
        'arenât': "aren't",
        'hasnât': "hasn't",
        'havenât': "haven't",
        'didnât': "didn't",
        'couldnât': "couldn't",
        'shouldnât': "shouldn't",
        'wouldnât': "wouldn't"
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Also handle any other problematic UTF-8 sequences
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    return text

def fix_post_file(file_path):
    """Fix a single post file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into frontmatter and content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                post_content = parts[2] if len(parts) > 2 else ''
                
                # Fix the frontmatter
                lines = frontmatter.strip().split('\n')
                fixed_lines = []
                
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Clean up the value
                        if value and not value.startswith('"') and not value.startswith("'"):
                            # Fix special characters
                            value = fix_yaml_string(value)
                            # If the value contains special characters or spaces, quote it
                            if any(char in value for char in ['"', "'", ':', '[', ']', '{', '}', '&', '*', '#', '|', '>', '@', '`']) or value != value.strip():
                                # Escape existing quotes and wrap in quotes
                                value = '"' + value.replace('"', '\\"') + '"'
                        elif value.startswith('"') or value.startswith("'"):
                            # Already quoted, just fix the content
                            quote_char = value[0]
                            inner_value = value[1:-1]
                            inner_value = fix_yaml_string(inner_value)
                            if quote_char == '"':
                                inner_value = inner_value.replace('"', '\\"')
                            value = quote_char + inner_value + quote_char
                        
                        fixed_lines.append(f"{key}: {value}")
                    else:
                        fixed_lines.append(line)
                
                # Reconstruct the file
                fixed_frontmatter = '\n'.join(fixed_lines)
                fixed_content = f"---\n{fixed_frontmatter}\n---{post_content}"
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False
    
    return False

def main():
    """Fix all post files with YAML encoding issues"""
    posts_dir = Path('_coffee_posts')
    
    if not posts_dir.exists():
        print("No _coffee_posts directory found")
        return
    
    fixed_count = 0
    total_count = 0
    
    for post_file in posts_dir.glob('*.md'):
        total_count += 1
        if fix_post_file(post_file):
            fixed_count += 1
            print(f"Fixed: {post_file.name}")
    
    print(f"\nFixed {fixed_count} out of {total_count} post files")

if __name__ == "__main__":
    main()