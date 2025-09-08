#!/usr/bin/env python3
"""
School Device Monitor - Status Checker
Checks the status of all components and services.
"""

import os
import sqlite3
import json
import psutil
import requests
from datetime import datetime

def check_database():
    """Check database status"""
    try:
        if os.path.exists("events.db"):
            conn = sqlite3.connect("events.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            conn.close()
            return True, f"Database OK - {count} events"
        else:
            return False, "Database not found"
    except Exception as e:
        return False, f"Database error: {e}"

def check_config():
    """Check configuration file"""
    try:
        if os.path.exists("config.json"):
            with open("config.json", 'r') as f:
                config = json.load(f)
            return True, f"Config OK - {len(config)} settings"
        else:
            return False, "Config file not found"
    except Exception as e:
        return False, f"Config error: {e}"

def check_whitelist():
    """Check whitelist file"""
    try:
        if os.path.exists("whitelist.txt"):
            with open("whitelist.txt", 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return True, f"Whitelist OK - {len(lines)} processes"
        else:
            return False, "Whitelist not found"
    except Exception as e:
        return False, f"Whitelist error: {e}"

def check_web_dashboard():
    """Check web dashboard status"""
    try:
        response = requests.get("http://localhost:5000/api/stats", timeout=5)
        if response.status_code == 200:
            return True, "Web Dashboard OK"
        else:
            return False, f"Web Dashboard error: {response.status_code}"
    except requests.exceptions.RequestException:
        return False, "Web Dashboard not running"

def check_process_monitor():
    """Check if process monitor is running"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'])
                if 'detect.py' in cmdline:
                    return True, f"Process Monitor OK - PID {proc.info['pid']}"
        return False, "Process Monitor not running"
    except Exception as e:
        return False, f"Process Monitor check error: {e}"

def main():
    """Main status check"""
    print("School Device Monitor - Status Check")
    print("=" * 50)
    
    checks = [
        ("Database", check_database),
        ("Configuration", check_config),
        ("Whitelist", check_whitelist),
        ("Process Monitor", check_process_monitor),
        ("Web Dashboard", check_web_dashboard)
    ]
    
    all_ok = True
    for name, check_func in checks:
        status, message = check_func()
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {message}")
        if not status:
            all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("🎉 All systems operational!")
    else:
        print("⚠️  Some issues detected. Check the errors above.")
    
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
