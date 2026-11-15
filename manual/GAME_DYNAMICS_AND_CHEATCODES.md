# Game Dynamics & In-Competition Cheat Codes

Offline reference for 24-hour Attack & Defense competition mechanics.

---

## 1. Absolute Red Lines

- Never turn down or crash enemy services: Causes immediate disqualification. Exploits must read the flag and exit cleanly.
- Never edit firewall or iptables rules: Defend exclusively at Layer 7 (code patches and local proxies).
- Never scan or probe other teams: Port scanning with nmap or directory brute-forcing against opposing teams is prohibited.
- Always throttle automation: Minimum 2.0s delay between requests per target team.
- Sniff only local interfaces: Restrict captures to `eth0` or `docker0`.

---

## 2. The Tick System

- The match runs in rounds called Ticks (typically 2 to 3 minutes each).
- The organizer bot plants a new, unique flag on every team's server each tick.
- Flags expire after 1 to 3 ticks (2 to 6 minutes).
- Your automated loop attacks all 29 teams in ~61 seconds (`29 * 2.1s = 60.9s`), well within the tick window.

---

## 3. Twin-Radar Intelligence Strategy

### Radar 1: Watch the Organizer SLA Bot
The bot visits your machine every tick. Its requests reveal the application blueprint:
```bash
# Watch bot traffic in real time:
chmod +x defense/bot_watcher.sh && ./defense/bot_watcher.sh
```
- Reveals the active endpoints (e.g., `POST /api/messages`).
- Reveals where the flag is stored (e.g., `messages` table, `/flag.txt`).
- Focus code audit only on the specific file handling that endpoint.

### Radar 2: Sniff Incoming Enemy Attackers
If an enemy finds a vulnerability before you, capture and reuse it:
```bash
# Run sniffer in background:
sudo python3 traffic/sniffer.py eth0 &
```
- Dumps incoming exploit payloads to `traffic/captured_exploits/`.
- Immediate counter-strike: Replay the captured payload against all other teams:
  ```bash
  python3 attack/exploit_replay.py traffic/captured_exploits/<dump>.bin --port 8080
  ```
- Use the payload data to patch the exact line of code on your own server.

---

## 4. Surgical Patching Rules

Avoid complex rewrites; use surgical fixes that keep the SLA green:

### Length-Limit Filter
Blocks long SQLi, RCE, or path traversal payloads while allowing short SLA bot inputs:
```php
if (strlen($_POST['input']) > 32) {
    die("OK"); // 200 OK preserves SLA status
}
```

### Type-Casting (SQLi Fix)
Force parameters into integers to drop SQL payloads:
```php
$id = intval($_GET['id']);
```

### Binary Patching (NOP-ing)
Replace dangerous calls with NOPs:
1. Open binary in Ghidra.
2. Select instruction -> Press `Ctrl + Shift + G`.
3. Replace call with `NOP` (`0x90`) or set function entry to `RET` (`0xC3`).
4. Export as Original File -> Replace service binary -> Restart service.

---

## 5. Database Flag Queries

When extracting flags from a database, older expired flags may still be present in the table. Always select the newest row:
```sql
-- Always sort descending by ID to get the active flag:
' UNION SELECT null, flag, null FROM flags ORDER BY id DESC LIMIT 1-- -
```

---

## 6. Deadlock Protocol (When No One Is Exploiting)

If no team has an exploit and the scoreboard flatlines:
1. Do not modify or break working services. If services are green, you are tied for 1st.
2. Run `defense/bot_watcher.sh` and inspect the bot's workflow.
3. Check for recently added or custom code files:
   ```bash
   find /var/www /home /opt -mmin -180 -type f
   ```
4. If a binary service is stalled, pivot effort to web or API services.
5. First team to solve the service gains an uncontested run across all 29 teams.

---

## 7. Team Shifts (3 Active + 1 Substitute)

- Player 1: Defense and traffic lead.
- Player 2: Attack and automation lead.
- Player 3: Reverse engineering and patching lead.
- Player 4 (Substitute): Manages logistics and rests during Phase 1. Substituted in for Phase 2 with full energy to lead the graveyard shift (02:00 - 06:00).
