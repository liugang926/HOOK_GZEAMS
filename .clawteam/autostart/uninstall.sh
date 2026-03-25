#!/bin/bash
# ClawTeam Auto-Start Uninstallation Script for macOS

set -e

PLIST_DEST="$HOME/Library/LaunchAgents/com.clawteam.autostart.plist"
LOG_DIR="$HOME/.clawteam/logs"

echo "==> Uninstalling ClawTeam Auto-Start LaunchAgent..."
echo ""

# Unload the LaunchAgent
if [ -f "$PLIST_DEST" ]; then
    echo "==> Unloading LaunchAgent..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true

    echo "==> Removing plist file..."
    rm -f "$PLIST_DEST"
else
    echo "⚠ LaunchAgent plist not found at $PLIST_DEST"
fi

echo ""
echo "==> Uninstallation complete!"
echo ""
echo "Note: Log files are preserved at $LOG_DIR"
echo "To remove logs, run: rm -rf $LOG_DIR"
echo ""
