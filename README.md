# World Coffee Tour ☕

A minimalist Jekyll website showcasing coffee experiences from around the world, automatically pulling posts from Instagram with the #worldcoffeetour hashtag.

## 🌍 Live Site
[worldcoffeetour.joegaudet.com](https://worldcoffeetour.joegaudet.com)

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
bundle install

# Serve locally
bundle exec jekyll serve

# Visit http://localhost:4000
```

### Update Coffee Posts

Run the update script to fetch new posts:
```bash
./update_posts.sh
```

Or use the Python script directly:
```bash
python3 fetch_instagram_posts.py
```

The script offers three modes:
1. **Manual Entry** - Add individual coffee posts
2. **Instagram Fetch** - Fetch posts with #worldcoffeetour (requires login)
3. **Process JSON** - Convert existing JSON data to Jekyll posts

## 📝 Adding Posts Manually

Create a new file in `_coffee_posts/` with format `YYYY-MM-DD-title.md`:

```yaml
---
layout: post
title: "Morning Brew in Tokyo"
date: 2024-01-10
city: "Tokyo"
country: "Japan"
region: "Asia"
latitude: 35.6762
longitude: 139.6503
cafe_name: "Blue Bottle Coffee"
coffee_type: "Pour Over"
rating: 5
notes: "Exceptional single-origin Ethiopian beans"
image_url: "https://..."
instagram_url: "https://www.instagram.com/p/..."
---
```

## 🎨 Features

- **Interactive Map** - Shows all coffee locations with clickable markers
- **Regional Grouping** - Posts organized by continent/region
- **Minimalist Design** - Clean, hipster-friendly aesthetic
- **Responsive Layout** - Works beautifully on all devices
- **Instagram Integration** - Pulls posts with #worldcoffeetour hashtag

## 🛠 Technical Stack

- **Jekyll** - Static site generator
- **GitHub Pages** - Hosting
- **Leaflet.js** - Interactive maps
- **Python** - Instagram post fetching
- **Minimal CSS** - Custom minimalist design

## 📱 Instagram Integration

The site is designed to work with Instagram posts tagged with #worldcoffeetour. Due to Instagram API limitations, you'll need to:

1. Use the provided Python script with your login credentials
2. Manually export your posts using third-party tools
3. Add posts manually through the script's interface

## 🚢 Deployment

The site automatically deploys to GitHub Pages when you push to the main branch:

```bash
git add .
git commit -m "Update coffee posts"
git push origin main
```

## 📄 License

Personal project by Joe Gaudet