#!/usr/bin/env python3
"""
DEPRECATED: Use update_corrections.py instead

Export corrections from admin interface localStorage to JSON file
This script is kept for backward compatibility
"""

import json
import sys

def main():
    print("⚠️  DEPRECATED: This script has been replaced by update_corrections.py")
    print("   Use: python3 update_corrections.py '<json_string>' instead")
    print()
    
    if len(sys.argv) != 2:
        print("Usage: python3 export_corrections.py <corrections_json_string>")
        print("Copy the localStorage corrections JSON from browser dev tools and paste as argument")
        return
    
    try:
        corrections_str = sys.argv[1]
        corrections = json.loads(corrections_str)
        
        # Load existing corrections file
        try:
            with open('post-corrections.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {
                "_readme": "This file contains manual corrections for coffee posts. The processing script will apply these corrections and not overwrite them.",
                "_format": "The keys are post URLs (without leading/trailing slashes), values are correction objects with any post fields to override."
            }
        
        # Merge corrections
        count = 0
        for key, value in corrections.items():
            if not key.startswith('_'):
                existing_data[key] = value
                count += 1
        
        # Save back to file
        with open('post-corrections.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {count} corrections to post-corrections.json")
        print(f"💡 Next: Run 'python3 apply_corrections.py' to apply them")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()