# School Device Monitor - Installation Guide

## Quick Start

### Prerequisites
- Windows 10/11
- Python 3.8 or higher
- Administrator access (recommended for full process visibility)

### Installation Steps

1. **Install Python Dependencies**
   ```powershell
   py -m pip install -r requirements.txt
   ```

2. **Run the Monitor**
   ```powershell
   py detect.py
   ```

3. **View Events**
   ```powershell
   py view_events.py recent 10
   py view_events.py unauthorized
   py view_events.py stats
   ```

## Configuration

### Whitelist Management
The `whitelist.txt` file contains allowed process names. Edit this file to:
- Add new allowed applications
- Remove applications that should be blocked
- Use comments (lines starting with #)

Example whitelist entry:
```
# Web browsers
chrome.exe
firefox.exe
msedge.exe

# Office applications
word.exe
excel.exe
powerpnt.exe
```

### Polling Interval
Edit `POLL_SECONDS` in `detect.py` to change how often processes are checked:
```python
POLL_SECONDS = 5  # Check every 5 seconds
```

## Usage Examples

### Basic Monitoring
```powershell
# Start monitoring (runs continuously)
py detect.py
```

### View Recent Events
```powershell
# View last 10 events
py view_events.py recent 10

# View only unauthorized processes
py view_events.py unauthorized

# View database statistics
py view_events.py stats
```

### Testing
```powershell
# Run quick functionality test
py test_monitor.py
```

## Database Schema

The `events.db` SQLite database contains:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | ISO format timestamp |
| process_name | TEXT | Name of the process |
| pid | INTEGER | Process ID |
| user | TEXT | Username running the process |
| path | TEXT | Full path to executable |
| status | TEXT | Status (UNAUTHORIZED) |

## Troubleshooting

### Common Issues

1. **"Access Denied" errors**
   - Run PowerShell as Administrator
   - Some system processes require elevated privileges

2. **No unauthorized processes detected**
   - Check if whitelist.txt is properly formatted
   - Verify process names are lowercase
   - Ensure no extra spaces or characters

3. **Database errors**
   - Delete `events.db` to reset the database
   - Check file permissions in the project directory

### Performance Tips

- Increase `POLL_SECONDS` for better performance
- Regularly clean up old database entries
- Monitor system resources during operation

## Security Considerations

- Run as Administrator for full process visibility
- Protect `whitelist.txt` from unauthorized modification
- Regularly review unauthorized process logs
- Consider implementing process termination for production use

## Next Steps

1. **Tune the whitelist** during a 1-2 week pilot
2. **Add Windows toast notifications** for real-time alerts
3. **Implement process termination** for unauthorized applications
4. **Set up centralized logging** for multiple devices
5. **Create Windows service** for background operation
