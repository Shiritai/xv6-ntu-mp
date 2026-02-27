#!/bin/bash
# mp.sh - Unified management script for xv6-ntu-template

# ------------------------------------------------------------------------------
# 1. Configuration & Utilities
# ------------------------------------------------------------------------------

# Colors for friendly output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

hint() {
    echo -e "${BOLD}[HINT]${NC}  $1"
}

# Constants
SCRIPT_DIR=$(realpath "$(dirname "$0")")

# Load configuration
if [ -f "$SCRIPT_DIR/mp.conf" ]; then
    source "$SCRIPT_DIR/mp.conf"
else
    error "mp.conf not found. Using defaults."
    exit 1
fi

# Configuration Defaults
IMAGE_NAME="${DOCKER_IMAGE:-ntuos/mp2}" # Default fallback

# ------------------------------------------------------------------------------
# 2. Environment Checks
# ------------------------------------------------------------------------------

check_os() {
    local os_name=$(uname -s)
    local kernel_release=$(uname -r)

    case "$os_name" in
        Linux*)
            if [[ "$kernel_release" == *"microsoft"* || "$kernel_release" == *"Microsoft"* || "$kernel_release" == *"WSL"* ]]; then
                 # WSL2 is supported
                 :
            else
                 # Native Linux is supported
                 :
            fi
            ;;
        Darwin*)
            # macOS is supported
            :
            ;;
        CYGWIN*|MINGW*|MSYS*)
            # Detect legacy Windows shells (Git Bash, Cygwin, MinGW)
            error "Unsupported Shell Environment!"
            hint "You appear to be running in Windows CMD, PowerShell, or Git Bash."
            hint "Please install **WSL2 (Ubuntu)** and run this script from there."
            exit 1
            ;;
        *)
            warn "Unknown OS ($os_name). Proceeding with caution..."
            ;;
    esac
}

check_docker() {
    # Simulation Mode Bypass
    if [ -n "$SIMULATION_MODE" ]; then
        return
    fi

    # 2.1 Check if Docker binary exists
    if command -v docker > /dev/null 2>&1; then
        DOCKER_CMD="docker"
    elif command -v podman > /dev/null 2>&1; then
        DOCKER_CMD="podman"
        info "Using Podman as container engine."
    else
        error "Container engine not found."
        hint "Please install Docker Desktop (Windows/macOS) or Docker Engine (Linux)."
        exit 1
    fi

    # 2.2 Check if Docker Daemon is running
    # We use 'docker info' which requires daemon connection
    if ! $DOCKER_CMD info > /dev/null 2>&1; then
        # If standard check fails, try sudo (for Linux)
        if sudo $DOCKER_CMD info > /dev/null 2>&1; then
             warn "Docker daemon is running but requires sudo."
             DOCKER_CMD="sudo $DOCKER_CMD"
        else
             # Daemon is truly unreachable
             error "Docker Daemon is not running!"
             
             if [[ "$(uname -s)" == "Darwin" ]]; then
                 hint "On macOS, please make sure **Docker Desktop** is open and running."
             elif [[ "$(uname -r)" == *"microsoft"* || "$(uname -r)" == *"Microsoft"* ]]; then
                 hint "On WSL2, please make sure **Docker Desktop** is running in Windows."
                 hint "Ensure 'Settings > Resources > WSL Integration' is enabled."
             else
                 hint "On Linux, try starting it with: sudo systemctl start docker"
             fi
             exit 1
        fi
    fi

    # 2.3 Configure Daemon Options
    DOCKER_CMD_OPTS=""
    
    # Check for TTY (interactive mode)
    # If GITHUB_ACTIONS is set, disable TTY to avoid 'the input device is not a TTY' errors
    if [ -t 1 ] && [ -z "$GITHUB_ACTIONS" ]; then
        DOCKER_CMD_OPTS+=" -it"
    fi

    # Architecture check for Apple Silicon / ARM64
    if [[ "$(uname -m)" == "arm64" || "$(uname -m)" == "aarch64" ]]; then
        # info "ARM64 architecture detected."
        # No warning needed now as we support multi-arch
        :
    fi

    # Podman specific fix
    if [[ "$DOCKER_CMD" == *"podman"* ]]; then
        # Fix permission mapping for podman
        DOCKER_CMD_OPTS+=" --security-opt label=disable"
        # If not root, keep id
        if [[ "$DOCKER_CMD" != *"sudo"* ]]; then
             DOCKER_CMD_OPTS+=" --userns=keep-id"
        fi
    fi
}

