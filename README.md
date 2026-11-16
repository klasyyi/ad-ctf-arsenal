# AD-CTF Arsenal: 24-Hour Attack & Defense Automation Framework

Lightweight, production-grade automation suite for 24-hour Attack & Defense CTF competitions. Compliant with strict competition rules: zero AI, zero firewall/iptables changes, no port scanning, and mandatory >=2.0s rate limiting.

---

## Repository Structure

```text
ad-ctf-arsenal/
├── README.md                 # Match day protocol and command reference
├── .gitignore                # Excludes runtime DBs, PCAPs, logs
├── bootstrap/
│   ├── setup_pwnbox.sh       # One-click bootstrap installer
│   ├── tmux.conf             # Ergonomic tmux configuration
│   └── aliases.sh            # Shell aliases (flaggrep, submit-flag, ports)
├── attack/
│   ├── submitter_daemon.py   # Flag submission queue with SQLite deduplication
│   ├── exploit_web.py        # Web exploit runner (2.1s delay per target)
│   ├── exploit_pwn.py        # Pwntools socket exploit runner (2.1s delay)
│   ├── exploit_replay.py     # Replay engine for captured enemy payloads
│   └── targets.txt           # Configurable target IP list
├── defense/
│   ├── backup_services.sh    # Initial service snapshot & Git initializer
│   ├── bot_watcher.sh        # Radar 1: Real-time SLA bot request watcher
│   ├── proxy_logger.py       # Zero-firewall Layer 7 proxy logger
│   ├── waf_php_shim.php      # PHP WAF shim (safe 200 OK exits)
│   └── waf_python_shim.py    # Python/Flask WAF shim (safe 200 OK exits)
├── traffic/
│   ├── sniffer.py            # Radar 2: Live packet sniffer & exploit dumper
│   └── pcap_dump.sh          # Rolling 60s tcpdump ring buffer
└── manual/
    ├── FIRST_HOUR_CHECKLIST.md         # Minute-by-minute startup checklist
    ├── GAME_DYNAMICS_AND_CHEATCODES.md # Bot tracking, exploit theft, SLA rules
    ├── FIELD_MANUAL.md                 # Offline cheat sheet (SQLi, SSTI, Pwn)
    └── PLAYBOOK.md                     # General rules and shift rotation
```

---

## Step-by-Step Match Day Protocol (From 10:00 AM)

### Step 1: Boot & Arm (00:00 - 00:05)
Open the Pwnbox terminal and run:
```bash
git clone https://github.com/klasyyi/ad-ctf-arsenal.git
cd ad-ctf-arsenal
chmod +x bootstrap/setup_pwnbox.sh && ./bootstrap/setup_pwnbox.sh
source ~/.bashrc
tmux
```

### Step 2: Lock Down & Launch Radars (00:05 - 00:15)
Do not modify any challenge code yet. Run these background defenses:
```bash
# 1. Snapshot services and initialize Git rollback
sudo ./defense/backup_services.sh

# 2. Start the central flag submitter
python3 attack/submitter_daemon.py &

# 3. Start Radar 2 (Enemy Packet Sniffer)
sudo python3 traffic/sniffer.py eth0 &

# 4. Start Radar 1 (Organizer Bot Watcher)
chmod +x defense/bot_watcher.sh && ./defense/bot_watcher.sh &
```
*Check scoreboard: Confirm your services start GREEN.*

### Step 3: Discover Flag Sink & Endpoints (00:15 - 00:30)
1. Check output in the Bot Watcher window:
   - Identify the active URLs visited by the bot (e.g. `POST /api/notes`, `GET /profile`).
   - Identify where the flag is placed (database table, `/flag.txt`, etc.).
2. Configure credentials:
   - Open `attack/submitter_daemon.py` and set `SUBMIT_URL` and `TEAM_TOKEN`.
   - Open `attack/targets.txt` and verify target IP range matches the scoreboard format.

### Step 4: Attack Execution & Replay (00:30 Onward)
1. Launch custom web or binary attacks:
   ```bash
   python3 attack/exploit_web.py
   python3 attack/exploit_pwn.py
   ```
2. Counter-strike using enemy exploits:
   When `traffic/sniffer.py` alerts an enemy attack, replay their exact payload:
   ```bash
   python3 attack/exploit_replay.py traffic/captured_exploits/<latest_dump>.bin --port 8080
   ```
   *All captured flags are automatically piped into flags_queue.txt and submitted.*

### Step 5: Surgical Defense (Preserve SLA)
- Never return HTTP 500 or crash services.
- Apply length limits to input parameters:
  ```php
  if (strlen($_POST['input']) > 32) { die("OK"); }
  ```
- Force type-casting on IDs:
  ```php
  $id = intval($_GET['id']);
  ```
- If a patch breaks SLA, immediately rollback with:
  ```bash
  cd /path/to/service && git checkout .
  ```

---

## Core Rules Compliance
- Anti-DDoS Throttling: `attack/exploit_web.py`, `exploit_pwn.py`, and `exploit_replay.py` enforce `time.sleep(2.1)` per target.
- Zero Firewall Changes: All defense tools operate strictly at Layer 7.
- Non-Destructive: Exploits only read flags; no crashing or disrupting enemy services.
- Internal Sniffing Only: Captures restricted strictly to local assigned interfaces (`eth0`, `docker0`).
