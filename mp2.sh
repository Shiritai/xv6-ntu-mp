#!/bin/bash
# mp2.sh - A unified management script for NTUOS 2025 MP2 assignments.
# Provides environment setup, container management, and testing utilities.

# Constants
SCRIPT_DIR=$(realpath "$(dirname "$0")")
IMAGE_NAME="ntuos/mp2"
CONTAINER_NAME="mp2"
TEST_DIR="$HOME/run_test"

# Check if sudo is required for Docker
DOCKER_CMD="docker"
if ! docker ps >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

DOCKER_IT_FLAG="-it"
if [ -n "$GITHUB_ACTIONS" ]; then
    DOCKER_IT_FLAG=""
fi

# Function to check if container is running
is_container_running() {
    [ -n "$($DOCKER_CMD ps -q --filter name="^$CONTAINER_NAME$")" ]
}

# Try with sudo if task failed
maysudo() {
    if ! "$@" >/dev/null 2>&1; then
        echo "Warning: '$*' failed, retrying with sudo..." >&2
        sudo "$@" >/dev/null 2>&1 || { echo "Error: '$*' failed even with sudo." >&2; return 1; }
    fi
}

# change owner of file/directory if needed
chown_if_need() {
    local target="$1"
    local current_user_group
    local desired_user_group="$(id -u):$(id -g)"

    if [ ! -e "$target" ]; then
        echo "Warning: '$target' does not exist, skipping chown." >&2
        return 1
    fi

    if [[ "$OSTYPE" == "darwin"* ]]; then
        current_user_group=$(stat -f "%u:%g" "$target" 2>/dev/null) || {
            echo "Error: Failed to stat '$target' on macOS." >&2
            return 1
        }
    else
        current_user_group=$(stat -c "%u:%g" "$target" 2>/dev/null) || {
            echo "Error: Failed to stat '$target' on Linux." >&2
            return 1
        }
    fi

    if [ "$current_user_group" != "$desired_user_group" ]; then
        maysudo chown -R "$(id -u):$(id -g)" "$target" >/dev/null 2>&1 || {
            echo "Warning: Failed to chown '$target', may not need to chown." >&2
            return 1
        }
    fi
}

START_IMAGE="$DOCKER_CMD run $DOCKER_IT_FLAG -v $(realpath $SCRIPT_DIR):/home/student/mp2 -w /home/student/mp2 -u 1000:1000"
START_VOLATILE_IMAGE="$START_IMAGE --rm $IMAGE_NAME"
START_PERSISTENT_IMAGE="$START_IMAGE -d --name $CONTAINER_NAME $IMAGE_NAME"

# Run test with basic timeout and error handling
run_test() {
    if ! timeout 5m python3 "$TEST_DIR/test/run_mp2.py" "$@"; then
        echo "Error: Test failed or timed out after 5 minutes." >&2
        printf "Interpretation Error or Timeout!\nFailed to parse your slab.\nIf you think this is buggy, please console to the admin.\nScore: 0/0\n"
        return 1
    fi
}

# Function to display usage
usage() {
    cat <<EOF
mp2.sh - Command line tool for ntuos2025 MP2

Usage:
  ./mp2.sh setup                  Setup the development environment for this repository.

  ./mp2.sh pull                   Pull the '$IMAGE_NAME' Docker image.

  ./mp2.sh update                 Update the repository according to Shiritai/xv6-ntu-mp2.

  ./mp2.sh qemu                   Compile and run xv6 in a volatile container (MP0,1 style).
  
  ./mp2.sh clean                  Cleanup compiled objectives produced by mp2.sh/make qemu.

  ./mp2.sh test [case]            Run specific public test cases in a volatile container:
    all                           - Run all specification and functionality tests.
    slab                          - Check slab structure design score (partial bonus).
    func <from> [<to>]            - Run functionality tests by number:
                                    - Range: <from> to <to> (inclusive).
                                    - If <to> omitted, runs only <from>.
                                    - If both omitted, runs all (0-24).
                                    - Indices: 0 to 24 (inclusive).
    list                          - Check Linux-style list API usage score (bonus).
    cache                         - Check in-cache fragmentation score (bonus).
    custom                        - Run custom test from 'test/custom/mytest.txt'.

  ./mp2.sh container [cmd]        Manage the development container:
    start                         - Start the container in the background.
    bash                          - Open a bash shell in the running container.
    finish                        - Stop and remove the container.

  ./mp2.sh testcase [case]        Run test cases directly (assumes inside container):
    all                           - Run all specification and functionality tests.
    slab                          - Check slab structure design score (partial bonus).
    func <from> [<to>]            - Run functionality tests by number:
                                    - Range: <from> to <to> (inclusive).
                                    - If <to> omitted, runs only <from>.
                                    - If both omitted, runs all (0-24).
                                    - Indices: 0 to 24 (inclusive).
    list                          - Check Linux-style list API usage score (bonus).
    cache                         - Check in-cache fragmentation score (bonus).
    custom                        - Run custom test from 'test/custom/mytest.txt'.
EOF
}

