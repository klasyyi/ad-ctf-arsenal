#!/usr/bin/env python3
"""
================================================================================
ATTACK & DEFENSE CTF ARENA SIMULATOR (FULL MATCH DRILL)
================================================================================
Simulates a real live A/D CTF competition on your machine:
- Live Scoreboard Server (Port 9000) with real-time CLI dashboard.
- 3 Teams with vulnerable web services:
    * Team 1 (YOU):   http://127.0.0.1:8001
    * Team 2 (Enemy): http://127.0.0.1:8002
    * Team 3 (Enemy): http://127.0.0.1:8003
- Organizer SLA Bot:
    * Advances Ticks every 20 seconds.
    * Plants new flags into each team's service every tick.
    * Checks SLA health (Green if up, Red if down).
- Enemy AI Attacker (Team 3):
    * Attacks YOUR Team 1 every tick to steal your flag!
    * Watches you lose defense points until you patch or defend!

Usage:
    python sim_arena.py
================================================================================
"""

import sys
import os
import time
import json
import random
import string
import threading
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==============================================================================
# CONFIGURATION
# ==============================================================================
TICK_DURATION = 20  # Fast 20-second ticks for practical training
SCOREBOARD_PORT = 9000

TEAM_CONFIG = {
    "team1": {"name": "Team 1 (YOU)",   "port": 8001, "token": "TOKEN_TEAM1"},
    "team2": {"name": "Team 2 (Enemy)", "port": 8002, "token": "TOKEN_TEAM2"},
    "team3": {"name": "Team 3 (Enemy)", "port": 8003, "token": "TOKEN_TEAM3"},
}

# Game State
current_tick = 1
lock = threading.Lock()

# Flags: { flag_string: {"team": "teamX", "tick": N, "valid_until": N + 2} }
active_flags = {}

# Scores: { "teamX": {"attack": 0, "defense": 0, "sla": "UP"} }
scores = {
    "team1": {"attack": 0, "defense": 0, "sla": "UP"},
    "team2": {"attack": 0, "defense": 0, "sla": "UP"},
    "team3": {"attack": 0, "defense": 0, "sla": "UP"},
}

submitted_flags_history = set()

# Services in-memory storage: { "teamX": [ {"id": 1, "flag": "..."}, ... ] }
services_db = {
    "team1": [],
    "team2": [],
    "team3": [],
}

# Patch status for Team 1 (Can be toggled in menu or file)
team1_patched = False

