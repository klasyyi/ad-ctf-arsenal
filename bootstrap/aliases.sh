# AD CTF Shell Aliases and Helpers
alias ll='ls -la --color=auto'
alias flaggrep='grep -r -E "(FLAG\{[A-Za-z0-9_-]+\}|[A-Z0-9]{32}=)" .'
alias docker-status='docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias ports='ss -tulpn'
alias sniff-http='sudo tshark -i any -Y "http.request" -T fields -e ip.src -e ip.dst -e http.request.method -e http.request.uri'
alias sniff-flags='sudo tshark -i any -Y "frame contains \"FLAG\"" -x'

# Quick helper to feed a flag into the queue
submit-flag() {
    if [ -z "$1" ]; then
        echo "Usage: submit-flag <FLAG_STRING>"
    else
        echo "$1" >> "$HOME/ad-ctf-arsenal/attack/flags_queue.txt"
        echo "[+] Queued: $1"
    fi
}
