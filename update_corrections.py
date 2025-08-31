#!/usr/bin/env python3
"""
Update post-corrections.json with corrections from admin interface
"""

import json
import sys
from pathlib import Path

def update_corrections(new_corrections_json):
    """Update corrections file with new corrections"""
    try:
        new_corrections = json.loads(new_corrections_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    
    # Load existing corrections file
    corrections_file = Path("post-corrections.json")
    
    if corrections_file.exists():
        with open(corrections_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = {
            "_readme": "This file contains manual corrections for coffee posts. The processing script will apply these corrections and not overwrite them.",
            "_format": "The keys are post URLs (without leading/trailing slashes), values are correction objects with any post fields to override."
        }
    
    # Count new and updated corrections
    new_count = 0
    updated_count = 0
    
    # Merge corrections
    for key, value in new_corrections.items():
        if not key.startswith('_'):
            if key not in existing_data:
                new_count += 1
            else:
                updated_count += 1
            existing_data[key] = value
    
    # Save back to file
    with open(corrections_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully updated post-corrections.json")
    print(f"   📝 {new_count} new corrections added")
    print(f"   🔄 {updated_count} existing corrections updated")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("""
☕ Update Post Corrections
=========================

Usage: python3 update_corrections.py '<json_string>'

Example:
python3 update_corrections.py '{"coffee/2024-11-16-example-post": {"cafe_name": "New Cafe Name", "city": "Corrected City"}}'

Or from admin interface:
1. Go to /admin.html
2. Make your edits
3. Click "Export Corrections" 
4. Copy the JSON from the downloaded file
5. Run: python3 update_corrections.py '<paste_json_here>'
""")
        return
    
    corrections_json = sys.argv[1]
    
    if update_corrections(corrections_json):
        print(f"""
🎉 Corrections Updated Successfully!

Next steps:
1. Run: python3 apply_corrections.py
2. Or run: python3 process_export_enhanced.py (full reprocess)
3. Check changes: bundle exec jekyll serve
""")

if __name__ == "__main__":
    main()