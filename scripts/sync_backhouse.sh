#!/usr/bin/env bash
# Push code and small parameter tables (not raw data, not runs) to backhouse WSL.
#   scripts/sync_backhouse.sh
set -euo pipefail
cd "$(dirname "$0")/.."
COPYFILE_DISABLE=1 tar --no-xattrs -cf - src scripts tests pyproject.toml uv.lock docs data/params data/model data/ontology data/derived data/measurements data/MANIFEST.yaml \
  | ssh backhouse 'wsl -d Ubuntu -- bash -c "mkdir -p ~/fly-emulation && tar -x -C ~/fly-emulation"'
echo synced
