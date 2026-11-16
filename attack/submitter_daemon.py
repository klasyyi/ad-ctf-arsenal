#!/usr/bin/env python3
"""
Flag Submission Daemon
Reads flags from flags_queue.txt, submits them to the scoreboard,
and stores results in SQLite to prevent duplicate submissions.
"""

import time
import re
import os
import sys
import sqlite3
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from config import SUBMIT_URL, TEAM_TOKEN, FLAG_REGEX_STR

FLAG_FILE = os.path.join(BASE_DIR, "flags_queue.txt")
DB_FILE = os.path.join(BASE_DIR, "submitted_flags.db")
FLAG_REGEX = re.compile(FLAG_REGEX_STR)
SUBMISSION_INTERVAL = 0.5

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
    print("FLAG SUBMISSION DAEMON STARTED")
    print(f"[*] Submit URL: {SUBMIT_URL}")
    print(f"[*] Team Token: {TEAM_TOKEN}")
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
