#!/bin/bash

# Constants
SCRIPT_DIR=$(realpath "$(dirname "$0")")
IMAGE_NAME="ntuos/mp2"
CONTAINER_NAME="mp2"
TEST_DIR="$HOME/run_test"

# Check if sudo is required for Docker
if ! docker ps >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

# Function to check if container is running
is_container_running() {
    [ -n "$($DOCKER_CMD ps -q --filter name="$CONTAINER_NAME")" ]
}

# Function to display usage
usage() {
    cat <<EOF
mp2.sh - Command Line Tool for ntuos2025 MP2 (Last Updated: 2025/03/19)

Usage:
  ./mp2.sh pull                   Pull the '$IMAGE_NAME' Docker image.

  ./mp2.sh test <from> [<to>]     Run public test cases in a volatile container.
                                  - Tests run from <from> to <to> (exclusive).
                                  - If <to> is omitted, runs only test <from>.
                                  - If both are omitted, runs all test cases.
                                  - Indices start at 0.

  ./mp2.sh container [cmd]        Manage the development container:
    start                         Start the container in the background.
    bash                          Open a bash shell in the running container.
    finish                        Stop and remove the container.

  ./mp2.sh testcase <from> [<to>] Run test cases directly without a volatile container.
                                  - Same range rules as 'test' apply.
                                  - Assume you're in the container.

  ./mp2.sh testspec [opt]         Run specification test cases:
    slab                          Check slab structure design score (partial bonus).
    list                          Check Linux-style list API usage score (bonus).
    cache                         Check in-cache fragmentation score (bonus).

  ./mp2.sh testall                   Run all specification and functionality tests.
EOF
}

# Main logic
case "$1" in
    "pull")
        echo "Pulling '$IMAGE_NAME'..."
        if $DOCKER_CMD pull "$IMAGE_NAME"; then
            echo "Successfully pulled '$IMAGE_NAME'."
        else
            echo "Error: Failed to pull '$IMAGE_NAME'." >&2
            exit 1
        fi
        ;;
    "test")
        $DOCKER_CMD run --rm -it -v "$(realpath "$SCRIPT_DIR"):/home/student/mp2" \
            -w /home/student/mp2 -u 1000:1000 "$IMAGE_NAME" ./mp2.sh testcase "$2" "$3"
            # -w /home/student/mp2 -u 1000:1000 "$IMAGE_NAME" bash
        ;;
    "container")
        case "$2" in
            "start")
                if is_container_running; then
                    echo "Container '$CONTAINER_NAME' is already running."
                else
                    echo "Starting '$CONTAINER_NAME'..."
                    if $DOCKER_CMD run -d -it -v "$(realpath "$SCRIPT_DIR"):/home/student/mp2" \
                        -w /home/student/mp2 -u 1000:1000 --name "$CONTAINER_NAME" "$IMAGE_NAME" bash; then
                        echo "Container '$CONTAINER_NAME' started."
                        $DOCKER_CMD exec "$CONTAINER_NAME" sudo chown -R 1000:1000 .
                    else
                        echo "Error: Failed to start container." >&2
                        exit 1
                    fi
                fi
                ;;
            "bash")
                if is_container_running; then
                    $DOCKER_CMD exec -it "$CONTAINER_NAME" bash
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
                    sudo chown -R "$(id -u):$(id -g)" "$SCRIPT_DIR"
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
        if [ ! -d "$TEST_DIR" ]; then
            mkdir -p "$TEST_DIR" || { echo "Error: Failed to create '$TEST_DIR'." >&2; exit 1; }
        fi
        rm -rf "$TEST_DIR" || true
        cp -r . "$TEST_DIR" || { echo "Error: Failed to copy files to '$TEST_DIR'." >&2; exit 1; }
        cd "$TEST_DIR" || { echo "Error: Failed to change directory to '$TEST_DIR'." >&2; exit 1; }
        if [ -n "$2" ]; then
            from="$2"
            to=$((from + 1))
            [ -n "$3" ] && to="$3"
            python3 test/run_mp2.py "$from" "$to"
        else
            python3 test/run_mp2.py
        fi
        ;;
    "private")
        if [ ! -d "$TEST_DIR" ]; then
            mkdir -p "$TEST_DIR" || { echo "Error: Failed to create '$TEST_DIR'." >&2; exit 1; }
        fi
        rm -rf "$TEST_DIR" || true
        cp -r . "$TEST_DIR" || { echo "Error: Failed to copy files to '$TEST_DIR'." >&2; exit 1; }
        cd "$TEST_DIR" || { echo "Error: Failed to change directory to '$TEST_DIR'." >&2; exit 1; }
        if [ -n "$2" ]; then
            from="$2"
            to=$((from + 1))
            [ -n "$3" ] && to="$3"
            python3 test/run_mp2.py private "$from" "$to"
        else
            python3 test/run_mp2.py private
        fi
        ;;
    "testspec")
        if [ ! -d "$TEST_DIR" ]; then
            mkdir -p "$TEST_DIR" || { echo "Error: Failed to create '$TEST_DIR'." >&2; exit 1; }
        fi
        rm -rf "$TEST_DIR" || true
        cp -r . "$TEST_DIR" || { echo "Error: Failed to copy files to '$TEST_DIR'." >&2; exit 1; }
        cd "$TEST_DIR" || { echo "Error: Failed to change directory to '$TEST_DIR'." >&2; exit 1; }
        python3 test/run_mp2.py "$2"
        ;;
    "testall")
        if [ ! -d "$TEST_DIR" ]; then
            mkdir -p "$TEST_DIR" || { echo "Error: Failed to create '$TEST_DIR'." >&2; exit 1; }
        fi
        rm -rf "$TEST_DIR" || true
        cp -r . "$TEST_DIR" || { echo "Error: Failed to copy files to '$TEST_DIR'." >&2; exit 1; }
        cd "$TEST_DIR" || { echo "Error: Failed to change directory to '$TEST_DIR'." >&2; exit 1; }
        python3 test/run_mp2.py all
        ;;
    *)
        usage
        exit 0
        ;;
esac
