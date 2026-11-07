#!/bin/bash
# sync code to backhouse (DEST, default ~/worm-night/wfit/repo). With REF set (a tag or commit), copies exactly that
# commit's src, scripts/worm/fit1, third_party, data/worm and pyproject.toml (git archive, so the run's code is the
# commit's). Without REF, copies the worktree's src and scripts/worm/fit1, plus "$@".
DEST=${DEST:-/home/greff/worm-night/wfit/repo}
cd /Users/ben/fly-emulation/.claude/worktrees/wormfit
ssh backhouse "wsl -d Ubuntu -- mkdir -p $DEST"
if [ -n "$REF" ]; then
  git archive --format=tar "$REF" src scripts/worm/fit1 third_party data/worm pyproject.toml | \
    ssh backhouse "wsl -d Ubuntu -- tar xf - -C $DEST"
  git rev-parse "$REF^{commit}" | ssh backhouse "wsl -d Ubuntu -- tee $DEST/COMMIT"
else
  COPYFILE_DISABLE=1 tar czf - --no-xattrs --exclude='__pycache__' src scripts/worm/fit1 "$@" | \
    ssh backhouse "wsl -d Ubuntu -- tar xzf - -C $DEST" 2>&1 | grep -v "unknown extended header"
fi
true
