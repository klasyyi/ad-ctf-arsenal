"""
Shared config for the S4DFarm-run sploits.

Match-day: edit service-specific bits HERE (ports, paths). The team list,
the authoritative flag format, submission protocol, quota and tick all live
in S4DFarm's server/app/config.py, not here.

FLAG_REGEX below is only used to print clean flags from the service response.
S4DFarm's server re-extracts flags from stdout using its own FLAG_FORMAT, so
keep the two in sync (same pattern).
"""
import re

# keep in sync with S4DFarm server FLAG_FORMAT
FLAG_REGEX = re.compile(r"FLAG\{[A-Za-z0-9_\-]{16,64}\}")
FLAG_REGEX_BYTES = re.compile(rb"FLAG\{[A-Za-z0-9_\-]{16,64}\}")

# ---- per-service settings (one block per vulnerable service) ----
WEB_PORT = 8080
WEB_PATH = "/api/v1/profile"

PWN_PORT = 9999
