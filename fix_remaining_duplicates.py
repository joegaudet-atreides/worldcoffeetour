#!/usr/bin/env python3
"""
Fix remaining duplicate cafe names in the database
"""

from coffee_db import CoffeeDatabase
import collections
from datetime import datetime

def fix_remaining_duplicates():
    db = CoffeeDatabase()
    posts = db.get_all_posts()
    
    # Group by cafe_name
    cafe_names = {}
    for post in posts:
        name = post.get('cafe_name', post.get('title', 'Unknown'))
        if name not in cafe_names:
            cafe_names[name] = []
        cafe_names[name].append(post)
    
    fixed_count = 0
    
    for name, post_list in cafe_names.items():
        if len(post_list) > 1:
            print(f'\nFixing duplicates for: {name} ({len(post_list)} posts)')
            
            # Sort by date to keep consistent ordering
            post_list.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            for idx, post in enumerate(post_list):
                post_id = post['id']
                date = post.get('date', 'Unknown')
                city = post.get('city', 'Unknown')
                country = post.get('country', 'Unknown')
                notes = post.get('notes', '')
                
                # Create unique name based on the generic pattern
                if name == 'Coffee in Unknown':
                    # Use date and ID for uniqueness
                    if date != 'Unknown':
                        new_name = f"Coffee Stop - {date}"
                    else:
                        new_name = f"Coffee Post #{post_id}"
                
                elif name == 'worldcoffee' or name.startswith('#worldcoffee'):
                    # Use location or date
                    if city != 'Unknown':
                        new_name = f"Coffee in {city}"
                    elif country != 'Unknown':
                        new_name = f"Coffee in {country}"
                    elif date != 'Unknown':
                        new_name = f"Coffee Stop - {date}"
                    else:
                        new_name = f"Coffee Post #{post_id}"
                
                elif name == 'spot near our hotel #worldcoffee':
                    # Differentiate by location
                    if city != 'Unknown':
                        new_name = f"Hotel Coffee - {city}"
                    else:
                        new_name = f"Hotel Coffee #{idx+1}"
                
                elif name in ['Another stop', 'Another excellent stop', 'Another great stop', 'Another cool cafe']:
                    # Use location to differentiate
                    if city != 'Unknown':
                        new_name = f"{city} Coffee Stop"
                    elif country != 'Unknown':
                        new_name = f"{country} Coffee Stop"
                    elif date != 'Unknown':
                        new_name = f"Coffee Stop - {date}"
                    else:
                        new_name = f"Coffee Stop #{post_id}"
                
                else:
                    # For other duplicates, add a number suffix
                    if idx == 0:
                        continue  # Keep the first one as-is
                    new_name = f"{name} ({idx+1})"
                
                if 'new_name' in locals() and new_name != name:
                    print(f"  ID {post_id}: '{name}' -> '{new_name}'")
                    db.update_post(post_id, {'cafe_name': new_name})
                    fixed_count += 1
                    del new_name  # Clear for next iteration
    
    print(f"\nFixed {fixed_count} duplicate entries")
    
    # Verify no duplicates remain
    posts = db.get_all_posts()
    cafe_names = {}
    for post in posts:
        name = post.get('cafe_name', post.get('title', 'Unknown'))
        if name not in cafe_names:
            cafe_names[name] = []
        cafe_names[name].append(post)
    
    remaining_dups = sum(1 for posts in cafe_names.values() if len(posts) > 1)
    print(f"Remaining duplicates: {remaining_dups}")

if __name__ == "__main__":
    fix_remaining_duplicates()