#!/bin/bash
# Copy this checkout's code to backhouse ~/worm-night/wbody2/code (wbody2; wtriage's pattern). Extra args: more paths.
cd "$(dirname "$0")/../../.."
DEVELOPER_DIR=/Library/Developer/CommandLineTools git rev-parse --short HEAD > /tmp/wbody2_COMMIT
COPYFILE_DISABLE=1 tar czf - --no-xattrs --exclude='__pycache__' --exclude='third_party/metaworm/driver/obj' \
  --exclude='third_party/metaworm/driver/run_body' -s ',^/tmp/wbody2_COMMIT,COMMIT,' \
  src scripts data third_party pyproject.toml /tmp/wbody2_COMMIT "$@" 2>/dev/null \
  | ssh backhouse wsl -d Ubuntu -- tar xzf - -C /home/greff/worm-night/wbody2/code 2>&1 \
  | grep -v "Ignoring unknown\|Removing leading" | head -3
