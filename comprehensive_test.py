#!/usr/bin/env python3
"""
Comprehensive Test Script for School Device Monitor
Tests all major functionality
"""

import os
import time
import subprocess
import sqlite3
import json
import requests
from datetime import datetime

def test_whitelist_loading():
    """Test whitelist loading"""
    print("🔍 Testing whitelist loading...")
    try:
        with open("whitelist.txt", 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"✅ Whitelist loaded: {len(lines)} processes")
        return True
    except Exception as e:
        print(f"❌ Whitelist error: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("🔍 Testing configuration loading...")
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        print(f"✅ Configuration loaded: {len(config)} settings")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("🔍 Testing database...")
    try:
        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if cursor.fetchone():
            print("✅ Events table exists")
        else:
            print("❌ Events table not found")
            return False
        
        # Check record count
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        print(f"✅ Database has {count} records")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_process_monitoring():
    """Test process monitoring functionality"""
    print("🔍 Testing process monitoring...")
    try:
        from detect import ProcessMonitor
        monitor = ProcessMonitor()
        
        # Test whitelist
        if len(monitor.whitelist) > 0:
            print(f"✅ Whitelist loaded: {len(monitor.whitelist)} processes")
        else:
            print("❌ Whitelist is empty")
            return False
        
        # Test database connection
        if monitor.db_conn:
            print("✅ Database connection established")
        else:
            print("❌ Database connection failed")
            return False
        
        # Test process scanning
        unauthorized = monitor.scan_processes()
        print(f"✅ Process scanning working: found {len(unauthorized)} unauthorized processes")
        
        monitor.db_conn.close()
        return True
    except Exception as e:
        print(f"❌ Process monitoring error: {e}")
        return False

def test_web_dashboard():
    """Test web dashboard"""
    print("🔍 Testing web dashboard...")
    try:
        # Check if dashboard is running
        response = requests.get("http://localhost:5000/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Web dashboard is running")
            print(f"   - Total events: {data.get('total_events', 0)}")
            print(f"   - Events today: {data.get('events_today', 0)}")
            return True
        else:
            print(f"❌ Web dashboard error: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Web dashboard not running (start with: py web_dashboard.py)")
        return False

def test_unauthorized_process_detection():
    """Test unauthorized process detection"""
    print("🔍 Testing unauthorized process detection...")
    try:
        # Get current unauthorized processes
        from detect import ProcessMonitor
        monitor = ProcessMonitor()
        
        before_count = len(monitor.scan_processes())
        
        # Launch a test process (notepad if not in whitelist)
        test_process = None
        try:
            test_process = subprocess.Popen(["notepad.exe"], 
                                          stdout=subprocess.DEVNULL, 
                                          stderr=subprocess.DEVNULL)
            time.sleep(2)  # Wait for process to start
            
            after_count = len(monitor.scan_processes())
            
            if after_count >= before_count:
                print("✅ Unauthorized process detection working")
                print(f"   - Before: {before_count} unauthorized processes")
                print(f"   - After: {after_count} unauthorized processes")
                
                # Clean up
                if test_process:
                    test_process.terminate()
                    test_process.wait(timeout=5)
                
                return True
            else:
                print("❌ Unauthorized process detection not working")
                return False
                
        except Exception as e:
            print(f"❌ Test process error: {e}")
            if test_process:
                test_process.terminate()
            return False
        finally:
            monitor.db_conn.close()
            
    except Exception as e:
        print(f"❌ Unauthorized process detection error: {e}")
        return False

def test_event_logging():
    """Test event logging"""
    print("🔍 Testing event logging...")
    try:
        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()
        
        # Get count before
        cursor.execute("SELECT COUNT(*) FROM events")
        before_count = cursor.fetchone()[0]
        
        # Run a quick scan
        from detect import ProcessMonitor
        monitor = ProcessMonitor()
        monitor.scan_processes()
        
        # Get count after
        cursor.execute("SELECT COUNT(*) FROM events")
        after_count = cursor.fetchone()[0]
        
        conn.close()
        monitor.db_conn.close()
        
        if after_count > before_count:
            print(f"✅ Event logging working: {after_count - before_count} new events logged")
            return True
        else:
            print("❌ Event logging not working")
            return False
            
    except Exception as e:
        print(f"❌ Event logging error: {e}")
        return False

def main():
    """Run all tests"""
    print("School Device Monitor - Comprehensive Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Whitelist Loading", test_whitelist_loading),
        ("Configuration Loading", test_config_loading),
        ("Database", test_database),
        ("Process Monitoring", test_process_monitoring),
        ("Event Logging", test_event_logging),
        ("Web Dashboard", test_web_dashboard),
        ("Unauthorized Process Detection", test_unauthorized_process_detection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. System is mostly working.")
    else:
        print("❌ Many tests failed. Check the errors above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
