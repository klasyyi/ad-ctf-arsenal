#!/usr/bin/env python3
"""
Internal Traffic Sniffer & Exploit Dumper
Sniffs TCP traffic on your assigned local interface.

Dual-Mode Intelligence:
1. Exploit Detection: When an outgoing response contains a leaked flag, tracks
   back to the matching INCOMING REQUEST sent by that attacker and dumps the
   exploit payload for instant replay.
2. Bot Watcher: When an incoming request contains a newly planted flag from the
   organizer bot, alerts the team and saves the plant payload.
"""

import re
import os
import sys
import time
from datetime import datetime
from collections import defaultdict
from scapy.all import sniff, TCP, Raw, IP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "..", "attack"))
from config import MY_TEAM_IP, WEB_PORT, PWN_PORT, FLAG_REGEX_STR

OUTPUT_DIR = os.path.join(BASE_DIR, "captured_exploits")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FLAG_REGEX = re.compile(FLAG_REGEX_STR.encode())
seen_flags = set()

# Ring buffer storing recent incoming requests: (client_ip, target_port) -> bytes
recent_incoming = defaultdict(bytes)

KNOWN_SERVICE_PORTS = {WEB_PORT, PWN_PORT, 80, 443, 8000, 8080, 9999}

def packet_callback(pkt):
    if not (pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt.haslayer(IP)):
        return

    src_ip = pkt[IP].src
    dst_ip = pkt[IP].dst
    sport = pkt[TCP].sport
    dport = pkt[TCP].dport
    payload = pkt[Raw].load

    clean_my_ip = MY_TEAM_IP.strip()

    # Track incoming client requests hitting our services
    is_incoming = (dst_ip == clean_my_ip or dport in KNOWN_SERVICE_PORTS)
    if is_incoming:
        recent_incoming[(src_ip, dport)] = payload

    # Check for flags in this packet
    match = FLAG_REGEX.search(payload)
    if match:
        flag_str = match.group(0).decode(errors="ignore")
        if flag_str in seen_flags:
            return
        seen_flags.add(flag_str)

        ts = datetime.now().strftime("%H:%M:%S")

        # SCENARIO A: OUTGOING LEAK (Our service is sending a flag back to an attacker)
        if src_ip == clean_my_ip or sport in KNOWN_SERVICE_PORTS:
            attacker_ip = dst_ip
            service_port = sport

            print(f"\n[ALERT] [{ts}] FLAG LEAK DETECTED (OUTGOING RESPONSE)")
            print(f"  Attacker IP:  {attacker_ip}")
            print(f"  Service Port: {service_port}")
            print(f"  Stolen Flag:  {flag_str}")

            # Grab the exploit request that triggered this leak
            exploit_request = recent_incoming.get((attacker_ip, service_port))
            if exploit_request:
                filename = os.path.join(
                    OUTPUT_DIR,
                    f"exploit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{attacker_ip}.bin"
                )
                with open(filename, "wb") as f:
                    f.write(exploit_request)
                print(f"  [+] Captured Attacker's INCOMING EXPLOIT: {filename}")
                print(f"  [+] Instant Replay Command:")
                print(f"      python3 attack/exploit_replay.py {filename} --port {service_port}")
            else:
                # Fallback: save response packet
                resp_file = os.path.join(OUTPUT_DIR, f"leak_resp_{attacker_ip}.bin")
                with open(resp_file, "wb") as f:
                    f.write(payload)
                print(f"  [!] Note: Exploit request not buffered; saved leak response to {resp_file}")

        # SCENARIO B: INCOMING PLANT (Organizer SLA Bot planting fresh flag)
        else:
            bot_ip = src_ip
            service_port = dport
            print(f"\n[BOT] [{ts}] NEW FLAG PLANTED (INCOMING REQUEST)")
            print(f"  Bot IP:       {bot_ip}")
            print(f"  Service Port: {service_port}")
            print(f"  Planted Flag: {flag_str}")

            plant_file = os.path.join(
                OUTPUT_DIR,
                f"bot_plant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
            )
            with open(plant_file, "wb") as f:
                f.write(payload)
            print(f"  [+] Saved Bot Plant Request to: {plant_file}")

def main():
    interface = sys.argv[1] if len(sys.argv) > 1 else "any"
    print("=" * 60)
    print("INTERNAL TRAFFIC SNIFFER & EXPLOIT DUMPER")
    print(f"[*] Interface:  {interface}")
    print(f"[*] Output Dir: {OUTPUT_DIR}")
    print(f"[*] My Team IP: {MY_TEAM_IP}")
    print("[*] Radars active: listening for incoming plants and outgoing leaks...")
    print("=" * 60)
    try:
        sniff(iface=interface, filter="tcp", prn=packet_callback, store=0)
    except KeyboardInterrupt:
        print("\n[*] Sniffer stopped.")

if __name__ == "__main__":
    main()
