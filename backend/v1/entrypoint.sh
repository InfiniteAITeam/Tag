#!/bin/bash
set -e

DISPLAY_NUM=99
XVFB_DISPLAY=":$DISPLAY_NUM"
XVFB_LOCK_FILE="/tmp/.X${DISPLAY_NUM}-lock"
XVFB_SOCKET_FILE="/tmp/.X11-unix/X${DISPLAY_NUM}"

echo "Cleaning up any stale Xvfb files..."
rm -f "$XVFB_LOCK_FILE"
rm -f "$XVFB_SOCKET_FILE"

echo "Starting Xvfb on display ${XVFB_DISPLAY}..."
Xvfb $XVFB_DISPLAY -screen 0 1980x1024x24 &
XVFB_PID=$!

# Trap termination signals to clean up Xvfb
cleanup() {
  echo "Stopping Xvfb..."
  kill -TERM "$XVFB_PID" 2>/dev/null || true
  wait "$XVFB_PID" 2>/dev/null || true
  echo "Cleaned up."
}
trap cleanup INT TERM EXIT

export DISPLAY=$XVFB_DISPLAY

# Wait a moment for Xvfb to be ready
sleep 3

setxkbmap us
# Run your app
echo "Running application..."
exec python "$@"