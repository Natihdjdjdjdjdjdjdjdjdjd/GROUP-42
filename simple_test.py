#!/usr/bin/env python3
"""
Simple Test Script for School Device Monitor
Tests core functionality without external dependencies
"""

import os
import sqlite3
import json
from datetime import datetime

def test_whitelist():
    """Test whitelist loading"""
    print("🔍 Testing whitelist...")
    try:
        with open("whitelist.txt", 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"✅ Whitelist: {len(lines)} processes loaded")
        return True
    except Exception as e:
        print(f"❌ Whitelist error: {e}")
        return False

def test_config():
    """Test configuration"""
    print("🔍 Testing configuration...")
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        print(f"✅ Configuration: {len(config)} settings loaded")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_database():
    """Test database"""
    print("🔍 Testing database...")
    try:
        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Check if we have the enhanced schema
        if 'alert_level' in columns and 'action_taken' in columns:
            print("✅ Database: Enhanced schema detected")
        else:
            print("⚠️  Database: Old schema detected (run fix_database.py)")
            conn.close()
            return False
        
        # Check record count
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        print(f"✅ Database: {count} events recorded")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_monitor():
    """Test the monitor"""
    print("�� Testing monitor...")
    try:
        from detect import ProcessMonitor
        monitor = ProcessMonitor()
        
        print(f"✅ Monitor: {len(monitor.whitelist)} processes in whitelist")
        print(f"✅ Monitor: Database connection established")
        
        # Test scanning
        unauthorized = monitor.scan_processes()
        print(f"✅ Monitor: Found {len(unauthorized)} unauthorized processes")
        
        monitor.db_conn.close()
        return True
    except Exception as e:
        print(f"❌ Monitor error: {e}")
        return False

def main():
    """Run all tests"""
    print("School Device Monitor - Simple Test")
    print("=" * 50)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Whitelist", test_whitelist),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Monitor", test_monitor)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is working.")
    elif passed >= 3:
        print("⚠️  Most tests passed. System is mostly working.")
    else:
        print("❌ Several tests failed. Check the errors above.")
    
    print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
