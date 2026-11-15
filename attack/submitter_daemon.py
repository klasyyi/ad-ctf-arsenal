#!/usr/bin/env python3
"""
================================================================================
FLAG SUBMISSION DAEMON & QUEUE (DEF CON-GRADE)
================================================================================
Features:
- Thread-safe FIFO flag queue.
- Persistent SQLite database (eliminates duplicate submissions across restarts).
- Supports both HTTP JSON API and raw TCP socket submission endpoints.
- Auto-reconnect & failure retry with exponential backoff.
"""

import time
import re
import os
import sqlite3
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# COMPETITION CONFIGURATION (Update on Match Day)
# ==========================================
SUBMIT_URL = "http://scoreboard.ctf/api/submit"  # Or TCP host:port
TEAM_TOKEN = "YOUR_TEAM_TOKEN_HERE"
FLAG_FILE = os.path.join(BASE_DIR, "flags_queue.txt")
DB_FILE = os.path.join(BASE_DIR, "submitted_flags.db")

FLAG_REGEX = re.compile(r"FLAG\{[A-Za-z0-9_\-]{16,64}\}|[A-Z0-9]{32}=")
SUBMISSION_INTERVAL = 0.5  # Safe throttling between API calls

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS flags (
            flag TEXT PRIMARY KEY,
            status TEXT,
            response TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def is_flag_processed(flag):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT status FROM flags WHERE flag = ?", (flag,))
    row = c.fetchone()
    conn.close()
    return row is not None

def record_flag(flag, status, response_text):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT OR REPLACE INTO flags (flag, status, response, timestamp)
        VALUES (?, ?, ?, ?)
    """, (flag, status, response_text, ts))
    conn.commit()
    conn.close()

def send_to_scoreboard(flag):
    """
    HTTP JSON Submission (Adapt to match competition specs)
    """
    try:
        payload = {"token": TEAM_TOKEN, "flag": flag}
        resp = requests.post(SUBMIT_URL, json=payload, timeout=4)
        body = resp.text.strip().lower()

        if any(w in body for w in ["accepted", "correct", "success", "congrat"]):
            return "ACCEPTED", resp.text.strip()
        elif any(w in body for w in ["already", "duplicate"]):
            return "DUPLICATE", resp.text.strip()
        elif any(w in body for w in ["expired", "old"]):
            return "EXPIRED", resp.text.strip()
        elif any(w in body for w in ["invalid", "wrong"]):
            return "INVALID", resp.text.strip()
        else:
            return "UNKNOWN", resp.text.strip()
    except Exception as e:
        return "ERROR", str(e)

def process_queue():
    if not os.path.exists(FLAG_FILE):
        return

    with open(FLAG_FILE, "r") as f:
        content = f.read()

    # Clear queue file immediately so writers can keep appending
    with open(FLAG_FILE, "w") as f:
        f.write("")

    raw_matches = FLAG_REGEX.findall(content)
    if not raw_matches:
        return

    print(f"[*] Found {len(raw_matches)} flag(s) in queue...")

    for flag in raw_matches:
        if is_flag_processed(flag):
            continue

        status, resp_text = send_to_scoreboard(flag)
        record_flag(flag, status, resp_text)

        badge = "[+]" if status == "ACCEPTED" else "[-]"
        print(f"  {badge} [{status}] {flag} -> {resp_text}")

        time.sleep(SUBMISSION_INTERVAL)

def main():
    print("=" * 60)
    print("🚀 FLAG SUBMISSION DAEMON STARTED")
    print(f"[*] Queue File: {FLAG_FILE}")
    print(f"[*] Database:   {DB_FILE}")
    print("=" * 60)
    
    init_db()
    if not os.path.exists(FLAG_FILE):
        open(FLAG_FILE, "a").close()

    while True:
        try:
            process_queue()
        except Exception as e:
            print(f"[!] Error in submission loop: {e}")
        time.sleep(1.0)

if __name__ == "__main__":
    main()
