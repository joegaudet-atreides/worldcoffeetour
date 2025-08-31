#!/bin/bash

# World Coffee Tour - Update Posts Script
# Run this script to fetch new Instagram posts and rebuild the site

echo "☕ World Coffee Tour - Update Script"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3 and try again."
    exit 1
fi

# Run the fetch script
echo "Running Instagram posts fetcher..."
python3 fetch_instagram_posts.py

# Build Jekyll site
echo ""
echo "Building Jekyll site..."
if command -v bundle &> /dev/null; then
    bundle exec jekyll build
    echo "✅ Site built successfully!"
else
    echo "⚠️  Jekyll not installed. Run: gem install bundler jekyll"
fi

echo ""
echo "Done! Your coffee posts are updated."
echo ""
echo "To serve locally: bundle exec jekyll serve"
echo "To deploy: git add . && git commit -m 'Update coffee posts' && git push"