# Main logic: Handle different commands based on the first argument
case "$1" in
    "pull")
        echo "Pulling '$IMAGE_NAME'... This may take a few minutes."
        if $DOCKER_CMD pull "$IMAGE_NAME"; then
            echo "Successfully pulled '$IMAGE_NAME'."
        else
            echo "Error: Failed to pull '$IMAGE_NAME'." >&2
            exit 1
        fi
        ;;
    "setup")
        HOOKS_DIR=".git/hooks"
        mkdir -p "$HOOKS_DIR" || exit 1

        # List of hook names.
        HOOKS=(pre-commit pre-push)

        for hook in "${HOOKS[@]}"; do
            ln -sf "$SCRIPT_DIR/scripts/${hook}" "$HOOKS_DIR/$hook" || exit 1
            chown_if_need "$SCRIPT_DIR"
        done
        ;;
    "qemu")
        $START_VOLATILE_IMAGE ./mp2.sh chown_if_need .
        $START_VOLATILE_IMAGE make qemu
        chown_if_need "$SCRIPT_DIR"
        ;;
    "clean")
        chown_if_need "$SCRIPT_DIR"
        make clean
        ;;
    "update")
        if ! command -v curl; then
            echo "Please install curl or download and run <YOUR_REPO>/update.sh from https://github.com/Shiritai/xv6-ntu-mp2/blob/ntuos/mp2-submit/update.sh by yourself."
        else
            UPDATE_SCRIPT="$SCRIPT_DIR/update.sh"
            curl https://raw.githubusercontent.com/Shiritai/xv6-ntu-mp2/refs/heads/ntuos/mp2-submit/update.sh --output "$UPDATE_SCRIPT"
            maysudo chmod +x "$UPDATE_SCRIPT"
            "$UPDATE_SCRIPT"            # update this repo
            "$SCRIPT_DIR/mp2.sh" setup  # To prevent no-git-hook issue
        fi
        ;;
    "test")
        $START_VOLATILE_IMAGE ./mp2.sh testcase "$2" "$3" "$4" "$5"
        ([[ -d $SCRIPT_DIR/out ]] && chown_if_need "$SCRIPT_DIR/out") || true
        ;;
    "container")
        case "$2" in
            "start")
                if is_container_running; then
                    echo "Container '$CONTAINER_NAME' is already running."
                else
                    echo "Starting '$CONTAINER_NAME'..."
                    if $START_PERSISTENT_IMAGE bash; then
                        echo "Container '$CONTAINER_NAME' started."
                        $DOCKER_CMD exec "$CONTAINER_NAME" ./mp2.sh chown_if_need .
                    else
                        echo "Error: Failed to start container." >&2
                        exit 1
                    fi
                fi
                ;;
            "bash")
                if is_container_running; then
                    $DOCKER_CMD exec $DOCKER_IT_FLAG "$CONTAINER_NAME" bash
                else
                    echo "Error: Container '$CONTAINER_NAME' is not running." >&2
                    exit 1
                fi
                ;;
            "finish")
                if is_container_running; then
                    echo "Stopping container '$CONTAINER_NAME'..."
                    $DOCKER_CMD rm -f "$CONTAINER_NAME"
                    echo "Container '$CONTAINER_NAME' stopped."
                    chown_if_need "$SCRIPT_DIR"
                else
                    echo "Container '$CONTAINER_NAME' is not running."
                fi
                ;;
            *)
                usage
                exit 1
                ;;
        esac
        ;;
    "testcase")
        # Copy this repo to $TEST_DIR and run it,
        # to ensure that developers can edit when running tests
        if [ ! -d "$TEST_DIR" ]; then
            mkdir -p "$TEST_DIR" || { echo "Error: Failed to create '$TEST_DIR'." >&2; exit 1; }
        fi
        cur_wd=$(pwd)
        rm -rf "$TEST_DIR" || true
        cp -r . "$TEST_DIR" || { echo "Error: Failed to copy files to '$TEST_DIR'." >&2; exit 1; }
        cd "$TEST_DIR" || { echo "Error: Failed to change directory to '$TEST_DIR'." >&2; exit 1; }

        case "$2" in
        func)
            if [ -n "$3" ]; then
                if ! [[ "$3" =~ ^[0-9]+$ ]] || [ "$3" -lt 0 ] || [ "$3" -gt 24 ]; then
                    echo "Error: '<from>' must be a number between 0 and 24." >&2
                    exit 1
                fi
                from="$3"
                to=$from
                if [ -n "$4" ]; then
                    if ! [[ "$4" =~ ^[0-9]+$ ]] || [ "$4" -lt "$from" ] || [ "$4" -gt 24 ]; then
                        echo "Error: '<to>' must be a number between $from and 24." >&2
                        exit 1
                    fi
                    to="$4"
                fi
                to=$((to + 1))
                run_test "$from" "$to"
            else
                run_test
            fi
            ;;
        all|slab|list|cache|custom)
            run_test "$2"
            ;;
        private)
            if [ -n "$3" ]; then
                from="$3"
                to=$from
                [ -n "$4" ] && to="$4"
                to=$((to + 1))
                run_test private "$from" "$to"
            else
                run_test private
            fi
            ;;
        *)
            usage
            exit 0
            ;;
        esac

        if [ -d "$TEST_DIR/out" ]; then
            maysudo cp -r "$TEST_DIR/out" "$cur_wd" || echo "Warning: Failed to copy output to $cur_wd"
            chown_if_need "$cur_wd/out"
        fi
        ;;
    chown_if_need)
        chown_if_need "$2"
        ;;
    *)
        usage
        exit 0
        ;;
esac
