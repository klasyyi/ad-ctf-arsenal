#!/usr/bin/env python3
"""
Internal Traffic Sniffer & Exploit Dumper
Sniffs TCP traffic on your assigned local interface.
When a flag is detected in an incoming packet, prints an alert and
dumps the full TCP payload to traffic/captured_exploits/ for instant replay.
"""

import re
import os
import sys
from datetime import datetime
from scapy.all import sniff, TCP, Raw, IP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "..", "attack"))
from config import FLAG_REGEX_STR

OUTPUT_DIR = os.path.join(BASE_DIR, "captured_exploits")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FLAG_REGEX = re.compile(FLAG_REGEX_STR.encode())
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
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"\n[ALERT] [{ts}] FLAG DETECTED IN INCOMING TRAFFIC")
                print(f"  Attacker IP:  {src_ip}")
                print(f"  Your Service: {dst_ip}:{dst_port}")
                print(f"  Flag:         {flag_str}")
                filename = os.path.join(
                    OUTPUT_DIR,
                    f"exploit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{src_ip}.bin"
                )
                with open(filename, "wb") as f:
                    f.write(payload)
                print(f"  Saved to:     {filename}")
                print(f"  Replay cmd:   python3 attack/exploit_replay.py {filename} --port {dst_port}")

def main():
    interface = sys.argv[1] if len(sys.argv) > 1 else "any"
    print("=" * 60)
    print("INTERNAL TRAFFIC SNIFFER")
    print(f"[*] Interface:  {interface}")
    print(f"[*] Output dir: {OUTPUT_DIR}")
    print("[*] Listening for enemy exploits hitting your services...")
    print("=" * 60)
    try:
        sniff(iface=interface, filter="tcp", prn=packet_callback, store=0)
    except KeyboardInterrupt:
        print("\n[*] Sniffer stopped.")

if __name__ == "__main__":
    main()
