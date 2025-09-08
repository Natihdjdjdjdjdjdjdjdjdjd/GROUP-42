#!/usr/bin/env python3
"""
School Device Monitor - Process Detection Script
Monitors running processes and compares them against a whitelist.
Enhanced with notifications, process termination, and advanced features.
"""

import psutil
import sqlite3
import time
import os
import sys
import json
import hashlib
import smtplib
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Try to import win10toast for notifications
try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False
    print("Warning: win10toast not available. Toast notifications disabled.")

# Configuration
WHITELIST_FILE = "whitelist.txt"
DATABASE_FILE = "events.db"
CONFIG_FILE = "config.json"
HASH_CACHE_FILE = "hash_cache.json"

# Default configuration
DEFAULT_CONFIG = {
    "poll_seconds": 5,
    "enable_toast": True,
    "enable_email": False,
    "enable_process_termination": False,
    "enable_hash_verification": False,
    "email_settings": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "to_email": "",
        "from_email": ""
    },
    "alert_levels": {
        "critical_processes": ["cmd.exe", "powershell.exe", "regedit.exe", "taskmgr.exe"],
        "warning_processes": ["notepad.exe", "calc.exe"],
        "info_processes": []
    },
    "alert_frequency": {
        "max_alerts_per_hour": 10,
        "suppress_duplicates_minutes": 5
    },
    "termination_settings": {
        "terminate_critical": True,
        "terminate_warning": False,
        "terminate_info": False,
        "grace_period_seconds": 30
    },
    "database_settings": {
        "max_days_to_keep": 30,
        "cleanup_interval_hours": 24
    }
}

class ProcessMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.whitelist = self.load_whitelist()
        self.db_conn = None
        self.setup_database()
        self.toast = None
        self.alert_history = {}
        self.hash_cache = self.load_hash_cache()
        self.setup_notifications()
        self.last_cleanup = time.time()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self.cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for missing keys
                    merged_config = DEFAULT_CONFIG.copy()
                    merged_config.update(config)
                    return merged_config
            else:
                # Create default config file
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=2)
                print(f"Created default configuration: {CONFIG_FILE}")
                return DEFAULT_CONFIG
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return DEFAULT_CONFIG
    
    def load_hash_cache(self):
        """Load hash cache for file verification"""
        try:
            if os.path.exists(HASH_CACHE_FILE):
                with open(HASH_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading hash cache: {e}")
        return {}
    
    def save_hash_cache(self):
        """Save hash cache to file"""
        try:
            with open(HASH_CACHE_FILE, 'w') as f:
                json.dump(self.hash_cache, f, indent=2)
        except Exception as e:
            print(f"Error saving hash cache: {e}")
    
    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        try:
            if file_path in self.hash_cache:
                return self.hash_cache[file_path]
            
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            
            file_hash = hash_sha256.hexdigest()
            self.hash_cache[file_path] = file_hash
            return file_hash
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def setup_notifications(self):
        """Setup notification systems"""
        if TOAST_AVAILABLE and self.config["enable_toast"]:
            self.toast = ToastNotifier()
            print("Toast notifications enabled")
        else:
            print("Toast notifications disabled")
    
    def load_whitelist(self):
        """Load allowed process names from whitelist.txt"""
        whitelist = set()
        try:
            if os.path.exists(WHITELIST_FILE):
                with open(WHITELIST_FILE, 'r') as f:
                    for line in f:
                        process_name = line.strip().lower()
                        if process_name and not line.startswith('#'):
                            whitelist.add(process_name)
                print(f"Loaded {len(whitelist)} processes from whitelist")
            else:
                print(f"Warning: {WHITELIST_FILE} not found. Creating default whitelist.")
                self.create_default_whitelist()
                whitelist = self.load_whitelist()
        except Exception as e:
            print(f"Error loading whitelist: {e}")
        return whitelist
    
    def create_default_whitelist(self):
        """Create a default whitelist with common Windows processes"""
        default_processes = [
            "explorer.exe",
            "chrome.exe",
            "notepad.exe",
            "zoom.exe",
            "teams.exe",
            "outlook.exe",
            "word.exe",
            "excel.exe",
            "powerpnt.exe",
            "winlogon.exe",
            "lsass.exe",
            "services.exe",
            "svchost.exe",
            "wininit.exe",
            "csrss.exe",
            "conhost.exe",
            "dwm.exe",
            "taskmgr.exe",
            "cmd.exe",
            "powershell.exe"
        ]
        
        with open(WHITELIST_FILE, 'w') as f:
            for process in default_processes:
                f.write(f"{process}\n")
        print(f"Created default whitelist with {len(default_processes)} processes")
    
    def setup_database(self):
        """Initialize SQLite database for event logging"""
        try:
            self.db_conn = sqlite3.connect(DATABASE_FILE)
            cursor = self.db_conn.cursor()
            
            # Create events table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
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
            
            self.db_conn.commit()
            print(f"Database initialized: {DATABASE_FILE}")
        except Exception as e:
            print(f"Error setting up database: {e}")
    
    def cleanup_worker(self):
        """Background worker for database cleanup"""
        while True:
            try:
                time.sleep(3600)  # Check every hour
                self.cleanup_old_records()
            except Exception as e:
                print(f"Error in cleanup worker: {e}")
    
    def cleanup_old_records(self):
        """Remove old database records"""
        try:
            max_days = self.config["database_settings"]["max_days_to_keep"]
            cutoff_date = datetime.now() - timedelta(days=max_days)
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
                DELETE FROM events 
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            self.db_conn.commit()
            
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old records")
                
        except Exception as e:
            print(f"Error cleaning up old records: {e}")
    
    def get_alert_level(self, process_name):
        """Determine alert level for a process"""
        critical = self.config["alert_levels"]["critical_processes"]
        warning = self.config["alert_levels"]["warning_processes"]
        
        if process_name in critical:
            return "CRITICAL"
        elif process_name in warning:
            return "WARNING"
        else:
            return "INFO"
    
    def should_send_alert(self, process_name, alert_level):
        """Check if we should send an alert based on frequency limits"""
        now = time.time()
        key = f"{process_name}_{alert_level}"
        
        # Clean old entries
        self.alert_history = {k: v for k, v in self.alert_history.items() 
                             if now - v < 3600}  # Keep last hour
        
        if key in self.alert_history:
            last_alert = self.alert_history[key]
            suppress_minutes = self.config["alert_frequency"]["suppress_duplicates_minutes"]
            if now - last_alert < suppress_minutes * 60:
                return False
        
        # Check hourly limit
        alerts_this_hour = len([v for v in self.alert_history.values() 
                               if now - v < 3600])
        if alerts_this_hour >= self.config["alert_frequency"]["max_alerts_per_hour"]:
            return False
        
        self.alert_history[key] = now
        return True
    
    def should_terminate_process(self, alert_level):
        """Check if process should be terminated based on alert level"""
        termination_settings = self.config["termination_settings"]
        
        if alert_level == "CRITICAL" and termination_settings["terminate_critical"]:
            return True
        elif alert_level == "WARNING" and termination_settings["terminate_warning"]:
            return True
        elif alert_level == "INFO" and termination_settings["terminate_info"]:
            return True
        
        return False
    
    def terminate_process(self, pid, process_name):
        """Terminate a process"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for graceful termination
            try:
                process.wait(timeout=self.config["termination_settings"]["grace_period_seconds"])
                action = "TERMINATED"
            except psutil.TimeoutExpired:
                process.kill()
                action = "FORCE_KILLED"
            
            print(f"Process {process_name} (PID: {pid}) {action.lower()}")
            return action
            
        except psutil.NoSuchProcess:
            print(f"Process {process_name} (PID: {pid}) already terminated")
            return "ALREADY_TERMINATED"
        except Exception as e:
            print(f"Error terminating process {process_name} (PID: {pid}): {e}")
            return "ERROR"
    
    def send_toast_notification(self, process_name, pid, user, alert_level, action="LOGGED"):
        """Send Windows toast notification"""
        if not self.toast:
            return
        
        title = f"Unauthorized Process - {alert_level}"
        message = f"Process: {process_name}\nPID: {pid}\nUser: {user}\nAction: {action}"
        
        try:
            self.toast.show_toast(title, message, duration=10, threaded=True)
        except Exception as e:
            print(f"Error sending toast notification: {e}")
    
    def send_email_alert(self, process_name, pid, user, path, alert_level, action="LOGGED"):
        """Send email alert"""
        if not self.config["enable_email"]:
            return
        
        email_config = self.config["email_settings"]
        if not all([email_config["username"], email_config["password"], 
                   email_config["to_email"], email_config["from_email"]]):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config["from_email"]
            msg['To'] = email_config["to_email"]
            msg['Subject'] = f"School Device Monitor Alert - {alert_level}"
            
            body = f"""
            Unauthorized Process Detected
            
            Alert Level: {alert_level}
            Process Name: {process_name}
            Process ID: {pid}
            User: {user}
            Path: {path}
            Action Taken: {action}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            This is an automated alert from the School Device Monitor.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()
            
            print(f"Email alert sent for {process_name}")
            
        except Exception as e:
            print(f"Error sending email alert: {e}")
    
    def log_event(self, process_name, pid, user, path, status, alert_level="INFO", file_hash=None, action="LOGGED"):
        """Log an event to the database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO events (timestamp, process_name, pid, user, path, status, alert_level, file_hash, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), process_name, pid, user, path, status, alert_level, file_hash, action))
            self.db_conn.commit()
        except Exception as e:
            print(f"Error logging event: {e}")
    
    def get_process_info(self, process):
        """Get detailed information about a process"""
        try:
            process_name = process.name().lower()
            pid = process.pid
            
            # Get user info
            try:
                user = process.username()
            except:
                user = "Unknown"
            
            # Get executable path
            try:
                path = process.exe()
            except:
                path = "Unknown"
            
            return process_name, pid, user, path
        except Exception as e:
            return None, None, None, None
    
    def scan_processes(self):
        """Scan all running processes and check against whitelist"""
        unauthorized_processes = []
        
        try:
            for process in psutil.process_iter(['pid', 'name', 'username', 'exe']):
                try:
                    process_name, pid, user, path = self.get_process_info(process)
                    
                    if process_name is None:
                        continue
                    
                    # Check if process is in whitelist
                    if process_name not in self.whitelist:
                        alert_level = self.get_alert_level(process_name)
                        file_hash = None
                        action = "LOGGED"
                        
                        # Calculate file hash if enabled
                        if self.config["enable_hash_verification"] and path != "Unknown":
                            file_hash = self.calculate_file_hash(path)
                        
                        # Determine action to take
                        if self.should_terminate_process(alert_level):
                            action = self.terminate_process(pid, process_name)
                        
                        unauthorized_processes.append({
                            'name': process_name,
                            'pid': pid,
                            'user': user,
                            'path': path,
                            'alert_level': alert_level,
                            'file_hash': file_hash,
                            'action': action
                        })
                        
                        # Log unauthorized process
                        self.log_event(process_name, pid, user, path, "UNAUTHORIZED", 
                                     alert_level, file_hash, action)
                        
                        # Send alerts if configured
                        if self.should_send_alert(process_name, alert_level):
                            if alert_level in ["CRITICAL", "WARNING"]:
                                self.send_toast_notification(process_name, pid, user, alert_level, action)
                                self.send_email_alert(process_name, pid, user, path, alert_level, action)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            print(f"Error scanning processes: {e}")
        
        return unauthorized_processes
    
    def run(self):
        """Main monitoring loop"""
        poll_seconds = self.config["poll_seconds"]
        
        print("School Device Monitor - Enhanced Process Detection")
        print("=" * 60)
        print(f"Polling every {poll_seconds} seconds")
        print(f"Whitelist contains {len(self.whitelist)} processes")
        print(f"Toast notifications: {'Enabled' if self.toast else 'Disabled'}")
        print(f"Email alerts: {'Enabled' if self.config['enable_email'] else 'Disabled'}")
        print(f"Process termination: {'Enabled' if self.config['enable_process_termination'] else 'Disabled'}")
        print(f"Hash verification: {'Enabled' if self.config['enable_hash_verification'] else 'Disabled'}")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        try:
            while True:
                unauthorized = self.scan_processes()
                
                if unauthorized:
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"Found {len(unauthorized)} unauthorized process(es):")
                    for proc in unauthorized:
                        level_icon = {"CRITICAL": "", "WARNING": "⚠️", "INFO": "ℹ️"}
                        icon = level_icon.get(proc['alert_level'], "ℹ️")
                        action_icon = {"TERMINATED": "💀", "FORCE_KILLED": "", "LOGGED": "📝"}
                        action_icon_char = action_icon.get(proc['action'], "📝")
                        
                        print(f"  {icon} {proc['name']} (PID: {proc['pid']}, User: {proc['user']}, "
                              f"Level: {proc['alert_level']}) {action_icon_char}")
                        if proc['path'] != "Unknown":
                            print(f"    Path: {proc['path']}")
                        if proc['file_hash']:
                            print(f"    Hash: {proc['file_hash'][:16]}...")
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"All processes are authorized")
                
                time.sleep(poll_seconds)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
        finally:
            if self.db_conn:
                self.db_conn.close()
            self.save_hash_cache()

def main():
    """Main entry point"""
    try:
        monitor = ProcessMonitor()
        monitor.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
