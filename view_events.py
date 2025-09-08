#!/usr/bin/env python3
"""
School Device Monitor - Event Viewer
Utility script to view events from the SQLite database.
"""

import sqlite3
import sys
from datetime import datetime

DATABASE_FILE = "events.db"

def view_recent_events(limit=10):
    """View recent events from the database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, process_name, pid, user, path, status
            FROM events 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        events = cursor.fetchall()
        
        if not events:
            print("No events found in database.")
            return
        
        print(f"Recent Events (Last {len(events)}):")
        print("=" * 80)
        print(f"{'Timestamp':<20} {'Process':<20} {'PID':<8} {'User':<15} {'Status':<12}")
        print("-" * 80)
        
        for event in events:
            timestamp, process_name, pid, user, path, status = event
            # Format timestamp for display
            try:
                dt = datetime.fromisoformat(timestamp)
                display_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                display_time = timestamp[:19]
            
            print(f"{display_time:<20} {process_name:<20} {pid:<8} {user:<15} {status:<12}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error viewing events: {e}")

def view_unauthorized_processes():
    """View only unauthorized processes"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, process_name, pid, user, path
            FROM events 
            WHERE status = 'UNAUTHORIZED'
            ORDER BY timestamp DESC
        ''')
        
        events = cursor.fetchall()
        
        if not events:
            print("No unauthorized processes found.")
            return
        
        print(f"Unauthorized Processes (Total: {len(events)}):")
        print("=" * 80)
        print(f"{'Timestamp':<20} {'Process':<20} {'PID':<8} {'User':<15} {'Path':<30}")
        print("-" * 80)
        
        for event in events:
            timestamp, process_name, pid, user, path = event
            try:
                dt = datetime.fromisoformat(timestamp)
                display_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                display_time = timestamp[:19]
            
            # Truncate path if too long
            display_path = path if len(path) <= 30 else path[:27] + "..."
            
            print(f"{display_time:<20} {process_name:<20} {pid:<8} {user:<15} {display_path:<30}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error viewing unauthorized processes: {e}")

def view_statistics():
    """View database statistics"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Total events
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        # Unauthorized events
        cursor.execute("SELECT COUNT(*) FROM events WHERE status = 'UNAUTHORIZED'")
        unauthorized_events = cursor.fetchone()[0]
        
        # Unique processes
        cursor.execute("SELECT COUNT(DISTINCT process_name) FROM events WHERE status = 'UNAUTHORIZED'")
        unique_processes = cursor.fetchone()[0]
        
        # Most common unauthorized processes
        cursor.execute('''
            SELECT process_name, COUNT(*) as count
            FROM events 
            WHERE status = 'UNAUTHORIZED'
            GROUP BY process_name 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_processes = cursor.fetchall()
        
        print("Database Statistics:")
        print("=" * 40)
        print(f"Total Events: {total_events}")
        print(f"Unauthorized Events: {unauthorized_events}")
        print(f"Unique Unauthorized Processes: {unique_processes}")
        
        if top_processes:
            print("\nTop Unauthorized Processes:")
            print("-" * 40)
            for process_name, count in top_processes:
                print(f"  {process_name}: {count} times")
        
        conn.close()
        
    except Exception as e:
        print(f"Error viewing statistics: {e}")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python view_events.py recent [limit]  - View recent events")
        print("  python view_events.py unauthorized    - View unauthorized processes only")
        print("  python view_events.py stats           - View database statistics")
        return
    
    command = sys.argv[1].lower()
    
    if command == "recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        view_recent_events(limit)
    elif command == "unauthorized":
        view_unauthorized_processes()
    elif command == "stats":
        view_statistics()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
