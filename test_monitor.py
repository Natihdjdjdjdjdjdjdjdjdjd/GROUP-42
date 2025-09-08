#!/usr/bin/env python3
"""
Test script for School Device Monitor
Quick test to verify functionality
"""

import time
import subprocess
import os
from detect import ProcessMonitor

def test_monitor():
    """Test the process monitor functionality"""
    print("Testing School Device Monitor...")
    print("=" * 40)
    
    # Initialize monitor
    monitor = ProcessMonitor()
    
    # Test whitelist loading
    print(f"Whitelist loaded: {len(monitor.whitelist)} processes")
    print("Sample whitelist entries:")
    for i, process in enumerate(list(monitor.whitelist)[:5]):
        print(f"  - {process}")
    
    # Test database setup
    if monitor.db_conn:
        print("Database connection: OK")
    else:
        print("Database connection: FAILED")
    
    # Test process scanning
    print("\nScanning processes...")
    unauthorized = monitor.scan_processes()
    
    if unauthorized:
        print(f"Found {len(unauthorized)} unauthorized processes:")
        for proc in unauthorized[:3]:  # Show first 3
            print(f"  - {proc['name']} (PID: {proc['pid']})")
    else:
        print("No unauthorized processes found")
    
    # Clean up
    if monitor.db_conn:
        monitor.db_conn.close()
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_monitor()
