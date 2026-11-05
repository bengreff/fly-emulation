#!/usr/bin/env bash
# Push the organism-agnostic package and worm scripts to backhouse ~/worm-spike (code only).
set -euo pipefail
cd "$(dirname "$0")/../.."
COPYFILE_DISABLE=1 tar --no-xattrs -cf - src/bioemu src/wormemu scripts/worm data/worm/spike 2>/dev/null \
  | ssh backhouse 'wsl -d Ubuntu -- bash -c "mkdir -p ~/worm-spike/repo && tar -x -C ~/worm-spike/repo"'
