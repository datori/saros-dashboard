#!/usr/bin/env bash
# One-time setup: symlink the systemd user unit, enable, and start the service.
# Idempotent — safe to re-run after moving the repo or updating the unit file.
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_SRC="$REPO_ROOT/deploy/vacuum-dashboard.service"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
UNIT_DEST="$SYSTEMD_USER_DIR/vacuum-dashboard.service"

mkdir -p "$SYSTEMD_USER_DIR"

# Remove old symlink if it exists (idempotent re-link)
if [ -L "$UNIT_DEST" ]; then
    rm "$UNIT_DEST"
fi

ln -s "$UNIT_SRC" "$UNIT_DEST"
echo "Linked $UNIT_DEST -> $UNIT_SRC"

systemctl --user daemon-reload
systemctl --user enable vacuum-dashboard
systemctl --user restart vacuum-dashboard

echo "Service enabled and started."
echo "Note: to run at boot without login, enable linger: loginctl enable-linger $USER"
