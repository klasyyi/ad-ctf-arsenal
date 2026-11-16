#!/usr/bin/env python3
"""
================================================================================
ZERO-FIREWALL PYTHON (FLASK) WAF & LOGGING MIDDLEWARE
================================================================================
How to integrate into any Flask app:

from waf_python_shim import register_waf
app = Flask(__name__)
register_waf(app)
================================================================================
Mode (env var WAF_MODE):
  "monitor" (default) - log matches, NEVER block. Attack/defense SLA-safe:
      a false positive can only cost you the log line, never the service check.
  "block"             - additionally return 403 on a match. Use only once you
      have watched the monitor log and trust the patterns against the real
      checker traffic. Blocking CAN fail SLA on a false positive; there is no
      "safe" fake-200, the checker needs the real response body.

Deliberately NOT matched: the flag format itself. The organizer SLA checker
plants and reads flags through your legit endpoints, so its traffic contains
the flag string. Matching on it blocks the checker and loses SLA.
================================================================================
"""

import os
import re
import json
from datetime import datetime
from flask import request, abort

LOG_FILE = "/tmp/flask_waf_traffic.log"
BLOCKED_LOG = "/tmp/flask_waf_blocked.log"

WAF_MODE = os.environ.get("WAF_MODE", "monitor").lower()  # "monitor" or "block"

BAD_PATTERNS = [
    re.compile(r"union\s+select", re.IGNORECASE),
    re.compile(r"\/\.\.\/"),
    re.compile(r"(cat|head|tail|more|less|tac)\s+.*flag", re.IGNORECASE),
    re.compile(r"\{\{.*config.*\}\}"),  # SSTI Jinja2
]

def register_waf(app):
    @app.before_request
    def intercept():
        client_ip = request.remote_addr or "unknown"
        path = request.path
        method = request.method
        headers = dict(request.headers)
        query = dict(request.args)
        body = request.get_data(as_text=True)

        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": client_ip,
            "method": method,
            "path": path,
            "args": query,
            "headers": headers,
            "body": body
        }

        # Log incoming traffic
        try:
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        # Check for attack patterns across URI, params, and body
        full_payload = f"{path} {json.dumps(query)} {body}"
        for pattern in BAD_PATTERNS:
            if pattern.search(full_payload):
                verb = "BLOCKED" if WAF_MODE == "block" else "WOULD-BLOCK"
                try:
                    with open(BLOCKED_LOG, "a") as f:
                        f.write(f"[{datetime.now()}] {verb} {pattern.pattern} from {client_ip}\n")
                except Exception:
                    pass

                # Only drop the request in block mode. In monitor mode we log and
                # fall through so legit/checker traffic always gets the real app
                # response. 403 is honest: a fake 200 still fails SLA on a false
                # positive (checker expects real content, not "OK").
                if WAF_MODE == "block":
                    abort(403)
                break
