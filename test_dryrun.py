#!/usr/bin/env python3
"""
================================================================================
END-TO-END DRY-RUN SIMULATION TEST
================================================================================
Tests the full pipeline locally without needing any external network:
1. Spawns a Mock Scoreboard API (port 9001).
2. Spawns a Mock Vulnerable Service (port 8080).
3. Tests Submitter Daemon (Queue -> API -> SQLite deduplication).
4. Tests Exploit Runner (HTTP request -> Regex extraction -> Queue).
5. Tests L7 Proxy Logger (Port forwarding -> Payload logging).
================================================================================
"""

import os
import sys
import time
import json
import socket
import sqlite3
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "attack"))
sys.path.insert(0, os.path.join(BASE_DIR, "defense"))

TEST_QUEUE_FILE = os.path.join(BASE_DIR, "attack", "flags_queue.txt")
TEST_DB_FILE = os.path.join(BASE_DIR, "attack", "test_submitted_flags.db")

MOCK_SCOREBOARD_PORT = 9001
MOCK_SERVICE_PORT = 8080
MOCK_PROXY_PORT = 8082

submitted_records = []

# ==============================================================================
# 1. MOCK SCOREBOARD SERVER
# ==============================================================================
class MockScoreboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # Silence console logging

    def do_POST(self):
        if self.path == "/api/submit":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(post_body)
            flag = data.get("flag", "")
            submitted_records.append(flag)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"status": "success", "message": f"Accepted flag: {flag}"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

# ==============================================================================
# 2. MOCK VULNERABLE SERVICE
# ==============================================================================
class MockServiceHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if "/api/v1/profile" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            # Vulnerable SQLi output containing a flag
            body = json.dumps({
                "id": 1,
                "username": "admin",
                "secret": "FLAG{DRYRUN_TEST_MOCK_FLAG_882233}"
            })
            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_http_server(handler_cls, port):
    server = HTTPServer(("127.0.0.1", port), handler_cls)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server

# ==============================================================================
# MAIN TEST SUITE
# ==============================================================================
def main():
    print("=" * 65)
    print("STARTING END-TO-END DRY-RUN SIMULATION")
    print("=" * 65)

    # Clean previous test files
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    if os.path.exists(TEST_QUEUE_FILE):
        os.remove(TEST_QUEUE_FILE)

    # 1. Start Mock Servers
    print("[*] Starting Mock Scoreboard on 127.0.0.1:9001...")
    run_http_server(MockScoreboardHandler, MOCK_SCOREBOARD_PORT)

    print("[*] Starting Mock Vulnerable Service on 127.0.0.1:8080...")
    run_http_server(MockServiceHandler, MOCK_SERVICE_PORT)
    time.sleep(0.5)

    # --------------------------------------------------------------------------
    # TEST 1: Flag Submitter Daemon
    # --------------------------------------------------------------------------
    print("\n--- TEST 1: Submitter Daemon & Queueing ---")
    import submitter_daemon
    submitter_daemon.SUBMIT_URL = f"http://127.0.0.1:{MOCK_SCOREBOARD_PORT}/api/submit"
    submitter_daemon.DB_FILE = TEST_DB_FILE
    submitter_daemon.FLAG_FILE = TEST_QUEUE_FILE
    submitter_daemon.SUBMISSION_INTERVAL = 0.05
    submitter_daemon.init_db()

    # Feed test flag into queue
    test_flag_1 = "FLAG{SUBMITTER_TEST_QUEUE_112233}"
    with open(TEST_QUEUE_FILE, "a") as f:
        f.write(f"{test_flag_1}\n")

    # Process queue
    submitter_daemon.process_queue()

    # Verify
    assert test_flag_1 in submitted_records, "FAIL: Flag not delivered to scoreboard"
    assert submitter_daemon.is_flag_processed(test_flag_1), "FAIL: Flag not stored in SQLite DB"
    print("[PASS] Flag picked up from queue and submitted to Scoreboard.")
    print("[PASS] SQLite persistent storage and deduplication verified.")

    # Deduplication test: re-feed same flag, must not re-submit
    with open(TEST_QUEUE_FILE, "a") as f:
        f.write(f"{test_flag_1}\n")
    initial_count = len(submitted_records)
    submitter_daemon.process_queue()
    assert len(submitted_records) == initial_count, "FAIL: Duplicate flag was re-submitted"
    print("[PASS] Deduplication check passed (duplicate was ignored).")

    # --------------------------------------------------------------------------
    # TEST 2: Exploit Runner
    # --------------------------------------------------------------------------
    print("\n--- TEST 2: Exploit Web Runner ---")
    import exploit_web
    exploit_web.SERVICE_PORT = MOCK_SERVICE_PORT
    exploit_web.QUEUE_FILE = TEST_QUEUE_FILE

    extracted_flag = exploit_web.attack_team("127.0.0.1")
    assert extracted_flag == "FLAG{DRYRUN_TEST_MOCK_FLAG_882233}", f"FAIL: Unexpected flag: {extracted_flag}"
    print(f"[PASS] Exploit successfully extracted flag: {extracted_flag}")

    # Queue and submit extracted flag
    with open(TEST_QUEUE_FILE, "a") as f:
        f.write(f"{extracted_flag}\n")
    submitter_daemon.process_queue()
    assert extracted_flag in submitted_records, "FAIL: Extracted flag failed submission"
    print("[PASS] Exploit-to-Submitter pipeline verified.")

    # --------------------------------------------------------------------------
    # TEST 3: Zero-Firewall L7 Proxy Logger
    # --------------------------------------------------------------------------
    print("\n--- TEST 3: L7 Proxy Logger ---")
    import proxy_logger
    test_log = os.path.join(BASE_DIR, "defense", "test_traffic_l7.log")
    if os.path.exists(test_log):
        os.remove(test_log)

    # Start proxy in background thread
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", MOCK_PROXY_PORT))
    server.listen(10)

    def proxy_worker():
        while True:
            try:
                csock, caddr = server.accept()
                threading.Thread(
                    target=proxy_logger.handle_client,
                    args=(csock, caddr, "127.0.0.1", MOCK_SERVICE_PORT, test_log),
                    daemon=True
                ).start()
            except Exception:
                break

    threading.Thread(target=proxy_worker, daemon=True).start()
    time.sleep(0.3)

    # Send request through the proxy port
    resp = requests.get(f"http://127.0.0.1:{MOCK_PROXY_PORT}/api/v1/profile")
    assert resp.status_code == 200, "FAIL: Proxy did not forward response"
    time.sleep(0.2)
    assert os.path.exists(test_log) and os.path.getsize(test_log) > 0, "FAIL: Log file was not created"
    print(f"[PASS] L7 Proxy successfully forwarded request and logged {os.path.getsize(test_log)} bytes.")

    # --------------------------------------------------------------------------
    # CLEANUP
    # --------------------------------------------------------------------------
    server.close()
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    if os.path.exists(test_log):
        os.remove(test_log)

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED SUCCESSFULLY! THE ARSENAL IS FULLY OPERATIONAL.")
    print("=" * 65)

if __name__ == "__main__":
    main()
