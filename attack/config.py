"""
================================================================================
CENTRAL CONFIGURATION FILE
================================================================================
This is the ONLY configuration file you need to edit at the start of the match.
All scripts automatically read their settings from here.
================================================================================
"""

# ---------------------------------------------------------------------------
# 1. SCOREBOARD & FLAG SUBMISSION
# Get these from the competition portal at 10:00 AM.
# ---------------------------------------------------------------------------
# Protocol options: "HTTP_JSON", "HTTP_FORM", "TCP_SOCKET"
SUBMISSION_PROTOCOL = "HTTP_JSON"

# For HTTP_JSON or HTTP_FORM:
SUBMIT_URL = "http://scoreboard.ctf/api/submit"
TEAM_TOKEN = "YOUR_TEAM_TOKEN_HERE"

# For TCP_SOCKET (if competition uses raw socket submission, e.g. nc host port):
TCP_SUBMIT_HOST = "scoreboard.ctf"
TCP_SUBMIT_PORT = 31337

# ---------------------------------------------------------------------------
# 2. YOUR TEAM IDENTITY
# Your team IP will be SKIPPED during attacks so you never attack yourself.
# ---------------------------------------------------------------------------
MY_TEAM_IP = "10.60.5.1"

# ---------------------------------------------------------------------------
# 3. SERVICE PORTS & PATHS
# Update ports and paths once challenge services are announced.
# ---------------------------------------------------------------------------
WEB_PORT = 8080
WEB_PATH = "/api/v1/profile"

PWN_PORT = 9999

# ---------------------------------------------------------------------------
# 4. TIMING & THROTTLING
# ---------------------------------------------------------------------------
# Round/tick sleep duration in seconds (matches game tick rate, e.g. 120 or 180)
TICK_DURATION = 120

# Mandatory per-target delay in seconds (must be >= 2.0 to comply with anti-DDoS rule)
PER_TARGET_SLEEP = 2.1

# ---------------------------------------------------------------------------
# 5. FLAG PATTERN
# Regex matching the competition flag format.
# Verify format at game start (e.g. check prefix like FLAG{ or CTF{,
# and check length boundaries {16,64} if flags are shorter/longer).
# ---------------------------------------------------------------------------
FLAG_REGEX_STR = r"(?:FLAG|CTF)\{[A-Za-z0-9_\-]{8,64}\}|[A-Z0-9]{32}="
