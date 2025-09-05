---
layout: default
title: New Database Admin
---

# ☕ New Database Admin System

The new SQLite-based admin system is now available! This replaces the old file-based system.

## Features
- **Hash-based deduplication** - No more duplicate posts
- **Per-post regeneration** - Changes save instantly to Jekyll
- **Single source of truth** - All data stored in SQLite
- **Modern interface** - Clean web UI with search and stats
- **Images as arrays** - Multiple images per post supported

## Access Methods

### Method 1: Direct File Access
Open the admin interface directly:
- **File path**: `admin_db.html` (open directly in browser)

### Method 2: API + Interface (Recommended)
1. **Start the API server**: `python3 admin_api.py`
2. **Open admin interface**: Open `admin_db.html` in your browser
3. **The interface will connect to**: `http://localhost:8081/api`

## Quick Commands

```bash
# Import existing posts to database
python3 import_posts_to_db.py

# Start full admin system
python3 start_admin.py

# Regenerate all Jekyll posts from database
python3 regenerate_posts.py

# Regenerate single post (ID)
python3 single_post_regenerator.py 1
```

## Current Status
- ✅ **47 posts imported** to SQLite database
- ✅ **Per-post regeneration** working on save
- ✅ **Duplicate cleanup** completed (was 223 files, now 47)
- ✅ **Jekyll running cleanly** with regenerated posts

## Benefits Over Old System
- **No more broken pages** - All YAML properly validated
- **No more duplicates** - Hash-based deduplication
- **Instant saves** - Changes apply immediately to Jekyll
- **Clean data** - Single source of truth in database
- **Better workflow** - Edit → Save → Auto-regenerate → Jekyll rebuilds