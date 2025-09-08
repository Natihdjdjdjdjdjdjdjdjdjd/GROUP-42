#!/usr/bin/env python3
"""
Database Migration Script v2
Handles database in use and creates new schema
"""

import sqlite3
import os
import time

def wait_for_database():
    """Wait for database to be available"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            conn = sqlite3.connect("events.db")
            conn.close()
            return True
        except:
            print(f"Database busy, waiting... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(2)
    return False

def migrate_database():
    """Migrate the database to the new schema"""
    print("�� Migrating database schema...")
    
    try:
        # Wait for database to be available
        if not wait_for_database():
            print("❌ Database is still busy. Please close any running monitors.")
            return False
        
        # Create new database with a different name
        new_db_name = "events_new.db"
        
        # Create new database with correct schema
        conn = sqlite3.connect(new_db_name)
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
        
        # Now try to replace the old database
        try:
            if os.path.exists("events.db"):
                os.rename("events.db", "events_old.db")
                print("✅ Old database backed up as events_old.db")
        except:
            print("⚠️  Could not backup old database, but continuing...")
        
        # Rename new database to events.db
        os.rename(new_db_name, "events.db")
        
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
    print("School Device Monitor - Database Migration v2")
    print("=" * 55)
    
    if migrate_database():
        if test_new_database():
            print("\n�� Database migration completed successfully!")
            print("You can now run the enhanced monitoring system.")
        else:
            print("\n❌ Database migration failed verification.")
    else:
        print("\n❌ Database migration failed.")
