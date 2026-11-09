#!/bin/bash
# Copy the checkout's code to backhouse ~/worm-night/wbrain2/code (wbrain2; wtriage's pattern: no macOS xattrs).
cd "$(dirname "$0")/../../.."
COPYFILE_DISABLE=1 tar czf - --no-xattrs --exclude='__pycache__' src scripts/worm data/worm/model third_party "$@" \
  2>/dev/null | ssh backhouse wsl -d Ubuntu -- tar xzf - -C /home/greff/worm-night/wbrain2/code 2>&1 \
  | grep -v "Ignoring unknown" | head -3