# ==============================================================================
# 1. VULNERABLE SERVICE HANDLER (One instance per team)
# ==============================================================================
class VulnerableServiceHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # Suppress default noisy console logs

    def get_team_id(self):
        port = self.server.server_address[1]
        for tid, cfg in TEAM_CONFIG.items():
            if cfg["port"] == port:
                return tid
        return "team1"

    def do_GET(self):
        tid = self.get_team_id()
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Check if service is down / killed
        if scores[tid]["sla"] == "DOWN":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"500 Internal Server Error")
            return

        # Profile / Notes API endpoint
        if "/api/v1/profile" in parsed.path or "/api/note" in parsed.path:
            raw_id = params.get("id", [""])[0]

            # VULNERABILITY: If SQLi string detected, leak newest flag!
            is_sqli = any(kw in raw_id.upper() for kw in ["UNION", "SELECT", "OR 1=1", "OR '1'='1", "ALL"])

            # Check if Team 1 is patched
            if tid == "team1" and team1_patched:
                # Patch blocks SQLi without breaking normal numeric lookups
                if is_sqli:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "blocked", "message": "Input sanitized."}).encode())
                    return

            with lock:
                records = services_db[tid]
                newest = records[-1] if records else {"id": 1, "flag": "NO_FLAGS_YET"}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            if is_sqli:
                # Exploit triggered! Leaks the newest flag
                resp = {
                    "id": newest["id"],
                    "username": f"user_{tid}",
                    "bio": f"Secret: {newest['flag']}",
                    "flag": newest["flag"]
                }
            else:
                # Normal legitimate SLA bot request
                resp = {
                    "id": newest["id"],
                    "username": f"user_{tid}",
                    "bio": "Normal user account bio.",
                    "status": "active"
                }

            self.wfile.write(json.dumps(resp).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h3>Service {tid} is online.</h3>".encode())

# ==============================================================================
# 2. SCOREBOARD & SUBMISSION API HANDLER (Port 9000)
# ==============================================================================
class ScoreboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_POST(self):
        if self.path == "/api/submit":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(post_body)
            except Exception:
                data = {}

            token = data.get("token", "")
            flag = data.get("flag", "").strip()

            # Find which team is submitting
            submitting_team = None
            for tid, cfg in TEAM_CONFIG.items():
                if cfg["token"] == token or token == "YOUR_TEAM_TOKEN_HERE":
                    submitting_team = tid if token != "YOUR_TEAM_TOKEN_HERE" else "team1"
                    break

            if not submitting_team:
                self.respond_json(403, {"status": "error", "message": "Invalid team token"})
                return

            # Verification
            with lock:
                if flag in submitted_flags_history:
                    self.respond_json(200, {"status": "duplicate", "message": "Flag already submitted"})
                    return

                if flag not in active_flags:
                    self.respond_json(200, {"status": "invalid", "message": "Flag invalid or unknown"})
                    return

                flag_info = active_flags[flag]

                # Check if it's their own flag
                if flag_info["team"] == submitting_team:
                    self.respond_json(200, {"status": "rejected", "message": "Cannot submit your own flag!"})
                    return

                # Check expiry
                if current_tick > flag_info["valid_until"]:
                    self.respond_json(200, {"status": "expired", "message": "Flag expired"})
                    return

                # SUCCESSFUL EXPLOIT!
                submitted_flags_history.add(flag)
                victim_team = flag_info["team"]

                # +100 Attack points to attacker, -50 Defense points from victim
                scores[submitting_team]["attack"] += 100
                scores[victim_team]["defense"] -= 50

            self.respond_json(200, {
                "status": "accepted",
                "message": f"SUCCESS! Captured flag from {victim_team}! (+100 Attack Points)"
            })
        else:
            self.respond_json(404, {"error": "Endpoint not found"})

    def respond_json(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

# ==============================================================================
# 3. ORGANIZER SLA BOT ENGINE
# ==============================================================================
def sla_bot_loop():
    global current_tick
    while True:
        time.sleep(TICK_DURATION)
        with lock:
            current_tick += 1
            # Award +50 Defense points to each team that is UP
            for tid, sc in scores.items():
                if sc["sla"] == "UP":
                    sc["defense"] += 50

            # Plant fresh flags
            for tid in TEAM_CONFIG.keys():
                rand_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
                flag_str = f"FLAG{{{tid.upper()}_TICK{current_tick}_{rand_id}}}"

                # Store active flag (valid for 2 ticks)
                active_flags[flag_str] = {
                    "team": tid,
                    "tick": current_tick,
                    "valid_until": current_tick + 2
                }

                # Plant into service
                services_db[tid].append({
                    "id": len(services_db[tid]) + 1,
                    "flag": flag_str,
                    "tick": current_tick
                })

# ==============================================================================
# 4. ENEMY ATTACKER BOT (Team 3 attacks YOU)
# ==============================================================================
def enemy_attacker_loop():
    """Team 3 periodically attacks Team 1 (You) using SQL injection!"""
    import urllib.request
    time.sleep(5)  # Wait for first tick
    while True:
        time.sleep(TICK_DURATION)
        try:
            # Team 3 exploits Team 1 on port 8001
            url = "http://127.0.0.1:8001/api/v1/profile?id=-1'%20UNION%20SELECT%201,flag,3%20FROM%20flags--%20-"
            req = urllib.request.Request(url, headers={"User-Agent": "EnemyBot-Team3"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                stolen_flag = data.get("flag", "")
                
                # If Team 3 stole your flag, they submit it to Scoreboard!
                if stolen_flag and stolen_flag.startswith("FLAG{TEAM1"):
                    submit_req = urllib.request.Request(
                        "http://127.0.0.1:9000/api/submit",
                        data=json.dumps({"token": "TOKEN_TEAM3", "flag": stolen_flag}).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                    urllib.request.urlopen(submit_req, timeout=3)
        except Exception:
            pass

# ==============================================================================
# 5. LIVE DASHBOARD DISPLAY
# ==============================================================================
def dashboard_loop():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=" * 72)
        print(f"  ATTACK & DEFENSE CTF ARENA  |  TICK: {current_tick} (Duration: {TICK_DURATION}s)")
        print(f"  Scoreboard: http://127.0.0.1:{SCOREBOARD_PORT}")
        print("=" * 72)
        print(f"  {'TEAM':<18} | {'PORT':<6} | {'DEFENSE':<8} | {'ATTACK':<8} | {'TOTAL':<8} | {'SLA'}")
        print("-" * 72)

        with lock:
            sorted_teams = sorted(
                scores.items(),
                key=lambda x: (x[1]["defense"] + x[1]["attack"]),
                reverse=True
            )
            for tid, sc in sorted_teams:
                cfg = TEAM_CONFIG[tid]
                total = sc["defense"] + sc["attack"]
                sla_str = "[ UP ]" if sc["sla"] == "UP" else "[DOWN]"
                patch_tag = " (PATCHED)" if tid == "team1" and team1_patched else ""
                print(f"  {cfg['name'] + patch_tag:<18} | {cfg['port']:<6} | {sc['defense']:<8} | {sc['attack']:<8} | {total:<8} | {sla_str}")

        print("-" * 72)
        print("  TARGETS TO ATTACK WITH YOUR SCRIPTS:")
        print("    Team 2: http://127.0.0.1:8002/api/v1/profile")
        print("    Team 3: http://127.0.0.1:8003/api/v1/profile")
        print("=" * 72)
        print("  PRESS 'p' + ENTER to Toggle Patch for Team 1 (Block enemy attacks)")
        print("  PRESS 'Ctrl+C' to Exit Arena")
        print("=" * 72)
        time.sleep(3)

# ==============================================================================
# ENTRY POINT
# ==============================================================================
def main():
    global team1_patched
    print("[*] Initializing CTF Simulation Arena...")

    # 1. Start Team Services
    for tid, cfg in TEAM_CONFIG.items():
        server = HTTPServer(("127.0.0.1", cfg["port"]), VulnerableServiceHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()

    # 2. Start Scoreboard
    sb_server = HTTPServer(("127.0.0.1", SCOREBOARD_PORT), ScoreboardHandler)
    threading.Thread(target=sb_server.serve_forever, daemon=True).start()

    # 3. Initialize Tick 1 with flags
    with lock:
        for tid in TEAM_CONFIG.keys():
            flag_str = f"FLAG{{{tid.upper()}_TICK1_INIT112233}}"
            active_flags[flag_str] = {"team": tid, "tick": 1, "valid_until": 3}
            services_db[tid].append({"id": 1, "flag": flag_str, "tick": 1})

    # 4. Start Background Engines
    threading.Thread(target=sla_bot_loop, daemon=True).start()
    threading.Thread(target=enemy_attacker_loop, daemon=True).start()
    threading.Thread(target=dashboard_loop, daemon=True).start()

    # Interactive key listener for patching toggle
    while True:
        try:
            cmd = input()
            if cmd.strip().lower() == "p":
                team1_patched = not team1_patched
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting Arena.")
            sys.exit(0)

if __name__ == "__main__":
    main()
