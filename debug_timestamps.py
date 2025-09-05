#!/usr/bin/env python3
"""
Debug timestamp parsing in Instagram data
"""

import json
from datetime import datetime
from pathlib import Path

# Test the timestamp parsing logic from the processor
def test_timestamp_parsing():
    # Read the Instagram data
    with open('instagram-export-folder/your_instagram_activity/media/posts_1.json', 'r') as f:
        data = json.load(f)
    
    # Find the specific post we're testing
    test_title = "18 grams - cold brewed coffee #worldcoffeetour"
    
    for item in data:
        if isinstance(item, dict) and 'media' in item:
            for media_item in item['media']:
                if media_item.get('title') == test_title:
                    print(f"Found post: {test_title}")
                    print(f"Raw creation_timestamp: {media_item.get('creation_timestamp')}")
                    
                    # Test the conversion logic from instagram_data_processor.py
                    timestamp = media_item.get('creation_timestamp')
                    
                    if timestamp:
                        if isinstance(timestamp, (int, float)):
                            date = datetime.fromtimestamp(timestamp).isoformat()
                            print(f"Converted to ISO: {date}")
                            print(f"Just the date: {date.split('T')[0]}")
                        else:
                            print(f"Timestamp is not int/float: {type(timestamp)}")
                    else:
                        print("No timestamp found - would use current date")
                        print(f"Current date: {datetime.now().isoformat()}")
                    
                    return

if __name__ == "__main__":
    test_timestamp_parsing()