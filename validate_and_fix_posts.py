#!/usr/bin/env python3
"""
Comprehensive validation and fixing script for Jekyll coffee posts
"""

import os
import re
import yaml
from pathlib import Path

def yaml_safe_string(text):
    """Make a string safe for YAML by properly escaping it"""
    if not text:
        return '""'
    
    text = str(text).strip()
    
    # Characters that require quoting in YAML
    needs_quoting = any([
        text.startswith(('%', '@', '`', '|', '>', '#', '-', '?', ':', '[', '{', ']', '}', ',', '&', '*', '!', '\'', '"')),
        text.endswith(':'),
        ':' in text,
        '\n' in text,
        '"' in text,
        "'" in text,
        text in ['true', 'false', 'null', 'yes', 'no', 'on', 'off'],
        text.replace('.', '').replace('-', '').isdigit(),
        text.startswith(' ') or text.endswith(' '),
    ])
    
    if needs_quoting:
        # Escape internal quotes and wrap in double quotes
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    
    return text

def validate_and_fix_post(file_path):
    """Validate and fix a single post file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading file: {e}"
    
    # Check basic structure
    if not content.startswith('---\n'):
        return False, "Missing YAML front matter start"
    
    # Find the end of front matter
    end_pos = content.find('\n---\n', 4)
    if end_pos == -1:
        return False, "Missing YAML front matter end"
    
    front_matter_text = content[4:end_pos]
    body = content[end_pos + 5:]
    
    # Parse front matter manually
    front_matter = {}
    errors = []
    
    for line_num, line in enumerate(front_matter_text.split('\n'), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if ':' not in line:
            continue
            
        try:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove existing quotes if present
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Convert types
            if value.lower() == 'null' or value == '':
                front_matter[key] = None
            elif value.lower() in ['true', 'false']:
                front_matter[key] = value.lower() == 'true'
            elif value.replace('.', '').replace('-', '').isdigit():
                if '.' in value:
                    front_matter[key] = float(value)
                else:
                    front_matter[key] = int(value)
            else:
                front_matter[key] = value
                
        except ValueError as e:
            errors.append(f"Line {line_num}: {e}")
            continue
    
    if errors:
        return False, "; ".join(errors)
    
    # Regenerate the front matter with proper escaping
    new_lines = ['---']
    
    # Standard field order
    field_order = [
        'layout', 'title', 'date', 'city', 'country', 'continent',
        'latitude', 'longitude', 'cafe_name', 'rating', 'notes',
        'image_url', 'images', 'instagram_url', 'published'
    ]
    
    # Add ordered fields
    for field in field_order:
        if field in front_matter and front_matter[field] is not None:
            value = front_matter[field]
            if isinstance(value, str):
                new_lines.append(f'{field}: {yaml_safe_string(value)}')
            elif isinstance(value, bool):
                new_lines.append(f'{field}: {str(value).lower()}')
            elif isinstance(value, (int, float)):
                new_lines.append(f'{field}: {value}')
            elif isinstance(value, list):
                if value:  # Only add if list is not empty
                    new_lines.append(f'{field}:')
                    for item in value:
                        new_lines.append(f'  - {yaml_safe_string(str(item))}')
    
    # Add any remaining fields
    for key, value in front_matter.items():
        if key not in field_order and value is not None:
            if isinstance(value, str):
                new_lines.append(f'{key}: {yaml_safe_string(value)}')
            elif isinstance(value, bool):
                new_lines.append(f'{key}: {str(value).lower()}')
            elif isinstance(value, (int, float)):
                new_lines.append(f'{key}: {value}')
    
    new_lines.append('---')
    new_content = '\n'.join(new_lines) + '\n' + body
    
    # Test if the new YAML is valid
    try:
        yaml.safe_load('\n'.join(new_lines[1:-1]))  # Exclude the --- markers
    except yaml.YAMLError as e:
        return False, f"Generated invalid YAML: {e}"
    
    # Write the fixed content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, "Fixed"
    except Exception as e:
        return False, f"Error writing file: {e}"

def check_image_paths(file_path, front_matter_dict):
    """Check if image paths exist"""
    issues = []
    
    if 'image_url' in front_matter_dict and front_matter_dict['image_url']:
        image_path = Path(file_path.parent.parent / front_matter_dict['image_url'].lstrip('/'))
        if not image_path.exists():
            issues.append(f"Missing image: {front_matter_dict['image_url']}")
    
    if 'images' in front_matter_dict and isinstance(front_matter_dict['images'], list):
        for img in front_matter_dict['images']:
            image_path = Path(file_path.parent.parent / str(img).lstrip('/'))
            if not image_path.exists():
                issues.append(f"Missing image: {img}")
    
    return issues

def main():
    print("🔧 Validating and fixing Jekyll coffee posts...")
    
    posts_dir = Path("_coffee_posts")
    if not posts_dir.exists():
        print("❌ _coffee_posts directory not found!")
        return 1
    
    fixed_count = 0
    error_count = 0
    warning_count = 0
    image_issues = []
    
    for post_file in posts_dir.glob("*.md"):
        print(f"🔍 Checking {post_file.name}...")
        
        success, message = validate_and_fix_post(post_file)
        
        if success:
            if message == "Fixed":
                print(f"   ✅ Fixed YAML issues")
                fixed_count += 1
            
            # Check for image issues
            try:
                with open(post_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                end_pos = content.find('\n---\n', 4)
                if end_pos != -1:
                    front_matter_text = content[4:end_pos]
                    # Simple parse for image checking
                    front_matter = {}
                    for line in front_matter_text.split('\n'):
                        if ':' in line and not line.strip().startswith('#'):
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if value and value != 'null':
                                front_matter[key] = value
                    
                    img_issues = check_image_paths(post_file, front_matter)
                    if img_issues:
                        image_issues.extend([(post_file.name, issue) for issue in img_issues])
                        warning_count += 1
                        
            except Exception as e:
                print(f"   ⚠️  Could not check images: {e}")
                warning_count += 1
        else:
            print(f"   ❌ Error: {message}")
            error_count += 1
    
    print(f"\n📊 Summary:")
    print(f"✅ Fixed: {fixed_count} posts")
    print(f"❌ Errors: {error_count} posts")
    print(f"⚠️  Warnings: {warning_count} posts")
    
    if image_issues:
        print(f"\n🖼️  Image Issues ({len(image_issues)}):")
        for post_name, issue in image_issues[:10]:  # Show first 10
            print(f"   {post_name}: {issue}")
        if len(image_issues) > 10:
            print(f"   ... and {len(image_issues) - 10} more")
    
    return error_count

if __name__ == "__main__":
    exit(main())