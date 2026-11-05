#!/bin/bash
# Build the headless MetaWorm body driver. Needs only a C++14 compiler and Eigen 3 (header-only); the upstream
# CMake also asked for Boost.Python, PythonLibs and OpenMP, but sim/ uses no Boost, and its one OpenMP loop
# (sim/fem/World.cpp, the local step) was commented out upstream. Upstream used -std=gnu++11; Eigen 3.5 needs C++14.
# Usage: driver/build.sh [eigen_include_dir]          -> driver/run_body      (one thread, as published)
#        OMP=1 driver/build.sh [eigen_include_dir]    -> driver/run_body_omp  (upstream's OpenMP loop on; set
#        OMP_NUM_THREADS; same result to 9 digits at 1-8 threads, docs/worm/BODY_TESTS.md)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
EIGEN="${1:-}"
if [ -z "$EIGEN" ]; then
  for d in /opt/homebrew/include/eigen3 /usr/local/include/eigen3 /usr/include/eigen3; do
    [ -d "$d" ] && EIGEN="$d" && break
  done
fi
SRC=$(ls "$ROOT"/sim/*.cpp "$ROOT"/sim/util/*.cpp "$ROOT"/sim/util/json/*.cpp \
         "$ROOT"/sim/fem/*.cpp "$ROOT"/sim/fem/Constraint/*.cpp "$ROOT"/sim/fem/Mesh/*.cpp)
OBJ="$HERE/obj"; BIN="$HERE/run_body"; EXTRA=""
if [ "${OMP:-0}" = "1" ]; then OBJ="$HERE/obj_omp"; BIN="$HERE/run_body_omp"; EXTRA="-fopenmp"; fi
mkdir -p "$OBJ"
# Headers are not tracked per object: an object older than the newest sim/ header is rebuilt.
NEWEST_H=$(ls -t $(find "$ROOT/sim" -name '*.h') | head -1)
FLAGS="-O2 $EXTRA -std=gnu++14 -include cassert -include cmath -include limits -DHAVE_CSTDDEF -DNDEBUG -DSOFTCON_DIR=\"$ROOT\" -DOCTOCON_DIR=\"$ROOT\" -I$EIGEN -I$ROOT/sim -I$ROOT/sim/fem -w"
objs=""
for f in $SRC; do
  o="$OBJ/$(echo "${f#$ROOT/}" | tr '/' '_').o"
  if [ ! -f "$o" ] || [ "$f" -nt "$o" ] || [ "$NEWEST_H" -nt "$o" ]; then c++ $FLAGS -c "$f" -o "$o"; fi
  objs="$objs $o"
done
c++ $FLAGS "$HERE/run_body.cpp" $objs -o "$BIN"
echo "built $BIN (eigen $EIGEN)"
