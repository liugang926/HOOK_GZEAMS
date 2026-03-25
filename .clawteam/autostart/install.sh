#!/bin/bash
# ClawTeam Auto-Start Installation Script for macOS
# This script installs the LaunchAgent for automatic startup on login

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.clawteam.autostart.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.clawteam.autostart.plist"
LOG_DIR="$HOME/.clawteam/logs"

echo "==> Installing ClawTeam Auto-Start LaunchAgent..."
echo ""

# Create necessary directories
echo "==> Creating directories..."
mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$LOG_DIR"

# Copy plist file
echo "==> Installing plist file to $PLIST_DEST"
cp "$PLIST_SRC" "$PLIST_DEST"

# Set proper permissions
echo "==> Setting permissions..."
chmod 644 "$PLIST_DEST"

# Load the LaunchAgent
echo "==> Loading LaunchAgent..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

# Verify installation
echo ""
echo "==> Verifying installation..."
if launchctl list | grep -q "com.clawteam.autostart"; then
    echo "✓ LaunchAgent installed and loaded successfully!"
else
    echo "⚠ Warning: LaunchAgent may not be active. Check logs."
fi

echo ""
echo "==> Installation complete!"
echo ""
echo "Management commands:"
echo "  Start service:   launchctl start com.clawteam.autostart"
echo "  Stop service:    launchctl stop com.clawteam.autostart"
echo "  View logs:       tail -f $LOG_DIR/autostart.log"
echo "  View errors:     tail -f $LOG_DIR/autostart.error.log"
echo "  Uninstall:       launchctl unload $PLIST_DEST && rm $PLIST_DEST"
echo ""
