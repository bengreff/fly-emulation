#!/bin/bash
# Copy scripts/worm/triage (and optionally more paths) to backhouse ~/worm-night/wtriage/code (wtriage).
cd "$(dirname "$0")/../../.."
COPYFILE_DISABLE=1 tar czf - --no-xattrs --exclude='__pycache__' scripts/worm/triage "$@" 2>/dev/null \
  | ssh backhouse wsl -d Ubuntu -- tar xzf - -C /home/greff/worm-night/wtriage/code 2>&1 | grep -v "Ignoring unknown" | head -3
