#!/bin/bash
# sync the worktree's code to backhouse (DEST, default ~/worm-night/wfit/repo): src, scripts/worm/fit1, plus "$@"
DEST=${DEST:-/home/greff/worm-night/wfit/repo}
cd /Users/ben/fly-emulation/.claude/worktrees/wormfit
ssh backhouse "wsl -d Ubuntu -- mkdir -p $DEST"
COPYFILE_DISABLE=1 tar czf - --no-xattrs --exclude='__pycache__' src scripts/worm/fit1 "$@" | \
  ssh backhouse "wsl -d Ubuntu -- tar xzf - -C $DEST" 2>&1 | grep -v "unknown extended header"
true
