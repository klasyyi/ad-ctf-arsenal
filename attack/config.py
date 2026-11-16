"""
================================================================================
CENTRAL CONFIGURATION FILE
================================================================================
This is the ONLY file you need to edit at the start of the competition.
Edit it, save it, and all scripts pick up the changes automatically.
================================================================================
"""

# ---------------------------------------------------------------------------
# 1. SCOREBOARD SUBMISSION (Get these from the competition portal at 10:00 AM)
# ---------------------------------------------------------------------------
SUBMIT_URL = "http://scoreboard.ctf/api/submit"
TEAM_TOKEN = "YOUR_TEAM_TOKEN_HERE"

# ---------------------------------------------------------------------------
# 2. YOUR TEAM (This IP is SKIPPED so you never attack yourself)
# ---------------------------------------------------------------------------
MY_TEAM_IP = "10.60.5.1"

# ---------------------------------------------------------------------------
# 3. TIMING
# Tick duration in seconds. Set to match the competition tick rate.
# Common values: 120 (2 min), 180 (3 min). Use 90 if unknown.
# ---------------------------------------------------------------------------
TICK_DURATION = 120
PER_TARGET_SLEEP = 2.1   # DO NOT lower this below 2.0 (competition rule)

# ---------------------------------------------------------------------------
# 4. TARGET SERVICE
# Update SERVICE_PORT and TARGET_PATH once you discover the vulnerable endpoint.
# ---------------------------------------------------------------------------
SERVICE_PORT = 8080
TARGET_PATH = "/api/v1/profile"

# ---------------------------------------------------------------------------
# 5. FLAG FORMAT
# Adjust regex if the competition uses a different flag format.
# ---------------------------------------------------------------------------
FLAG_REGEX_STR = r"FLAG\{[A-Za-z0-9_\-]{16,64}\}|[A-Z0-9]{32}="
