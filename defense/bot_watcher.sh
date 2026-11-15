#!/usr/bin/env bash
# ==============================================================================
# RADAR 1: REAL-TIME ORGANIZER SLA BOT WATCHER
# ==============================================================================
# Continuously monitors web server logs and network traffic to detect:
# 1. When the SLA bot visits your server.
# 2. Which URLs and endpoints the bot calls.
# 3. Newly planted flag strings.
# ==============================================================================

echo "[*] =========================================="
echo "[*] RADAR 1: ORGANIZER BOT WATCHER ACTIVE"
echo "[*] Monitoring web logs and HTTP traffic..."
echo "[*] =========================================="

# Check for existing web server log files
LOG_FILES=""
for log in /var/log/nginx/access.log /var/log/apache2/access.log /var/log/httpd/access_log /tmp/traffic_l7.log; do
    if [ -f "$log" ]; then
        LOG_FILES="$LOG_FILES $log"
    fi
done

if [ -n "$LOG_FILES" ]; then
    echo "[+] Found web logs: $LOG_FILES"
    echo "[*] Streaming live bot requests (Press Ctrl+C to stop)..."
    echo "--------------------------------------------------------"
    sudo tail -n 20 -f $LOG_FILES | grep --line-buffered -E "(POST|GET|PUT|DELETE|FLAG\{|[A-Z0-9]{32}=)"
else
    echo "[!] No standard web log files found. Falling back to live tshark network sniffer..."
    if command -v tshark &> /dev/null; then
        sudo tshark -i any -Y "http.request" -T fields \
            -e ip.src \
            -e http.request.method \
            -e http.request.uri \
            -e http.user_agent
    else
        echo "[!] tshark not installed. Install via: sudo apt-get install -y tshark"
        exit 1
    fi
fi
