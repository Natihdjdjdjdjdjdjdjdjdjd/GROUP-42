#!/usr/bin/env python3
"""
Reset Database Script
Deletes old database and creates new one with correct schema
"""

import sqlite3
import os

def reset_database():
    """Reset the database"""
    print("�� Resetting database...")
    
    try:
        # Delete old database files
        files_to_delete = ["events.db", "events.db-journal"]
        for file in files_to_delete:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print(f"✅ Deleted {file}")
                except:
                    print(f"⚠️  Could not delete {file}")
        
        # Create new database with correct schema
        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()
        
        # Create the enhanced events table
        cursor.execute('''
            CREATE TABLE events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                process_name TEXT NOT NULL,
                pid INTEGER NOT NULL,
                user TEXT,
                path TEXT,
                status TEXT NOT NULL,
                alert_level TEXT DEFAULT 'INFO',
                file_hash TEXT,
                action_taken TEXT DEFAULT 'LOGGED'
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ New database created with enhanced schema")
        return True
        
    except Exception as e:
        print(f"❌ Database reset error: {e}")
        return False

if __name__ == "__main__":
    print("School Device Monitor - Database Reset")
    print("=" * 45)
    
    if reset_database():
        print("\n🎉 Database reset completed!")
        print("You can now run the enhanced monitoring system.")
    else:
        print("\n❌ Database reset failed.")
