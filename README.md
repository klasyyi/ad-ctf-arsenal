# AD-CTF Arsenal: 24-Hour Attack & Defense Framework

A lightweight, automated operational framework for 24-hour Attack & Defense CTFs. Built for environments prohibiting AI, firewall modifications, and network port scanning, with mandatory rate limits.

---

## Quickstart (Inside Pwnbox)

```bash
git clone https://github.com/klasyyi/ad-ctf-arsenal.git
cd ad-ctf-arsenal
chmod +x bootstrap/setup_pwnbox.sh && ./bootstrap/setup_pwnbox.sh
source ~/.bashrc
tmux
```

---

## Repository Structure

```text
ad-ctf-arsenal/
├── README.md                 # System overview and quickstart
├── .gitignore                # Excludes runtime DBs, PCAPs, logs
├── bootstrap/
│   ├── setup_pwnbox.sh       # One-click bootstrap installer
│   ├── tmux.conf             # Ergonomic tmux config
│   └── aliases.sh            # Useful shell aliases (flaggrep, ports)
├── attack/
│   ├── submitter_daemon.py   # Flag submission queue with SQLite deduplication
│   ├── exploit_web.py        # Web exploit runner (2.1s delay per target)
│   ├── exploit_pwn.py        # Pwntools socket exploit runner (2.1s delay)
│   ├── exploit_replay.py     # Replay engine for captured enemy payloads
│   └── targets.txt           # Target IP list
├── defense/
│   ├── backup_services.sh    # Initial service snapshot & Git initializer
│   ├── bot_watcher.sh        # Radar 1: Live organizer SLA bot inspector
│   ├── proxy_logger.py       # Zero-firewall Layer 7 proxy logger
│   ├── waf_php_shim.php      # PHP WAF shim
│   └── waf_python_shim.py    # Python/Flask WAF shim
├── traffic/
│   ├── sniffer.py            # Radar 2: Packet sniffer & exploit dumper
│   └── pcap_dump.sh          # Rolling 60s tcpdump ring buffer
└── manual/
    ├── FIRST_HOUR_CHECKLIST.md         # Minute-by-minute startup checklist
    ├── GAME_DYNAMICS_AND_CHEATCODES.md # Core mechanics, bot tracking, SLA rules
    ├── FIELD_MANUAL.md                 # Offline cheat sheet (SQLi, SSTI, Pwn)
    └── PLAYBOOK.md                     # General rules and shift rotation
```

---

## Match Day Workflow

### 1. Initial 15 Minutes
```bash
# Step 1: Snapshot and track services with Git
chmod +x defense/backup_services.sh && sudo ./defense/backup_services.sh

# Step 2: Launch flag submitter
python3 attack/submitter_daemon.py &

# Step 3: Launch Radar 2 (Enemy Sniffer)
sudo python3 traffic/sniffer.py eth0 &

# Step 4: Launch Radar 1 (Bot Watcher)
chmod +x defense/bot_watcher.sh && ./defense/bot_watcher.sh &
```

### 2. Attack Execution
```bash
# Web challenges:
python3 attack/exploit_web.py

# Pwn challenges:
python3 attack/exploit_pwn.py

# Replay an attack captured from an enemy:
python3 attack/exploit_replay.py traffic/captured_exploits/<file>.bin --port 8080
```

---

## Core Rules Compliance
- Anti-DDoS Throttling: All attack runners hardcode `time.sleep(2.1)` per target.
- Zero Firewall Changes: All defenses run at Layer 7 (application code and local proxies).
- Non-Destructive: Exploits only read flags; no crashing or disrupting enemy services.
- Internal Sniffing Only: Sniffing restricted to local host interfaces.
