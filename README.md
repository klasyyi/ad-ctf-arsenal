# AD-CTF Arsenal: 24-Hour Attack & Defense Automation Framework

Lightweight, production-grade automation suite for 24-hour Attack & Defense CTF competitions. Compliant with strict competition rules: zero AI, zero firewall/iptables changes, no port scanning, and mandatory >=2.0s rate limiting.

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

## What to Configure at 10:00 AM (The Only 3 Files to Edit)

### 1. `attack/submitter_daemon.py`
Set scoreboard API endpoint and team secret token:
```python
SUBMIT_URL = "http://scoreboard.ctf/api/submit"  # Submission URL from portal
TEAM_TOKEN = "YOUR_TEAM_TOKEN_HERE"              # Private token from portal
FLAG_REGEX = re.compile(r"FLAG\{[A-Za-z0-9_\-]{16,64}\}") # Match flag pattern
```

### 2. `attack/targets.txt`
Replace with list of opposing team IPs/hosts (omit your own team IP):
```text
10.60.1.1
10.60.2.1
10.60.3.1
...
```

### 3. `attack/exploit_web.py`
Set ports and insert exploit payload once a vulnerability is found:
```python
MY_TEAM_IP = "10.60.5.1"        # Your team's IP (skip self)
SERVICE_PORT = 8080              # Target challenge port
TARGET_PATH = "/api/v1/profile"  # Endpoint path
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

# 2. Check network interface name (eth0, ens3, etc.)
ip a

# 3. Start the central flag submitter
python3 attack/submitter_daemon.py &

# 4. Start Radar 2 (Enemy Packet Sniffer)
sudo python3 traffic/sniffer.py eth0 &

# 5. Start Radar 1 (Organizer Bot Watcher)
chmod +x defense/bot_watcher.sh && ./defense/bot_watcher.sh &
```
*Check scoreboard: Confirm your services start GREEN.*

### Step 3: Discover Flag Sink & Endpoints (00:15 - 00:30)
1. Check output in the Bot Watcher window:
   - Identify active URLs visited by the bot (e.g. `POST /api/notes`, `GET /profile`).
   - Identify where the flag is placed (database table, `/flag.txt`, etc.).
2. Update `attack/submitter_daemon.py` and `attack/targets.txt` with competition details.

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

## File Action Reference

| File | Match Day Action |
| :--- | :--- |
| `attack/submitter_daemon.py` | Edit: Set `SUBMIT_URL` and `TEAM_TOKEN`. |
| `attack/targets.txt` | Edit: Paste list of opposing team IPs. |
| `attack/exploit_web.py` | Edit: Set `SERVICE_PORT` and insert payload once found. |
| `bootstrap/setup_pwnbox.sh` | Run only: `./setup_pwnbox.sh`. |
| `defense/backup_services.sh`| Run only: `./backup_services.sh`. |
| `defense/bot_watcher.sh` | Run only: `./bot_watcher.sh`. |
| `traffic/sniffer.py` | Run only: `python3 sniffer.py <iface>`. |

---

## Core Rules Compliance
- Anti-DDoS Throttling: All attack runners enforce `time.sleep(2.1)` per target.
- Zero Firewall Changes: All defense tools operate strictly at Layer 7.
- Non-Destructive: Exploits only read flags; no crashing or disrupting enemy services.
- Internal Sniffing Only: Captures restricted strictly to local assigned interfaces (`eth0`, `docker0`).
