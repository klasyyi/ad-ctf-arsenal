#!/usr/bin/env python3
"""
================================================================================
ZERO-FIREWALL LAYER 7 PROXY LOGGER
================================================================================
Binds to the public challenge port (e.g., 8080) and forwards to the real
backend (e.g., 8081).
Dumps all full HTTP request and response payloads to disk for exploit analysis.

Complies 100% with the "NO FIREWALL / IPTABLES CHANGES" rule!
"""

import socket
import threading
import sys
import os
import argparse
from datetime import datetime

def log_data(log_file, direction, client_ip, data):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n{'='*25} [{ts}] {direction} ({client_ip}) {'='*25}\n"
    with open(log_file, "ab") as f:
        f.write(header.encode() + data + b"\n")

def forward(src_sock, dst_sock, client_ip, direction, log_file):
    while True:
        try:
            data = src_sock.recv(4096)
            if not data:
                break
            log_data(log_file, direction, client_ip, data)
            dst_sock.sendall(data)
        except Exception:
            break
    try:
        dst_sock.shutdown(socket.SHUT_WR)
    except Exception:
        pass

def handle_client(client_sock, client_addr, target_host, target_port, log_file):
    try:
        target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_sock.connect((target_host, target_port))
    except Exception:
        try:
            client_sock.close()
        except Exception:
            pass
        return

    t_in = threading.Thread(target=forward, args=(client_sock, target_sock, client_addr[0], "CLIENT -> BACKEND", log_file))
    t_out = threading.Thread(target=forward, args=(target_sock, client_sock, client_addr[0], "BACKEND -> CLIENT", log_file))
    t_in.daemon = True
    t_out.daemon = True
    t_in.start()
    t_out.start()

    def cleanup():
        t_in.join(timeout=10)
        t_out.join(timeout=10)
        try:
            client_sock.close()
        except Exception:
            pass
        try:
            target_sock.close()
        except Exception:
            pass

    threading.Thread(target=cleanup, daemon=True).start()

def main():
    parser = argparse.ArgumentParser(description="Zero-firewall L7 proxy logger")
    parser.add_argument("--listen", type=int, default=8080, help="Public listening port (default: 8080)")
    parser.add_argument("--target-port", type=int, default=8081, help="Real backend port (default: 8081)")
    parser.add_argument("--target-host", default="127.0.0.1", help="Backend host (default: 127.0.0.1)")
    parser.add_argument("--log", default="traffic_l7.log", help="Log file path (default: traffic_l7.log)")
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", args.listen))
    server.listen(100)

    print(f"[*] Proxy active on 0.0.0.0:{args.listen} -> forwarding to {args.target_host}:{args.target_port}")
    print(f"[*] Logging payloads to {args.log}")

    while True:
        client_sock, client_addr = server.accept()
        threading.Thread(
            target=handle_client,
            args=(client_sock, client_addr, args.target_host, args.target_port, args.log),
            daemon=True
        ).start()

if __name__ == "__main__":
    main()
