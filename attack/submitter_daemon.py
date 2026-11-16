#!/usr/bin/env python3
"""
============================================================================
EXPIRED - DO NOT RUN WHEN USING S4DFARM
============================================================================
S4DFarm (s4dfarm_engine/) is the flag submitter now: its server dedups,
quota-limits and submits. Running this daemon alongside it double-submits.
Kept only as a break-glass fallback if the S4DFarm server is unavailable.

Known bug if you do fall back: a flag that returns ERROR or UNKNOWN
(scoreboard timeout/down) is still recorded, so is_flag_processed() skips it
forever - transient flags are lost, never retried. S4DFarm's QUEUED status
retries them correctly, which is the main reason to prefer the farm.
============================================================================

Flag Submission Daemon
Reads flags from flags_queue.txt, submits them to the scoreboard,
and stores results in SQLite to prevent duplicate submissions.
Supports HTTP_JSON, HTTP_FORM, and TCP_SOCKET protocols configured in config.py.
"""

import time
import re
import os
import sys
import socket
import sqlite3
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from config import (
    SUBMISSION_PROTOCOL,
    SUBMIT_URL,
    TEAM_TOKEN,
    TCP_SUBMIT_HOST,
    TCP_SUBMIT_PORT,
    FLAG_REGEX_STR,
)

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

def parse_scoreboard_response(raw_resp):
    body = raw_resp.strip().lower()
    if any(w in body for w in ["accepted", "correct", "success", "congrat", "ok", "1"]):
        return "ACCEPTED", raw_resp.strip()
    elif any(w in body for w in ["already", "duplicate"]):
        return "DUPLICATE", raw_resp.strip()
    elif any(w in body for w in ["expired", "old"]):
        return "EXPIRED", raw_resp.strip()
    elif any(w in body for w in ["invalid", "wrong", "cannot submit your own"]):
        return "INVALID", raw_resp.strip()
    else:
        return "UNKNOWN", raw_resp.strip()

def send_to_scoreboard(flag):
    try:
        if SUBMISSION_PROTOCOL == "HTTP_JSON":
            payload = {"token": TEAM_TOKEN, "flag": flag}
            resp = requests.post(SUBMIT_URL, json=payload, timeout=4)
            return parse_scoreboard_response(resp.text)

        elif SUBMISSION_PROTOCOL == "HTTP_FORM":
            payload = {"token": TEAM_TOKEN, "flag": flag}
            resp = requests.post(SUBMIT_URL, data=payload, timeout=4)
            return parse_scoreboard_response(resp.text)

        elif SUBMISSION_PROTOCOL == "TCP_SOCKET":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4.0)
            s.connect((TCP_SUBMIT_HOST, TCP_SUBMIT_PORT))
            # Send flag (or token + flag depending on scoreboard format)
            s.sendall(f"{flag}\n".encode())
            raw_data = s.recv(1024).decode(errors="ignore")
            s.close()
            return parse_scoreboard_response(raw_data)

        else:
            return "ERROR", f"Unknown protocol: {SUBMISSION_PROTOCOL}"

    except Exception as e:
        return "ERROR", str(e)

def process_queue():
    if not os.path.exists(FLAG_FILE) or os.path.getsize(FLAG_FILE) == 0:
        return

    # Atomic rotation prevents race conditions where writers append while reading
    proc_file = FLAG_FILE + ".proc"
    try:
        os.replace(FLAG_FILE, proc_file)
    except OSError:
        return

    try:
        with open(proc_file, "r") as f:
            content = f.read()
    finally:
        if os.path.exists(proc_file):
            os.remove(proc_file)

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
    print(f"[*] Protocol:    {SUBMISSION_PROTOCOL}")
    if SUBMISSION_PROTOCOL in ["HTTP_JSON", "HTTP_FORM"]:
        print(f"[*] Submit URL:  {SUBMIT_URL}")
        print(f"[*] Team Token:  {TEAM_TOKEN}")
    else:
        print(f"[*] TCP Target:  {TCP_SUBMIT_HOST}:{TCP_SUBMIT_PORT}")
    print(f"[*] Queue File:  {FLAG_FILE}")
    print(f"[*] Database:    {DB_FILE}")
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
