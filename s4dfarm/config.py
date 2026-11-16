"""
Shared config for the S4DFarm-run sploits.

Single source of truth: s4dfarm_engine/server/app/config.py - the file the farm
server itself reads. This module imports the shared values from it, so match-day
config is a single edit there; the flag pattern and service ports are NOT
redefined here. Team IPs, submission protocol, quota and tick also live in that
same server config.

FLAG_REGEX below is only used to print clean flags from the service response.
S4DFarm's server re-extracts flags from stdout with its own FLAG_FORMAT - which
is this same value, since both come from the one server config.
"""
import os
import re
import importlib.util

# Load the single source (server/app/config.py) by absolute path, so it resolves
# no matter what directory start_sploit.py runs the sploit from.
_here = os.path.dirname(os.path.abspath(__file__))
_server_config = os.path.join(_here, "..", "s4dfarm_engine", "server", "app", "config.py")
_spec = importlib.util.spec_from_file_location("farm_server_config_s4d", _server_config)
_farm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_farm)

# ---- flag pattern (single source: server FLAG_FORMAT) ----
FLAG_REGEX = re.compile(_farm.FLAG_FORMAT)
FLAG_REGEX_BYTES = re.compile(_farm.FLAG_FORMAT.encode())

# ---- per-service settings (single source: server config) ----
WEB_PORT = _farm.WEB_PORT
WEB_PATH = _farm.WEB_PATH
PWN_PORT = _farm.PWN_PORT
