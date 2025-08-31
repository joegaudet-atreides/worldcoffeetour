# Instagram Data Fetching Instructions

Due to Instagram's API restrictions, you'll need to manually fetch your World Coffee Tour posts. Here are the options:

## Option 1: Manual Data Entry
Create coffee post files in `_coffee_posts/` directory with the following format:

```yaml
---
layout: post
title: "Coffee in Paris"
date: 2024-01-15
city: "Paris"
country: "France"
region: "Europe"
latitude: 48.8566
longitude: 2.3522
cafe_name: "Café de Flore"
coffee_type: "Espresso"
rating: 5
notes: "Classic Parisian café experience with perfect espresso"
image_url: "[Instagram image URL]"
instagram_url: "[Instagram post URL]"
---
```

## Option 2: Instagram Basic Display API
1. Create a Facebook Developer account
2. Create an app with Instagram Basic Display
3. Get access token for your account
4. Use the token to fetch posts with #worldcoffeetour hashtag

## Option 3: Third-party Tools
Use tools like:
- Zapier to export Instagram posts to JSON
- IFTTT to save posts to a spreadsheet
- Instagram export tools to get your data

## Sample Data Structure
Posts should be saved in `_data/coffee_posts.json`:

```json
[
  {
    "id": "1",
    "title": "Morning Brew in Tokyo",
    "date": "2024-01-10",
    "city": "Tokyo",
    "country": "Japan",
    "region": "Asia",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "cafe_name": "Blue Bottle Coffee",
    "coffee_type": "Pour Over",
    "rating": 5,
    "notes": "Exceptional single-origin Ethiopian beans",
    "image_url": "https://example.com/image.jpg",
    "instagram_url": "https://www.instagram.com/p/..."
  }
]
```