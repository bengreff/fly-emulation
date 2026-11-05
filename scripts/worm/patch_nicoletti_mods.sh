#!/bin/bash
# Local copy of the Nicoletti 2024 mods with per-segment Ca-channel-to-BK coupling (docs/worm/GAPCHECK.md,
# gapcheck2). The published files pass EGL-19's and UNC-2's gates to the coupled SLO channels through GLOBAL
# variables, one value for the whole model, so in a multi-segment cell every segment reads the last writer. Here
# the gates are RANGE variables and the SLO mechanisms read them through a POINTER that the caller sets per
# segment (h.setpointer(seg._ref_megl19_egl19, "megl19_egl19", seg.slo1egl19)). Nothing else changes.
# The same for the Ca pool (W1_RIM_AFD.md, Q3): caintra1's `calcium` becomes RANGE and kcnl reads it through a
# POINTER (h.setpointer(seg._ref_calcium_caintra1, "calcium_caintra1", seg.kcnl)).
# usage: patch_nicoletti_mods.sh <published moddir> <new moddir>
set -e
src=$1; dst=$2
mkdir -p "$dst"; cp "$src"/*.mod "$dst"/
python3 - "$dst" <<'PY'
import re, sys, os
d = sys.argv[1]
def edit(f, fn):
    p = os.path.join(d, f); s = open(p).read(); t = fn(s); assert t != s, f; open(p, "w").write(t)
for prod, m, hh in (("egl19", "megl19", "hegl19"), ("unc2", "munc2", "hunc2")):
    edit(f"{prod}.mod", lambda s: re.sub(rf"GLOBAL minf, hinf, mtau, htau, {m},\s*{hh}",
                                        f"GLOBAL minf, hinf, mtau, htau\n\tRANGE {m}, {hh}", s, count=1))
    for user in (f"slo1{prod}", f"slo2{prod}"):
        X, Y = f"{m}_{prod}", f"{hh}_{prod}"
        def fn(s, X=X, Y=Y):
            s = re.sub(rf"EXTERNAL\s+{X},\s*{Y}", f"POINTER {X}, {Y}", s, count=1)
            s = re.sub(rf"\n[ \t]*{X}[ \t]*\n[ \t]*{Y}[ \t]*\n", "\n", s, count=1)  # drop from PARAMETER
            return re.sub(r"ASSIGNED\s*\{", f"ASSIGNED{{\n\t\t {X}\n\t\t {Y}", s, count=1)
        edit(f"{user}.mod", fn)
edit("caintra1.mod", lambda s: re.sub(r"GLOBAL ca_eq,Fc,calcium", "GLOBAL ca_eq,Fc\n\tRANGE calcium", s, count=1))
def kc(s):
    s = re.sub(r"EXTERNAL calcium_caintra1", "POINTER calcium_caintra1", s, count=1)
    return re.sub(r"ASSIGNED\s*\{", "ASSIGNED{\n\t\t calcium_caintra1", s, count=1)
edit("kcnl.mod", kc)
print("patched", d)
PY
cd "$dst" && nrnivmodl > nrnivmodl.log 2>&1 && ls x86_64/libnrnmech.so
