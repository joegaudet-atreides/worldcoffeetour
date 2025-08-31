# Instagram Post Import Guide

Since Instagram has restricted API access, here are the best ways to add your coffee posts:

## Option 1: Interactive Script (Recommended)
Use the helper script to add posts one by one:

```bash
python3 add_coffee_post.py
```

This script will:
- Guide you through adding each post
- Auto-detect regions from location
- Clean up captions for notes
- Generate proper Jekyll post files

## Option 2: Manual Instagram Data Export

1. **Get Your Post Data:**
   - Open Instagram in a web browser
   - Go to your profile
   - Click on a post with #worldcoffeetour
   - Right-click → "Inspect" → Network tab
   - Look for the JSON data containing post info

2. **Extract Key Information:**
   - Caption text
   - Location (if tagged)
   - Date posted
   - Image URL (right-click image → "Copy image address")

3. **Use the Script:**
   ```bash
   python3 add_coffee_post.py
   ```
   Paste the information when prompted

## Option 3: Instagram Data Download

1. Go to Instagram Settings → Privacy → Data Download
2. Request your data (JSON format)
3. Wait for email (can take 48 hours)
4. Extract posts with #worldcoffeetour
5. Use the script to add them

## Getting Coordinates

For accurate map markers:

1. **Google Maps Method:**
   - Search for the café on Google Maps
   - Right-click on the location
   - Select "What's here?"
   - Copy the coordinates shown

2. **From Instagram Location:**
   - If you tagged a location on Instagram
   - Click the location name
   - The URL often contains coordinates

## Tips for Better Posts

- **Title**: Keep it short and descriptive
- **Notes**: Include your experience, not just coffee details
- **Rating**: Be consistent with your scale
- **Image**: Download your Instagram photo in high quality
- **Coffee Type**: Be specific (e.g., "Ethiopian Pour Over" vs just "Coffee")

## Batch Adding Posts

For multiple posts at once:
```bash
python3 add_coffee_post.py
# Choose option 2 for batch mode
```

## After Adding Posts

Rebuild the site to see your new posts:
```bash
bundle exec jekyll build
bundle exec jekyll serve
```

Visit http://localhost:4000 to see your updated site!