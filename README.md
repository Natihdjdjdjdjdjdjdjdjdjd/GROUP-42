# GROUP-42
School Device Monitor — README.md

What it is
A simple Windows process-based detector that watches running programs, compares them to a whitelist, logs unknown processes, and alerts the admin.

Quick features

   - Polls running processes with psutil every few seconds

   - Compares process names to whitelist.txt

   - Logs events to events.db (SQLite) with timestamp, user, PID, path

   - Easy to run for testing or package as a Windows service for production

Requirements

    - Windows machine (Admin access for full visibility)

    - Python 3.8+

    - Libraries: psutil (optional: win10toast for popups)

Install:

    - pip install psutil
    # optional: pip install win10toast

Files

   - detect.py — main script

   - whitelist.txt — one allowed process name per line (lowercase)

   - events.db — SQLite database created automatically

Example whitelist.txt:

          explorer.exe
          chrome.exe
          notepad.exe
          zoom.exe

Run (quick test)
 
   - Open PowerShell/CMD as Administrator.

   - Run:

        - python detect.py


    - Launch an app not in whitelist.txt and watch the console. Check events.db for records.

    - View DB:

      sqlite3 events.db "SELECT * FROM events ORDER BY ts DESC LIMIT 10;"
      Or open with DB Browser for SQLite.

- Package & service (basic)

Create exe:

          - pip install pyinstaller
          - pyinstaller --onefile detect.py

          
# result: dist\detect.exe


- Install as Windows service using NSSM:

- Download nssm.exe, then:

- nssm install DetectService "C:\full\path\to\dist\detect.exe"
- nssm start DetectService


Run these commands as Administrator.

 - Configurable settings

 - POLL_SECONDS in detect.py — default 5 seconds (adjust for performance)

 - Whitelist format — process names only at start; can be extended to path/sha256 later

Operational notes

  - Start in audit only (alerts + logs). Don’t auto-terminate processes until whitelist is stable.

  - Run the service under an account with rights to read process exe paths (SYSTEM or admin).

  - Protect and version whitelist.txt (serve updates securely if centralizing).

Next steps (recommended)

   - Tune whitelist.txt during a 1–2 week pilot.

   - Add pop-up or email alerts if needed.

   - Consider centralizing logs (SIEM/Wazuh) for scale.
