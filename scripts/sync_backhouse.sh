#!/usr/bin/env bash
# Push the working tree's code (not data, not runs) to backhouse WSL.
#   scripts/sync_backhouse.sh
set -euo pipefail
cd "$(dirname "$0")/.."
COPYFILE_DISABLE=1 tar --no-xattrs -cf - src scripts tests pyproject.toml uv.lock docs \
  | ssh backhouse 'wsl -d Ubuntu -- bash -c "mkdir -p ~/fly-emulation && tar -x -C ~/fly-emulation"'
echo synced
