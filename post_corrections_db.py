#!/usr/bin/env python3
"""
SQLite database for managing post corrections
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

class PostCorrectionsDB:
    def __init__(self, db_path="post_corrections.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with the corrections table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corrections (
                post_id TEXT PRIMARY KEY,
                cafe_name TEXT,
                city TEXT,
                country TEXT,
                continent TEXT,
                latitude REAL,
                longitude REAL,
                notes TEXT,
                rating INTEGER,
                published BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_corrections(self, corrections_data):
        """Save corrections from the admin interface"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for post_id, corrections in corrections_data.items():
            # Check if record exists
            cursor.execute('SELECT post_id FROM corrections WHERE post_id = ?', (post_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing record
                fields = []
                values = []
                for key, value in corrections.items():
                    fields.append(f"{key} = ?")
                    values.append(value)
                
                fields.append("updated_at = ?")
                values.append(datetime.now())
                values.append(post_id)
                
                query = f"UPDATE corrections SET {', '.join(fields)} WHERE post_id = ?"
                cursor.execute(query, values)
            else:
                # Insert new record
                keys = list(corrections.keys())
                keys.extend(['post_id', 'created_at', 'updated_at'])
                values = list(corrections.values())
                values.extend([post_id, datetime.now(), datetime.now()])
                
                placeholders = ', '.join(['?'] * len(keys))
                query = f"INSERT INTO corrections ({', '.join(keys)}) VALUES ({placeholders})"
                cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def get_corrections(self, post_id=None):
        """Get corrections for a specific post or all corrections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if post_id:
            cursor.execute('SELECT * FROM corrections WHERE post_id = ?', (post_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                result = dict(zip(columns, row))
                conn.close()
                return result
            conn.close()
            return None
        else:
            cursor.execute('SELECT * FROM corrections')
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            result = {}
            for row in rows:
                row_dict = dict(zip(columns, row))
                post_id = row_dict.pop('post_id')
                row_dict.pop('created_at', None)
                row_dict.pop('updated_at', None)
                result[post_id] = row_dict
            conn.close()
            return result
    
    def delete_correction(self, post_id):
        """Delete corrections for a specific post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM corrections WHERE post_id = ?', (post_id,))
        conn.commit()
        conn.close()
    
    def export_to_json(self):
        """Export corrections to JSON format (for compatibility)"""
        corrections = self.get_corrections()
        return json.dumps(corrections, indent=2)
    
    def import_from_json(self, json_data):
        """Import corrections from JSON format"""
        if isinstance(json_data, str):
            corrections_data = json.loads(json_data)
        else:
            corrections_data = json_data
        
        self.save_corrections(corrections_data)

if __name__ == "__main__":
    # Test the database
    db = PostCorrectionsDB()
    
    # Example usage
    test_corrections = {
        "coffee/2024-01-01-test-post": {
            "cafe_name": "Test Cafe",
            "city": "Test City",
            "country": "Test Country",
            "published": False
        }
    }
    
    db.save_corrections(test_corrections)
    
    # Retrieve corrections
    all_corrections = db.get_corrections()
    print("All corrections:")
    print(json.dumps(all_corrections, indent=2))
    
    # Get specific post
    specific = db.get_corrections("coffee/2024-01-01-test-post")
    print(f"\nSpecific post: {specific}")