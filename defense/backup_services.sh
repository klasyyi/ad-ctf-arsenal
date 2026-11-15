#!/usr/bin/env bash
# ==============================================================================
# DEFENSE: IMMEDIATE SERVICE BACKUP & GIT INITIALIZER
# ==============================================================================
# Run this during the FIRST 10 MINUTES ("Golden Hour").
# 1. Takes full compressed archive of services.
# 2. Initializes git in challenge folders for instant diffing and rollback.
# ==============================================================================
set -e

BACKUP_ROOT="$HOME/ctf_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SNAPSHOT_DIR="$BACKUP_ROOT/snapshot_$TIMESTAMP"

mkdir -p "$SNAPSHOT_DIR"

echo "[*] =========================================="
echo "[*] CREATING INITIAL SERVICE SNAPSHOT"
echo "[*] Destination: $SNAPSHOT_DIR"
echo "[*] =========================================="

# 1. Backup standard challenge directories
for dir in /home /var/www /opt; do
    if [ -d "$dir" ]; then
        echo "[+] Backing up $dir..."
        tar -czf "$SNAPSHOT_DIR/$(basename $dir).tar.gz" -C "$dir" . 2>/dev/null || true
    fi
done

# 2. Backup Docker compose files and configs
if command -v docker &> /dev/null; then
    echo "[+] Dumping running Docker container info..."
    docker ps -a > "$SNAPSHOT_DIR/docker_ps_initial.txt"
fi

# 3. Initialize Git tracking in service directories for instant diffing
echo "[*] Initializing Git repositories in service directories..."
find /var/www /home /opt -maxdepth 2 -type f \( -name "docker-compose.yml" -o -name "Makefile" -o -name "index.php" -o -name "app.py" \) 2>/dev/null | while read -r marker; do
    chall_dir=$(dirname "$marker")
    if [ ! -d "$chall_dir/.git" ]; then
        echo "[+] Initializing git in: $chall_dir"
        (cd "$chall_dir" && git init -q && git add . && git commit -q -m "Initial challenge baseline" || true)
    fi
done

echo "[*] =========================================="
echo "[*] BACKUP COMPLETE!"
echo "[*] To check changes anytime: cd /service/dir && git status / git diff"
echo "[*] To rollback bad patch:   cd /service/dir && git checkout ."
echo "[*] =========================================="
