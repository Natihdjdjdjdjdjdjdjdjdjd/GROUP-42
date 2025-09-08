#!/usr/bin/env python3
"""
School Device Monitor - Web Dashboard
Provides a web interface for monitoring and managing the system.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
import sqlite3
import json
import psutil
import subprocess
import os
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'school_device_monitor_secret_key'

DATABASE_FILE = "events.db"
CONFIG_FILE = "config.json"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_config():
    """Load configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def terminate_process(pid, process_name="Unknown"):
    """Enhanced process termination with multiple methods"""
    try:
        process = psutil.Process(pid)
        process_name = process_name or process.name()
        
        # Method 1: Graceful termination
        try:
            process.terminate()
            process.wait(timeout=3)
            return True, f"Process '{process_name}' terminated gracefully"
        except psutil.TimeoutExpired:
            # Method 2: Force kill if graceful fails
            try:
                process.kill()
                process.wait(timeout=2)
                return True, f"Process '{process_name}' force killed"
            except psutil.TimeoutExpired:
                # Method 3: Use taskkill command for stubborn processes
                try:
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                 capture_output=True, timeout=5, check=True)
                    return True, f"Process '{process_name}' terminated via taskkill"
                except subprocess.CalledProcessError:
                    return False, f"Failed to terminate '{process_name}' - process may be protected"
                except subprocess.TimeoutExpired:
                    return False, f"Timeout while terminating '{process_name}'"
            
    except psutil.NoSuchProcess:
        return False, f"Process '{process_name}' (PID: {pid}) not found"
    except psutil.AccessDenied:
        return False, f"Access denied - '{process_name}' requires administrator privileges"
    except Exception as e:
        return False, f"Error terminating '{process_name}': {str(e)}"

def terminate_multiple_processes(pids):
    """Terminate multiple processes at once"""
    results = []
    for pid in pids:
        success, message = terminate_process(pid)
        results.append({
            'pid': pid,
            'success': success,
            'message': message
        })
    return results

def get_process_details(pid):
    """Get detailed information about a process"""
    try:
        process = psutil.Process(pid)
        return {
            'pid': pid,
            'name': process.name(),
            'exe': process.exe(),
            'cmdline': ' '.join(process.cmdline()),
            'username': process.username(),
            'memory_mb': round(process.memory_info().rss / 1024 / 1024, 1),
            'cpu_percent': round(process.cpu_percent(), 1),
            'create_time': datetime.fromtimestamp(process.create_time()).isoformat(),
            'status': process.status(),
            'num_threads': process.num_threads(),
            'connections': len(process.connections()) if process.connections() else 0
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def get_running_processes():
    """Get currently running unauthorized processes with enhanced details"""
    try:
        # Load whitelist
        whitelist = set()
        try:
            with open("whitelist.txt", 'r') as f:
                for line in f:
                    line = line.strip().lower()
                    if line and not line.startswith('#'):
                        whitelist.add(line)
        except:
            pass
        
        unauthorized_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'exe']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name'].lower()
                
                if proc_name not in whitelist:
                    # Get additional process details
                    try:
                        memory_info = proc.memory_info()
                        cpu_percent = proc.cpu_percent()
                        create_time = datetime.fromtimestamp(proc.create_time())
                        
                        unauthorized_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'username': proc_info['username'],
                            'path': proc_info['exe'] or 'Unknown',
                            'memory_mb': round(memory_info.rss / 1024 / 1024, 1),
                            'cpu_percent': round(cpu_percent, 1),
                            'create_time': create_time.strftime('%H:%M:%S'),
                            'status': proc.status(),
                            'num_threads': proc.num_threads(),
                            'priority': proc.nice()
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by memory usage (highest first)
        unauthorized_processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        return unauthorized_processes
    except Exception as e:
        return []

