#!/usr/bin/env bash
# ==============================================================================
# PWNBOX BOOTSTRAP SCRIPT (Debian/Ubuntu)
# ==============================================================================
set -e

echo "[+] =========================================="
echo "[+] Starting Pwnbox Setup for AD CTF"
echo "[+] =========================================="

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. Install Essential Python Libraries
echo "[*] Installing/updating Python packages..."
pip install --break-system-packages \
    requests \
    pwntools \
    scapy \
    tqdm \
    rich \
    flask \
    paramiko \
    pycryptodome 2>/dev/null || true

# 2. Setup tmux configuration
echo "[*] Configuring tmux..."
cp "$BASE_DIR/bootstrap/tmux.conf" ~/.tmux.conf

# 3. Setup Shell Aliases
echo "[*] Configuring bash aliases..."
grep -qxF "source $BASE_DIR/bootstrap/aliases.sh" ~/.bashrc || echo "source $BASE_DIR/bootstrap/aliases.sh" >> ~/.bashrc

# 4. Download and setup Burp Suite Community Portable
echo "[*] Checking Burp Suite installation..."
BURP_DIR="$HOME/burp"
mkdir -p "$BURP_DIR"
if ! command -v burpsuite &> /dev/null && [ ! -f "$BURP_DIR/burpsuite.jar" ]; then
    echo "[*] Downloading Burp Suite Community JAR..."
    BURP_URL="https://portswigger.net/burp/releases/download?product=community&version=2024.11.1&type=Jar"
    curl -sSL -o "$BURP_DIR/burpsuite.jar" "$BURP_URL" || echo "[!] Internet download failed, use local copy if available."
    
    # Create wrapper launcher script
    cat << 'EOF' > /tmp/burp_launcher
#!/usr/bin/env bash
java -jar -Xmx2g "$HOME/burp/burpsuite.jar" "$@" &
EOF
    sudo cp /tmp/burp_launcher /usr/local/bin/burp 2>/dev/null || cp /tmp/burp_launcher "$HOME/burp/burp"
    chmod +x /usr/local/bin/burp 2>/dev/null || chmod +x "$HOME/burp/burp"
    echo "[+] Burp Suite launcher installed."
fi

# 5. Create runtime folders
mkdir -p "$BASE_DIR/traffic/captured_exploits"
touch "$BASE_DIR/attack/flags_queue.txt"

echo "[+] =========================================="
echo "[+] Setup Complete!"
echo "[+] Run: source ~/.bashrc"
echo "[+] =========================================="
