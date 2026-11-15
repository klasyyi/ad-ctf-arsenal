# 🛡️ AD-CTF-ARSENAL: 24-Hour Attack & Defense Automation Framework

A production-grade, battle-tested operational repository for **Attack & Defense CTFs**, engineered for strict competition environments (No AI during match, No firewall modifications, No port scanning, Mandatory >=2s rate limiting).

---

## ⚡ Quickstart on Game Day (Inside Pwnbox)

Once you gain access to your competition Pwnbox at 10:00 AM, clone and bootstrap everything in 60 seconds:

```bash
# 1. Clone your private repository
git clone https://github.com/klasyyi/ad-ctf-arsenal.git
cd ad-ctf-arsenal

# 2. Run the Pwnbox bootstrap installer
chmod +x bootstrap/setup_pwnbox.sh
./bootstrap/setup_pwnbox.sh

# 3. Source environment & aliases
source ~/.bashrc

# 4. Launch the team tmux command center
tmux
```

---

## 📂 Repository Architecture

```text
ad-ctf-arsenal/
├── README.md                 # This operational guide
├── .gitignore                # Excludes runtime DBs, PCAPs, logs, and queue files
├── bootstrap/
│   ├── setup_pwnbox.sh       # One-click bootstrap (Burp, tools, Python libraries)
│   ├── tmux.conf             # Ergonomic tmux config (mouse on, fast splits)
│   └── aliases.sh            # Productivity aliases (flaggrep, sniff, docker helpers)
├── attack/
│   ├── submitter_daemon.py   # Central flag submission queue with SQLite deduplication
│   ├── exploit_web.py        # Multi-target web exploit runner (>=2.1s anti-DDoS delay)
│   ├── exploit_pwn.py        # Pwntools socket exploit runner (>=2.1s anti-DDoS delay)
│   ├── exploit_replay.py     # "Steal & Replay" engine for incoming enemy payloads
│   └── targets.txt           # Configurable target IP/host list
├── defense/
│   ├── backup_services.sh    # Instant service snapshot & Git initialization
│   ├── bot_watcher.sh        # Radar 1: Real-time organizer SLA bot watcher
│   ├── proxy_logger.py       # Zero-Firewall Layer 7 proxy logger
│   ├── waf_php_shim.php      # PHP auto_prepend_file WAF & attack sink
│   └── waf_python_shim.py    # Python/Flask WSGI request logger & filter
├── traffic/
│   ├── sniffer.py            # Radar 2: Live scapy flag sniffer & payload dumper
│   └── pcap_dump.sh          # Rolling 60-second tcpdump ring buffer
└── manual/
    ├── GAME_DYNAMICS_AND_CHEATCODES.md # Master guide: Bot spying, stealing exploits, SLA rules
    ├── FIELD_MANUAL.md       # Offline cheat sheet (SQLi, SSTI, LFI, Pwn, Ghidra)
    └── PLAYBOOK.md           # Game rules, team shift rotations & triage protocol
```

---

## 🚀 Match Day Workflow

### Step 1: The "Golden Hour" (00:00 - 00:15)
Run the automated backup script to save clean baselines and enable instant git diffing:
```bash
chmod +x defense/backup_services.sh
sudo ./defense/backup_services.sh
```

### Step 2: Start Twin-Radar Intelligence & Submitter Daemon
In your tmux panes, start the central flag engine and monitoring radars:
```bash
# Pane 1: Central Submitter Daemon
python3 attack/submitter_daemon.py

# Pane 2: Radar 2 - Live Network Sniffer (Catch Enemy Attackers)
sudo python3 traffic/sniffer.py eth0

# Pane 3: Radar 1 - Organizer Bot Watcher (Find Where Flag Lives)
chmod +x defense/bot_watcher.sh && ./defense/bot_watcher.sh
```

### Step 3: Attack Execution
When your team finds a vulnerability or extracts an enemy payload:
1. Update `attack/exploit_web.py` or `attack/exploit_pwn.py`.
2. Run the dispatcher:
   ```bash
   python3 attack/exploit_web.py
   ```
   *All flags captured will be piped into `flags_queue.txt` and automatically submitted by the daemon.*

### Step 4: Replay Stolen Enemy Attacks
When `traffic/sniffer.py` catches an enemy attacking your service, replay their exact payload against everyone else:
```bash
python3 attack/exploit_replay.py traffic/captured_exploits/latest_exploit.bin --port 8080
```

---

## 🔒 Strict Rule Compliance Verification
- **Anti-DDoS Throttling:** `attack/exploit_web.py`, `exploit_pwn.py`, and `exploit_replay.py` enforce `time.sleep(2.1)` per target.
- **Zero-Firewall Compliance:** Defense tools (`proxy_logger.py`, `waf_php_shim.php`, `waf_python_shim.py`) operate strictly at Layer 7.
- **No Disrupting Enemy Services:** All exploit templates are non-destructive (read-only flag extraction).
- **Internal Sniffing Only:** `traffic/sniffer.py` attaches strictly to your assigned local interface.
