#!/usr/bin/env python3
"""
================================================================================
INTERNAL TRAFFIC SNIFFER & EXPLOIT DUMPER
================================================================================
Sniffs TCP traffic on your assigned local interface (e.g. eth0, docker0).
When a flag leak is detected:
1. Prints an immediate terminal alert with the attacker IP.
2. Dumps the raw payload into captured_exploits/ for instant replay.
================================================================================
"""

import re
import os
import sys
from datetime import datetime
from scapy.all import sniff, TCP, Raw, IP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "captured_exploits")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FLAG_REGEX = re.compile(rb"(FLAG\{[A-Za-z0-9_\-]{16,64}\}|[A-Z0-9]{32}=)")
seen_flags = set()

def packet_callback(pkt):
    if pkt.haslayer(TCP) and pkt.haslayer(Raw):
        payload = pkt[Raw].load
        match = FLAG_REGEX.search(payload)
        
        if match:
            flag_str = match.group(0).decode(errors="ignore")
            src_ip = pkt[IP].src if pkt.haslayer(IP) else "unknown"
            dst_ip = pkt[IP].dst if pkt.haslayer(IP) else "unknown"
            dst_port = pkt[TCP].dport
            
            if flag_str not in seen_flags:
                seen_flags.add(flag_str)
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[🚨 FLAG LEAK DETECTED] [{timestamp}]")
                print(f"  Attacker: {src_ip} -> Target: {dst_ip}:{dst_port}")
                print(f"  Flag:     {flag_str}")
                
                # Dump payload to file for instant replay
                filename = os.path.join(
                    OUTPUT_DIR,
                    f"exploit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{src_ip}.bin"
                )
                with open(filename, "wb") as f:
                    f.write(payload)
                print(f"  [+] Saved payload to: {filename}")
                print(f"  [+] Replay with: python3 attack/exploit_replay.py {filename} --port {dst_port}")

def main():
    interface = sys.argv[1] if len(sys.argv) > 1 else "any"
    print("=" * 60)
    print("📡 INTERNAL TRAFFIC SNIFFER ACTIVE")
    print(f"[*] Interface: {interface}")
    print(f"[*] Output Dir: {OUTPUT_DIR}")
    print("=" * 60)
    try:
        sniff(iface=interface, filter="tcp", prn=packet_callback, store=0)
    except KeyboardInterrupt:
        print("\n[*] Stopped sniffer.")

if __name__ == "__main__":
    main()
