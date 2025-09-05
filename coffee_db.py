#!/usr/bin/env python3
"""
SQLite database management for coffee posts
Single source of truth for all post data
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime

class CoffeeDatabase:
    def __init__(self, db_path='coffee_posts.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE NOT NULL,
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
                images TEXT,  -- JSON array of image URLs
                instagram_url TEXT,
                published BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                original_filename TEXT,
                metadata TEXT  -- JSON for any extra fields
            )
        ''')
        
        # Create indexes for common queries
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON posts(date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_continent ON posts(continent)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON posts(country)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON posts(city)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_published ON posts(published)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON posts(hash)')
        
        self.conn.commit()
    
    def generate_hash(self, data):
        """Generate a unique hash for a post based on key content"""
        # Use title, date, and first image (if available) to create unique hash
        hash_parts = []
        
        if data.get('title'):
            hash_parts.append(data['title'][:50])  # First 50 chars of title
        
        if data.get('date'):
            hash_parts.append(str(data['date']))
        
        if data.get('notes'):
            hash_parts.append(data['notes'][:50])  # First 50 chars of notes
            
        images = data.get('images', [])
        if images:
            if isinstance(images, str):
                images = json.loads(images)
            if images and len(images) > 0:
                hash_parts.append(images[0])  # First image URL
        
        # Fallback to timestamp if no meaningful data
        if not hash_parts:
            hash_parts.append(str(datetime.now().timestamp()))
        
        hash_string = '|'.join(hash_parts)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def upsert_post(self, data):
        """Insert or update a post (idempotent operation)"""
        # Generate hash
        post_hash = self.generate_hash(data)
        
        # Convert images list to JSON
        images = data.get('images', [])
        if isinstance(images, list):
            images_json = json.dumps(images)
        else:
            images_json = images
        
        # Store any extra fields in metadata
        core_fields = {
            'title', 'date', 'city', 'country', 'continent',
            'latitude', 'longitude', 'cafe_name', 'rating', 'notes',
            'images', 'instagram_url', 'published', 'original_filename'
        }
        
        metadata = {}
        for key, value in data.items():
            if key not in core_fields and value is not None:
                metadata[key] = value
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Try to insert, update if exists
        try:
            self.cursor.execute('''
                INSERT INTO posts (
                    hash, title, date, city, country, continent,
                    latitude, longitude, cafe_name, rating, notes,
                    images, instagram_url, published, original_filename, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post_hash,
                data.get('title'),
                data.get('date'),
                data.get('city', 'Unknown'),
                data.get('country', 'Unknown'),
                data.get('continent', 'Unknown'),
                data.get('latitude'),
                data.get('longitude'),
                data.get('cafe_name'),
                data.get('rating'),
                data.get('notes'),
                images_json,
                data.get('instagram_url'),
                data.get('published', True),
                data.get('original_filename'),
                metadata_json
            ))
            self.conn.commit()
            return self.cursor.lastrowid, 'inserted'
            
        except sqlite3.IntegrityError:
            # Hash exists, update the record
            self.cursor.execute('''
                UPDATE posts SET
                    title = ?,
                    date = ?,
                    city = ?,
                    country = ?,
                    continent = ?,
                    latitude = ?,
                    longitude = ?,
                    cafe_name = ?,
                    rating = ?,
                    notes = ?,
                    images = ?,
                    instagram_url = ?,
                    published = ?,
                    metadata = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE hash = ?
            ''', (
                data.get('title'),
                data.get('date'),
                data.get('city', 'Unknown'),
                data.get('country', 'Unknown'),
                data.get('continent', 'Unknown'),
                data.get('latitude'),
                data.get('longitude'),
                data.get('cafe_name'),
                data.get('rating'),
                data.get('notes'),
                images_json,
                data.get('instagram_url'),
                data.get('published', True),
                metadata_json,
                post_hash
            ))
            self.conn.commit()
            return self.cursor.lastrowid, 'updated'
    
    def get_all_posts(self, published_only=False):
        """Get all posts from the database"""
        if published_only:
            query = 'SELECT * FROM posts WHERE published = 1 ORDER BY date DESC'
        else:
            query = 'SELECT * FROM posts ORDER BY date DESC'
        
        self.cursor.execute(query)
        posts = []
        
        for row in self.cursor.fetchall():
            post = dict(row)
            # Parse JSON fields
            if post['images']:
                try:
                    post['images'] = json.loads(post['images'])
                except (json.JSONDecodeError, TypeError):
                    print(f"Warning: Invalid JSON in images field for post {post.get('id')}: {post['images']}")
                    post['images'] = []
            else:
                post['images'] = []
            
            if post['metadata']:
                metadata = json.loads(post['metadata'])
                post.update(metadata)
            
            posts.append(post)
        
        return posts
    
    def get_post_by_id(self, post_id):
        """Get a single post by ID"""
        self.cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        row = self.cursor.fetchone()
        
        if row:
            post = dict(row)
            if post['images']:
                post['images'] = json.loads(post['images'])
            else:
                post['images'] = []
            
            if post['metadata']:
                metadata = json.loads(post['metadata'])
                post.update(metadata)
            
            return post
        return None
    
    def update_post(self, post_id, data):
        """Update a post by ID - supports partial updates"""
        # Build SET clause dynamically for only provided fields
        set_clauses = []
        params = []
        
        # Handle each field that might be updated
        if 'title' in data:
            set_clauses.append('title = ?')
            params.append(data['title'])
            
        if 'date' in data:
            set_clauses.append('date = ?')
            params.append(data['date'])
            
        if 'city' in data:
            set_clauses.append('city = ?')
            params.append(data['city'])
            
        if 'country' in data:
            set_clauses.append('country = ?')
            params.append(data['country'])
            
        if 'continent' in data:
            set_clauses.append('continent = ?')
            params.append(data['continent'])
            
        if 'latitude' in data:
            set_clauses.append('latitude = ?')
            params.append(data['latitude'])
            
        if 'longitude' in data:
            set_clauses.append('longitude = ?')
            params.append(data['longitude'])
            
        if 'cafe_name' in data:
            set_clauses.append('cafe_name = ?')
            params.append(data['cafe_name'])
            
        if 'rating' in data:
            set_clauses.append('rating = ?')
            params.append(data['rating'])
            
        if 'notes' in data:
            set_clauses.append('notes = ?')
            params.append(data['notes'])
            
        if 'images' in data:
            images = data['images']
            if isinstance(images, list):
                images_json = json.dumps(images)
            else:
                images_json = images
            set_clauses.append('images = ?')
            params.append(images_json)
            
        if 'instagram_url' in data:
            set_clauses.append('instagram_url = ?')
            params.append(data['instagram_url'])
            
        if 'published' in data:
            set_clauses.append('published = ?')
            params.append(data['published'])
        
        # Always update the timestamp
        set_clauses.append('updated_at = CURRENT_TIMESTAMP')
        
        if not set_clauses:
            return False  # No fields to update
            
        # Add post_id to params
        params.append(post_id)
        
        sql = f"UPDATE posts SET {', '.join(set_clauses)} WHERE id = ?"
        
        self.cursor.execute(sql, params)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_post(self, post_id):
        """Delete a post by ID"""
        self.cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def search_posts(self, query, fields=None):
        """Search posts across specified fields"""
        if fields is None:
            fields = ['title', 'notes', 'cafe_name', 'city', 'country']
        
        conditions = []
        params = []
        
        for field in fields:
            conditions.append(f"{field} LIKE ?")
            params.append(f"%{query}%")
        
        where_clause = " OR ".join(conditions)
        sql = f"SELECT * FROM posts WHERE {where_clause} ORDER BY date DESC"
        
        self.cursor.execute(sql, params)
        posts = []
        
        for row in self.cursor.fetchall():
            post = dict(row)
            if post['images']:
                post['images'] = json.loads(post['images'])
            else:
                post['images'] = []
            posts.append(post)
        
        return posts
    
    def get_statistics(self):
        """Get database statistics"""
        stats = {}
        
        # Total posts
        self.cursor.execute('SELECT COUNT(*) as count FROM posts')
        stats['total_posts'] = self.cursor.fetchone()['count']
        
        # Published posts
        self.cursor.execute('SELECT COUNT(*) as count FROM posts WHERE published = 1')
        stats['published_posts'] = self.cursor.fetchone()['count']
        
        # Posts by continent
        self.cursor.execute('''
            SELECT continent, COUNT(*) as count 
            FROM posts 
            WHERE published = 1 
            GROUP BY continent 
            ORDER BY count DESC
        ''')
        stats['by_continent'] = {row['continent']: row['count'] for row in self.cursor.fetchall()}
        
        # Posts with images
        self.cursor.execute('''
            SELECT COUNT(*) as count 
            FROM posts 
            WHERE images IS NOT NULL AND images != '[]'
        ''')
        stats['posts_with_images'] = self.cursor.fetchone()['count']
        
        # Posts with ratings
        self.cursor.execute('SELECT COUNT(*) as count FROM posts WHERE rating IS NOT NULL')
        stats['posts_with_ratings'] = self.cursor.fetchone()['count']
        
        # Posts with location
        self.cursor.execute('''
            SELECT COUNT(*) as count 
            FROM posts 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ''')
        stats['posts_with_location'] = self.cursor.fetchone()['count']
        
        # Posts with cafe names
        self.cursor.execute('''
            SELECT COUNT(*) as count 
            FROM posts 
            WHERE cafe_name IS NOT NULL AND cafe_name != ''
        ''')
        stats['posts_with_cafe_names'] = self.cursor.fetchone()['count']
        
        return stats
    
    def get_post_by_hash(self, post_hash):
        """Get a post by its hash"""
        self.cursor.execute('SELECT * FROM posts WHERE hash = ?', (post_hash,))
        row = self.cursor.fetchone()
        if row:
            post = dict(row)
            # Parse JSON fields
            if post['images']:
                try:
                    post['images'] = json.loads(post['images'])
                except (json.JSONDecodeError, TypeError):
                    print(f"Warning: Invalid JSON in images field for post {post.get('id')}: {post['images']}")
                    post['images'] = []
            else:
                post['images'] = []
            return post
        return None
    
    def insert_post(self, data):
        """Insert a new post"""
        post_hash = data.get('hash') or self.generate_hash(data)
        
        # Convert images list to JSON if needed
        images = data.get('images', [])
        if isinstance(images, list):
            images_json = json.dumps(images)
        else:
            images_json = images
            
        # Store any extra fields in metadata
        core_fields = {
            'title', 'date', 'city', 'country', 'continent',
            'latitude', 'longitude', 'cafe_name', 'rating', 'notes',
            'images', 'instagram_url', 'published', 'original_filename', 'hash'
        }
        
        metadata = {}
        for key, value in data.items():
            if key not in core_fields and value is not None:
                metadata[key] = value
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.cursor.execute('''
            INSERT INTO posts (
                hash, title, date, city, country, continent,
                latitude, longitude, cafe_name, rating, notes,
                images, instagram_url, published, original_filename, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            post_hash,
            data.get('title'),
            data.get('date'),
            data.get('city', 'Unknown'),
            data.get('country', 'Unknown'),
            data.get('continent', 'Unknown'),
            data.get('latitude'),
            data.get('longitude'),
            data.get('cafe_name'),
            data.get('rating'),
            data.get('notes'),
            images_json,
            data.get('instagram_url'),
            data.get('published', True),
            data.get('original_filename'),
            metadata_json
        ))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_post_count(self):
        """Get total number of posts"""
        self.cursor.execute('SELECT COUNT(*) as count FROM posts')
        return self.cursor.fetchone()['count']
    
    def get_continents(self):
        """Get list of all continents"""
        self.cursor.execute('''
            SELECT DISTINCT continent 
            FROM posts 
            WHERE continent IS NOT NULL AND continent != 'Unknown'
            ORDER BY continent
        ''')
        return [row['continent'] for row in self.cursor.fetchall()]
    
    def get_posts_by_continent(self, continent):
        """Get posts by continent"""
        self.cursor.execute('SELECT * FROM posts WHERE continent = ? ORDER BY date DESC', (continent,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    # Test the database
    db = CoffeeDatabase()
    stats = db.get_statistics()
    print(f"Database initialized. Current stats: {stats}")
    db.close()