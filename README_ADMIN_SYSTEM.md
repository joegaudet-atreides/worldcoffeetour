# Coffee Posts Database Admin System

A complete SQLite-based content management system for the World Coffee Tour Jekyll site.

## System Overview

The new system uses SQLite as the single source of truth for all coffee posts, with hash-based deduplication to prevent duplicates. All editing is done in the database, and Jekyll posts are regenerated from the database.

## Key Features

- **Hash-based deduplication**: Prevents duplicate posts based on content fingerprinting
- **Single source of truth**: SQLite database stores all post data
- **Images as arrays**: Multiple images stored as JSON arrays
- **Clean regeneration**: Destroys and recreates all Jekyll posts from database
- **Modern admin interface**: Web-based editing with real-time stats

## Files

### Core Database
- `coffee_db.py` - Main database class with CRUD operations
- `coffee_posts.db` - SQLite database file (created automatically)

### Import/Export
- `import_posts_to_db.py` - Import existing Jekyll posts to database
- `regenerate_posts.py` - Generate all Jekyll posts from database

### Admin Interface
- `admin_api.py` - HTTP API server for database operations
- `admin_db.html` - Web-based admin interface
- `start_admin.py` - Convenient startup script

### Utilities
- `verify_posts.py` - Comprehensive post validation
- `fix_duplicate_frontmatter.py` - Fix YAML front matter issues
- `quick_yaml_fix.py` - Quick YAML special character fixes

## Workflow

### 1. Initial Setup
```bash
# Import existing posts to database
python3 import_posts_to_db.py

# Start admin system
python3 start_admin.py
```

### 2. Daily Usage
```bash
# Start admin interface
python3 start_admin.py
```

The admin interface opens at `admin_db.html` with API at `http://localhost:8081`

### 3. Making Changes
1. Edit posts in the web admin interface
2. Click "Regenerate Jekyll Posts" to update the Jekyll files
3. Jekyll automatically rebuilds the site

### 4. Adding New Posts
- Use the admin interface "Add New Post" button
- All images go in the images array
- Posts are automatically deduplicated by hash

## Database Schema

```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT UNIQUE NOT NULL,           -- Deduplication hash
    title TEXT,
    date TEXT,
    city TEXT,
    country TEXT,
    continent TEXT,
    latitude REAL,
    longitude REAL,
    cafe_name TEXT,
    rating INTEGER,
    notes TEXT,
    images TEXT,                         -- JSON array of image URLs
    instagram_url TEXT,
    published BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_filename TEXT,
    metadata TEXT                        -- JSON for extra fields
)
```

## API Endpoints

- `GET /api/posts` - Get all posts
- `GET /api/posts/{id}` - Get single post
- `POST /api/posts` - Create new post
- `POST /api/posts/{id}/update` - Update post
- `POST /api/posts/{id}/delete` - Delete post
- `GET /api/stats` - Get statistics
- `GET /api/search?q=query` - Search posts
- `POST /api/regenerate` - Regenerate Jekyll posts

## Benefits

1. **No more duplicates**: Hash-based deduplication prevents duplicate posts
2. **Clean workflow**: Edit in database → regenerate → Jekyll rebuilds
3. **Data integrity**: Single source of truth with proper validation
4. **Flexible images**: Store multiple images per post as arrays
5. **Better admin**: Modern web interface with search and stats
6. **Idempotent imports**: Can safely re-run imports without creating duplicates

## Migration Notes

The system successfully imported 47 posts from the existing Jekyll collection. Posts with broken YAML front matter were skipped and can be manually recreated in the admin interface.

All new posts should be created through the admin interface to ensure proper formatting and deduplication.