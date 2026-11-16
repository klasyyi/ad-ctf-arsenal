"""
================================================================================
CENTRAL CONFIGURATION  (single-source)
================================================================================
The flag format, team IPs and service ports now live in ONE file:

    s4dfarm_engine/server/app/config.py

That is the file the S4DFarm server already reads, so match-day config is a
single edit there. This module imports the shared values from it, so the arsenal
tools (exploit_replay.py, traffic/sniffer.py, and the EXPIRED standalone attack
scripts) keep working unchanged - they still do `from config import ...`.

Only the standalone submitter_daemon's scoreboard settings stay in this file,
because under S4DFarm the server submits through its own SYSTEM_PROTOCOL and the
standalone submitter is EXPIRED (break-glass fallback only).
================================================================================
"""
import os
import importlib.util

# ---- load the single source: server/app/config.py, by absolute path so it
#      resolves no matter what directory a tool is launched from ----
_here = os.path.dirname(os.path.abspath(__file__))
_server_config = os.path.join(_here, "..", "s4dfarm_engine", "server", "app", "config.py")
_spec = importlib.util.spec_from_file_location("farm_server_config", _server_config)
_farm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_farm)

# ---- shared values (edit these in server/app/config.py, NOT here) ----
FLAG_REGEX_STR = _farm.FLAG_FORMAT      # same string the farm server extracts with
WEB_PORT = _farm.WEB_PORT
WEB_PATH = _farm.WEB_PATH
PWN_PORT = _farm.PWN_PORT
MY_TEAM_IP = _farm.MY_TEAM_IP
PER_TARGET_SLEEP = _farm.PER_TARGET_SLEEP
TICK_DURATION = _farm.TICK_DURATION

# ---- standalone submitter_daemon ONLY (EXPIRED; the farm submits via the
#      server's SYSTEM_PROTOCOL, so these are unused under S4DFarm) ----
SUBMISSION_PROTOCOL = "HTTP_JSON"       # "HTTP_JSON", "HTTP_FORM", "TCP_SOCKET"
SUBMIT_URL = "http://scoreboard.ctf/api/submit"
TEAM_TOKEN = "YOUR_TEAM_TOKEN_HERE"
TCP_SUBMIT_HOST = "scoreboard.ctf"
TCP_SUBMIT_PORT = 31337