def log_termination_event(pid, process_name, success, message, user="SYSTEM"):
    """Log termination events to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events (timestamp, process_name, pid, user, path, status, alert_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            process_name,
            pid,
            user,
            "Dashboard Termination",
            "TERMINATED" if success else f"FAILED: {message}",
            "CRITICAL" if success else "WARNING"
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging termination event: {e}")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total events
        cursor.execute("SELECT COUNT(*) as count FROM events")
        total_events = cursor.fetchone()['count']
        
        # Unauthorized events
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE status LIKE '%unauthorized%' OR status LIKE '%detected%'")
        unauthorized_count = cursor.fetchone()['count']
        
        # Today's events
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE DATE(timestamp) = ?", (today,))
        today_events = cursor.fetchone()['count']
        
        # Unique users
        cursor.execute("SELECT COUNT(DISTINCT user) as count FROM events")
        unique_users = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'total_events': total_events,
            'unauthorized_count': unauthorized_count,
            'today_events': today_events,
            'unique_users': unique_users
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/terminate_process', methods=['POST'])
def api_terminate_process():
    """Enhanced API endpoint to terminate a process"""
    try:
        data = request.get_json()
        pid = int(data.get('pid'))
        process_name = data.get('process_name', 'Unknown')
        
        # Get process details before termination
        process_details = get_process_details(pid)
        
        # Attempt termination
        success, message = terminate_process(pid, process_name)
        
        # Log the termination attempt
        log_termination_event(pid, process_name, success, message)
        
        return jsonify({
            'success': success,
            'message': message,
            'pid': pid,
            'process_name': process_name,
            'process_details': process_details
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid PID provided'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 400

@app.route('/api/terminate_multiple', methods=['POST'])
def api_terminate_multiple():
    """Terminate multiple processes at once"""
    try:
        data = request.get_json()
        pids = data.get('pids', [])
        
        if not pids:
            return jsonify({
                'success': False,
                'message': 'No PIDs provided'
            }), 400
        
        results = terminate_multiple_processes(pids)
        
        # Log all termination attempts
        for result in results:
            log_termination_event(
                result['pid'], 
                f"Bulk Termination", 
                result['success'], 
                result['message']
            )
        
        return jsonify({
            'success': True,
            'results': results,
            'total_attempted': len(pids),
            'successful': sum(1 for r in results if r['success'])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 400

@app.route('/api/running_processes')
def api_running_processes():
    """Enhanced API endpoint to get currently running unauthorized processes"""
    try:
        processes = get_running_processes()
        return jsonify({
            'success': True,
            'processes': processes,
            'count': len(processes),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 400

@app.route('/api/process_details/<int:pid>')
def api_process_details(pid):
    """Get detailed information about a specific process"""
    try:
        details = get_process_details(pid)
        if details:
            return jsonify({
                'success': True,
                'process': details
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Process not found or access denied'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 400

@app.route('/api/events')
def get_events():
    """Get events with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status', '')
        alert_level = request.args.get('alert_level', '')
        
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if alert_level:
            query += " AND alert_level = ?"
            params.append(alert_level)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        events = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = "SELECT COUNT(*) as count FROM events WHERE 1=1"
        count_params = []
        
        if status:
            count_query += " AND status = ?"
            count_params.append(status)
        
        if alert_level:
            count_query += " AND alert_level = ?"
            count_params.append(alert_level)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'events': events,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or update configuration"""
    if request.method == 'GET':
        config = load_config()
        return jsonify(config)
    else:
        try:
            new_config = request.json
            with open(CONFIG_FILE, 'w') as f:
                json.dump(new_config, f, indent=2)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/whitelist', methods=['GET', 'POST'])
def whitelist():
    """Get or update whitelist"""
    whitelist_file = "whitelist.txt"
    
    if request.method == 'GET':
        try:
            with open(whitelist_file, 'r') as f:
                content = f.read()
            return jsonify({'content': content})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            content = request.json['content']
            with open(whitelist_file, 'w') as f:
                f.write(content)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
