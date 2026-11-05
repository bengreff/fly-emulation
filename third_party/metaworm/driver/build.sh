#!/bin/bash
# Build the headless MetaWorm body driver. Needs only a C++14 compiler and Eigen 3 (header-only); the upstream
# CMake also asked for Boost.Python, PythonLibs and OpenMP, but sim/ uses none of them (no omp pragmas, no Boost
# includes), so they are left out. Upstream used -std=gnu++11; Eigen 3.5 needs C++14.
# Usage: driver/build.sh [eigen_include_dir]   -> driver/run_body
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
OBJ="$HERE/obj"
mkdir -p "$OBJ"
FLAGS="-O2 -std=gnu++14 -include cassert -include cmath -include limits -DHAVE_CSTDDEF -DNDEBUG -DSOFTCON_DIR=\"$ROOT\" -DOCTOCON_DIR=\"$ROOT\" -I$EIGEN -I$ROOT/sim -I$ROOT/sim/fem -w"
objs=""
for f in $SRC; do
  o="$OBJ/$(echo "${f#$ROOT/}" | tr '/' '_').o"
  if [ ! -f "$o" ] || [ "$f" -nt "$o" ]; then c++ $FLAGS -c "$f" -o "$o"; fi
  objs="$objs $o"
done
c++ $FLAGS "$HERE/run_body.cpp" $objs -o "$HERE/run_body"
echo "built $HERE/run_body (eigen $EIGEN)"
