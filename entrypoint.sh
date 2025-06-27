#!/bin/sh
set -e

TARGET_DIR="/tmp/stich-worker"

# If the target directory is empty, copy contents from template
if [ -z "$(ls -A $TARGET_DIR)" ]; then
  echo "[INFO] Initializing /tmp/stich-worker from template..."
  cp -r /template/. "$TARGET_DIR"
else
  echo "[INFO] /tmp/stich-worker already initialized."
fi

# Now launch code-server
exec /init
