#!/usr/bin/env bash
# ==============================================================================
# ROLLING PCAP RECORDER (Ring Buffer)
# ==============================================================================
# Captures rolling 60-second PCAPs and retains the last 15 files to prevent
# disk exhaustion during a 24-hour match.
# ==============================================================================
IFACE="${1:-any}"
PCAP_DIR="$HOME/pcap_dumps"
mkdir -p "$PCAP_DIR"

echo "[*] Starting rolling tcpdump on interface: $IFACE"
echo "[*] Storage directory: $PCAP_DIR"
echo "[*] Retaining maximum 15 chunks (60 seconds each)"

# -G 60: Rotate file every 60 seconds
# -W 15: Ring buffer of 15 files (auto-overwrites oldest)
sudo tcpdump -i "$IFACE" -s 0 -G 60 -W 15 -w "$PCAP_DIR/traffic_%Y%m%d_%H%M%S.pcap"