check_hooks() {
    # Skip hook check in GITHUB_ACTIONS or if in Simulation Mode
    if [ -n "$GITHUB_ACTIONS" ] || [ -n "$SIMULATION_MODE" ]; then
        return
    fi

    local hooks_installed=true
    for hook in pre-commit pre-push; do
        if [ ! -f "$SCRIPT_DIR/.git/hooks/$hook" ]; then
            hooks_installed=false
            break
        fi
    done

    if [ "$hooks_installed" = false ]; then
        warn "Git Hooks are NOT installed. File protection is inactive."
        hint "Run './mp.sh init' to install hooks and protect your work."
    fi
}

check_environment() {
    check_os
    check_docker
    check_hooks
}

# Run Checks early
check_environment

# ------------------------------------------------------------------------------
# 3. Helper Functions
# ------------------------------------------------------------------------------

maysudo() {
    if ! "$@" >/dev/null 2>&1; then
        sudo "$@" >/dev/null 2>&1 || { error "Command '$*' failed even with sudo."; return 1; }
    fi
}

chown_if_need() {
    local target="$1"
    if [ ! -e "$target" ]; then return 1; fi
    
    local current_user_group
    if [[ "$OSTYPE" == "darwin"* ]]; then
        current_user_group=$(stat -f "%u:%g" "$target" 2>/dev/null)
    else
        current_user_group=$(stat -c "%u:%g" "$target" 2>/dev/null)
    fi
    
    local desired_user_group="$(id -u):$(id -g)"
    
    if [ "$current_user_group" != "$desired_user_group" ]; then
        # Only warn/run if we are not using podman (which handles mapping)
        # or if we are using docker
        if [[ "$DOCKER_CMD" != *"podman"* ]]; then
             maysudo chown -R "$desired_user_group" "$target" >/dev/null 2>&1
        fi
    fi
}

ensure_docker_start_cmd() {
    if [ -n "$SIMULATION_MODE" ]; then
        START_IMAGE=""
        info "Simulation Mode: Docker bypassed."
    else
        START_IMAGE="$DOCKER_CMD run $DOCKER_CMD_OPTS -v $(realpath "$SCRIPT_DIR"):/home/student/xv6 -w /home/student/xv6 -u $(id -u):$(id -g) --rm $IMAGE_NAME"
    fi
}

# Prepare execution command
ensure_docker_start_cmd

# ------------------------------------------------------------------------------
# 4. Grading & Sanitization Logic
# ------------------------------------------------------------------------------

check_ta_commit() {
    # If TA_EMAILS is not defined, skip this check
    if [ -z "$TA_EMAILS" ]; then
        return 0
    fi

    # Bypass check if in Official Grading mode
    if [ -n "$OFFICIAL_GRADING" ]; then
        return 0
    fi

    # Get the committer email of the HEAD commit
    local committer_email
    committer_email=$(git log -1 --format='%ce')

    for ta_email in $TA_EMAILS; do
        if [ "$committer_email" == "$ta_email" ]; then
            warn "Skipping execution: Commit by TA ($committer_email)."
            exit 0
        fi
    done
}



# ------------------------------------------------------------------------------
# 5. Main Logic
# ------------------------------------------------------------------------------

case "$1" in
    "init"|"setup")
        info "Initializing environment for $ASSIGNMENT..."
        mkdir -p "$SCRIPT_DIR/.git/hooks"
        
        # Install hooks from scripts/
        hook_count=0
        if [ -d "$SCRIPT_DIR/scripts" ]; then
            for hook in pre-commit pre-push; do
                if [ -f "$SCRIPT_DIR/scripts/$hook" ]; then
                    ln -sf "../../scripts/$hook" "$SCRIPT_DIR/.git/hooks/$hook"
                    hook_count=$((hook_count + 1))
                fi
            done
        fi
        
        if [ $hook_count -eq 0 ]; then
            warn "No hook templates found in grade/hooks/."
        else
            info "Successfully installed $hook_count Git hooks."
        fi
        info "Initialization complete."
        ;;
    "qemu")
        info "Starting QEMU in $IMAGE_NAME..."
        $START_IMAGE make qemu
        chown_if_need "."
        ;;
    "test"|"grade")
        check_ta_commit
        info "Running tests for $ASSIGNMENT..."
        # Pass arguments to run.py
        shift
        $START_IMAGE python3 grade/run.py "$@"
        chown_if_need "."
        ;;

    "clean")
        info "Cleaning build artifacts..."
        $START_IMAGE make clean
        chown_if_need "."
        ;;
    *)
        echo "Usage: $0 {init|qemu|test|grade|clean}"
        exit 1
        ;;
esac
