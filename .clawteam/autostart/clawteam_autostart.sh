#!/bin/bash
# ClawTeam Auto-Start Shell Configuration
# Source this file from ~/.zshrc or ~/.bashrc
# Add this line to your shell config: source /Users/abner/My_Project/HOOK_GZEAMS/.clawteam/autostart/clawteam_autostart.sh

# ClawTeam Auto-Start Configuration
CLAWTEAM_AUTOSTART_VERSION="1.0.0"

# Check if clawteam command exists
if command -v clawteam &> /dev/null; then

    # Set ClawTeam identity for the session
    export CLAWTEAM_AGENT_ID="leader-001"
    export CLAWTEAM_AGENT_NAME="leader"
    export CLAWTEAM_AGENT_TYPE="leader"

    # ClawTeam binary path
    export CLAWTEAM_BIN="$(command -v clawteam)"

    # Project directory
    export CLAWTEAM_PROJECT_DIR="/Users/abner/My_Project/HOOK_GZEAMS"
    export CLAWTEAM_TEAM_NAME="hook-team"

    # Log directory
    export CLAWTEAM_LOG_DIR="$HOME/.clawteam/logs"

    # Create log directory if it doesn't exist
    mkdir -p "$CLAWTEAM_LOG_DIR"

    # ClawTeam alias shortcuts
    alias ct='clawteam'
    alias ct-board='clawteam board'
    alias ct-task='clawteam task'
    alias ct-inbox='clawteam inbox'
    alias ct-spawn='clawteam spawn'
    alias ct-team='clawteam team'

    # Quick commands for hook-team
    alias ct-status='clawteam board show hook-team'
    alias ct-live='clawteam board live hook-team --interval 5'
    alias ct-attach='clawteam board attach hook-team'
    alias ct-tasks='clawteam task list hook-team'

    # Function to auto-start team monitoring
    clawteam_start() {
        echo "==> Starting ClawTeam team: $CLAWTEAM_TEAM_NAME"
        cd "$CLAWTEAM_PROJECT_DIR" || return 1
        clawteam board live "$CLAWTEAM_TEAM_NAME" --interval 5
    }

    # Function to spawn a new worker
    clawteam_spawn_worker() {
        local worker_name="${1:-worker$(date +%s)}"
        local task="${2:-Auto-assigned task}"
        echo "==> Spawning worker: $worker_name with task: $task"
        cd "$CLAWTEAM_PROJECT_DIR" || return 1
        clawteam spawn --team "$CLAWTEAM_TEAM_NAME" --agent-name "$worker_name" --task "$task"
    }

    # Function to check ClawTeam status
    clawteam_status() {
        echo "==> ClawTeam Status"
        echo "  Binary: $CLAWTEAM_BIN"
        echo "  Project: $CLAWTEAM_PROJECT_DIR"
        echo "  Team: $CLAWTEAM_TEAM_NAME"
        echo "  Logs: $CLAWTEAM_LOG_DIR"
        echo ""
        clawteam board show "$CLAWTEAM_TEAM_NAME" 2>/dev/null || echo "Team not found or not running"
    }

    # Auto-start message (comment out if you don't want to see this)
    # echo "🤖 ClawTeam environment loaded. Type 'clawteam_status' for info."

else
    echo "⚠ ClawTeam not found. Install with: pip install clawteam"
fi
