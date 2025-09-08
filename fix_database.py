#!/usr/bin/env python3
"""
Database Migration Script
Updates the database schema to match the enhanced detect.py
"""

import sqlite3
import os

def migrate_database():
    """Migrate the database to the new schema"""
    print("�� Migrating database schema...")
    
    try:
        # Backup the old database
        if os.path.exists("events.db"):
            os.rename("events.db", "events.db.backup")
            print("✅ Old database backed up as events.db.backup")
        
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
        
        print("✅ Database schema updated successfully")
        print("✅ New database created with enhanced schema")
        
        return True
        
    except Exception as e:
        print(f"❌ Database migration error: {e}")
        return False

def test_new_database():
    """Test the new database"""
    try:
        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()
        
        # Check if all columns exist
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'id', 'timestamp', 'process_name', 'pid', 'user', 
            'path', 'status', 'alert_level', 'file_hash', 'action_taken'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print("✅ All required columns present")
            return True
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("School Device Monitor - Database Migration")
    print("=" * 50)
    
    if migrate_database():
        if test_new_database():
            print("\n�� Database migration completed successfully!")
            print("You can now run the enhanced monitoring system.")
        else:
            print("\n❌ Database migration failed verification.")
    else:
        print("\n❌ Database migration failed.")
