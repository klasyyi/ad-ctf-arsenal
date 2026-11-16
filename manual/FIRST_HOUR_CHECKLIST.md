# First Hour Protocol: Minute-by-Minute Action Plan

## 00:00 - 00:05: Boot & Arm
1. Connect to Pwnbox via browser, VNC, or SSH.
2. Clone repository and run installer:
   ```bash
   git clone https://github.com/klasyyi/ad-ctf-arsenal.git
   cd ad-ctf-arsenal
   chmod +x bootstrap/setup_pwnbox.sh && ./bootstrap/setup_pwnbox.sh
   source ~/.bashrc
   ```
3. Start tmux session:
   ```bash
   tmux
   ```

## 00:05 - 00:15: Lock In & Launch Radars
Do not touch or modify any challenge code yet.
1. Run initial backup (snapshots services and initializes git for rollback):
   ```bash
   sudo ./defense/backup_services.sh
   ```
2. Check local network interface name:
   ```bash
   ip a
   ```
3. Start background flag submitter:
   ```bash
   python3 attack/submitter_daemon.py &
   ```
4. Start Radar 2 (Enemy sniffer on your interface):
   ```bash
   sudo python3 traffic/sniffer.py eth0 &
   ```
5. Start Radar 1 (Bot watcher):
   ```bash
   chmod +x defense/bot_watcher.sh && ./defense/bot_watcher.sh &
   ```
6. Check scoreboard: Confirm all services are GREEN.

## 00:15 - 00:30: Configuration & Flag Sink Discovery
1. Check output in the Bot Watcher window:
   - Identify active endpoints called by the SLA bot (e.g., `POST /api/notes`, `GET /profile`).
   - Identify flag format and storage location (database table, `/flag.txt`, etc.).
2. Configure the 2 core files:
   - In `attack/submitter_daemon.py`: Set `SUBMIT_URL` and `TEAM_TOKEN`.
   - In `attack/targets.txt`: Paste opposing team IPs (omit your own IP).

## 00:30 - 01:00: Role Assignment & Initial Exploitation
1. Player 1 (Defense Lead):
   - Monitor `traffic/sniffer.py` and `defense/bot_watcher.sh`.
   - Check local code for obvious backdoors (`eval`, `system`, hardcoded credentials).
2. Player 2 (Attack Lead):
   - Target active endpoints spotted by the Bot Watcher.
   - Test basic injections on localhost (SQLi, IDOR, Path Traversal).
   - Once working, set `SERVICE_PORT` and `params` in `attack/exploit_web.py` and run against all teams.
3. Player 3 (Reverser):
   - Load binary challenges into Ghidra.
   - Locate vulnerable functions and draft surgical patches.

## 01:00 Onward: Routine Loop
1. Automated attack scripts run every tick (2-3 minutes).
2. Submitter daemon processes flags in the background.
3. When sniffer alerts an incoming attack:
   - Replay payload against all other teams via `attack/exploit_replay.py`.
   - Apply surgical patch to your local file.
