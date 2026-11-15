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
"""

import re
import json
from datetime import datetime
from flask import request, abort, Response

LOG_FILE = "/tmp/flask_waf_traffic.log"
BLOCKED_LOG = "/tmp/flask_waf_blocked.log"

BAD_PATTERNS = [
    re.compile(r"union\s+select", re.IGNORECASE),
    re.compile(r"\/\.\.\/"),
    re.compile(r"(cat|head|tail|more|less|tac)\s+.*flag", re.IGNORECASE),
    re.compile(r"\{\{.*config.*\}\}"),  # SSTI Jinja2
    re.compile(r"flag\{", re.IGNORECASE),
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
                with open(BLOCKED_LOG, "a") as f:
                    f.write(f"[{datetime.now()}] Blocked {pattern.pattern} from {client_ip}\n")
                
                # Safe response: 200 OK so SLA checker doesn't trigger a failure alarm
                return Response("OK", status=200)
