# ☕ World Coffee Tour - Complete Admin System

The coffee posts are now managed through a comprehensive SQLite-based system that provides a single source of truth for all data.

## 🎯 Key Features

✅ **SQLite Database Backend** - Single source of truth for all post data  
✅ **Multiple Image Support** - All images from Instagram posts are preserved  
✅ **Hash-based Deduplication** - Prevents duplicate posts automatically  
✅ **Idempotent Operations** - Safe to re-run scripts multiple times  
✅ **Live Admin Interface** - Real-time editing with instant Jekyll updates  
✅ **Published/Unpublished Tabs** - Easy content management  
✅ **Problematic Post Detection** - Identifies posts needing attention  
✅ **Advanced Search & Filtering** - Find posts by location, cafe, etc.  
✅ **Typeahead Location Search** - Quick location entry assistance  
✅ **Interactive Maps** - Visual editing of post locations  

## 📊 Current Status

- **Total Posts**: 345 (imported from Instagram export)
- **Published**: 327 posts visible on site
- **Unpublished**: 18 posts hidden from site
- **With Multiple Images**: Supports all original Instagram multi-image posts
- **Jekyll Sync**: 100% generated from SQLite database

## 🚀 Quick Start

### 1. Start the Admin System
```bash
# Start the admin API server
python3 admin_api.py

# Jekyll is already running on http://localhost:4000
# Admin interface: http://localhost:4000/admin.html
```

### 2. Import from Instagram (if needed)
```bash
# Import all posts from Instagram export
python3 import_instagram_full.py

# Check what was imported
python3 import_instagram_full.py --stats-only
```

### 3. Sync Jekyll Posts
```bash
# Ensure Jekyll posts match database exactly
python3 ensure_db_sync.py --clean

# Just verify sync without changes
python3 ensure_db_sync.py --verify-only
```

## 📝 Admin Interface

### Access
- **URL**: http://localhost:4000/admin.html
- **API**: http://localhost:8081/api (must be running)

### Features

#### Tabs
- **Published Posts**: Shows all published posts (visible on site)
- **Unpublished Posts**: Shows hidden posts
- **Problematic Posts**: Shows posts missing location, cafe name, etc.

#### Search & Filtering
- **Text Search**: Search titles, cafe names, locations, notes
- **Continent Filter**: Filter by continent
- **Country Filter**: Filter by country  
- **Problematic Only**: Show only posts needing attention

#### Post Editing
- **Multiple Images**: View all images from original Instagram post
- **Location Search**: Typeahead search for cafes and locations
- **Interactive Map**: Click or drag to set precise coordinates
- **Rich Metadata**: Title, cafe name, city, country, continent
- **Rating System**: 1-5 coffee rating
- **Publication Control**: Publish/unpublish posts
- **Notes**: Full post content and additional notes

#### Actions
- **Save**: Instantly updates database and regenerates Jekyll post
- **Delete**: Removes post from database and Jekyll
- **Regenerate All**: Rebuilds all Jekyll posts from database

## 🔧 System Architecture

### Core Files

**Database Layer:**
- `coffee_db.py` - SQLite database management
- `coffee_posts.db` - SQLite database file

**Admin Interface:**
- `admin.html` - Modern web admin interface
- `admin_api.py` - REST API server for database operations

**Import/Sync Tools:**
- `import_instagram_full.py` - Import from Instagram export
- `ensure_db_sync.py` - Sync Jekyll posts with database
- `regenerate_posts.py` - Bulk Jekyll post generation
- `single_post_regenerator.py` - Individual post regeneration

**Generated Content:**
- `_coffee_posts/` - Jekyll posts (auto-generated from database)

### Data Flow

```
Instagram Export → Database → Jekyll Posts → Website
                     ↑             ↓
               Admin Interface ← API Server
```

## 🔄 Workflow

### Normal Operations
1. **Edit posts** through admin interface
2. **Changes save instantly** to database
3. **Jekyll posts regenerate** automatically
4. **Website updates** immediately

### Bulk Operations
1. **Import new Instagram data** with `import_instagram_full.py`
2. **Regenerate all posts** with `ensure_db_sync.py --clean`
3. **Jekyll rebuilds** site automatically

### Maintenance
1. **Check sync status** with `ensure_db_sync.py --verify-only`
2. **View statistics** with `import_instagram_full.py --stats-only`
3. **Backup database** by copying `coffee_posts.db`

## 🛠 Troubleshooting

### Admin Page Won't Load
```bash
# Check if API server is running
curl http://localhost:8081/api/posts

# Start API server if needed
python3 admin_api.py
```

### Posts Not Appearing on Site
```bash
# Check Jekyll is running
curl http://localhost:4000

# Regenerate all posts from database
python3 ensure_db_sync.py --clean
```

### Import Issues
```bash
# Verify Instagram export structure
ls -la instagram-export-folder/your_instagram_activity/media/

# Check for posts_1.json file
# Update paths in import_instagram_full.py if needed
```

### Database Issues
```bash
# Check database status
python3 -c "from coffee_db import CoffeeDatabase; db = CoffeeDatabase(); print(db.get_statistics())"

# Reset database (⚠️ DESTRUCTIVE)
rm coffee_posts.db
python3 import_instagram_full.py
```

## 📈 Statistics

The system tracks comprehensive statistics:
- Total posts and publication status
- Posts with images, locations, and cafe names
- Geographic distribution by continent/country
- Post completeness for quality control

## 🎛 Configuration

### Environment
- Jekyll serves on `http://localhost:4000`
- Admin API serves on `http://localhost:8081`
- Database file: `coffee_posts.db`

### Customization
- Modify `coffee_db.py` for schema changes
- Edit `admin.html` for interface improvements
- Update `import_instagram_full.py` for different data sources

## 🎉 Success!

The system now provides:
- **345 posts** imported and managed
- **100% database-driven** Jekyll generation
- **Modern admin interface** with all requested features
- **Idempotent operations** safe for repeated use
- **Multiple image support** preserving Instagram content
- **Advanced filtering and search** capabilities

Everything is working together as a cohesive system for managing the World Coffee Tour content! ☕️