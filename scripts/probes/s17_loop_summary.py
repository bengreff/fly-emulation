"""s17 closed-loop secondary readouts and the open-loop repro check (DECISIONS 21 Oct 03:18). Never a pass.

repro: the edited S2 harness without --proprio must equal the s16 run (rates, active MNs, every pool).
table: per run, the chordotonal afferent rate (the 78.4 Hz bound), CS, first-order targets, premotor and leg-MN
rates, joint-angle SD, and the neuromeres where I1 (IN16B036) spikes during drive.

    python scripts/probes/s17_loop_summary.py runs/s17/loop [--ref runs/s16/oa/s2/s2_M0_25mv.json] [--out x.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CHORDOTONAL = ("claw", "hook_flex", "hook_ext", "club")
BOUND_HZ = 78.4                 # top of larval lch5, Warren & Göpfert 2024 (F-REFLEX-2)


def repro(new: dict, ref: dict) -> dict:
    keys = ("rates_hz", "mns_active_drive", "mns_scored", "mns_rhythmic", "rhythmic_pools", "alternating_pools", "pools")
    diff = [k for k in keys if new.get(k) != ref.get(k)]
    return dict(match=not diff, differing=diff)


def row(r: dict) -> dict:
    lp = r.get("proprio") or {}
    af = lp.get("afferent_hz_per_cell", {})
    cho = [(v["n"], v["drive"]) for g, v in af.items() if g in CHORDOTONAL and v["n"]]
    cho_hz = round(sum(n * h for n, h in cho) / max(sum(n for n, _ in cho), 1), 2) if cho else None
    i1 = [c for c in r.get("core", []) if c["role"] == "I1"]
    return dict(chordotonal_drive_hz=cho_hz, chordotonal_max_subtype_hz=max((h for _, h in cho), default=None),
                inside_bound=None if cho_hz is None else cho_hz <= BOUND_HZ,
                cs_drive_hz=af.get("CS", {}).get("drive"), first_order=lp.get("first_order"),
                premotor_hz=[r["rates_hz"]["premotor_base"], r["rates_hz"]["premotor_drive"]],
                leg_mn_hz=[r["rates_hz"]["leg_mn_base"], r["rates_hz"]["leg_mn_drive"]],
                mns_active=r["mns_active_drive"], joint_sd_deg=r["joint_angle_sd_deg_max"],
                i1_spiking=sorted(c["neuromere"] for c in i1 if c["drive_hz"] > 0),
                i1_max_hz=max((c["drive_hz"] for c in i1), default=None))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--ref", default="runs/s16/oa/s2/s2_M0_25mv.json")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    s2 = Path(a.root) / "s2"
    out = {}
    o = s2 / "s2_M0open_25mv.json"
    if o.exists():
        out["repro_M0_25mv"] = repro(json.loads(o.read_text()), json.loads(Path(a.ref).read_text()))
        print("repro M0 25 mV vs s16:", out["repro_M0_25mv"])
    for f in sorted(s2.glob("s2_*mv.json")):
        k = f.stem[3:]
        out[k] = r = row(json.loads(f.read_text()))
        print(f"{k:16s} cho {r['chordotonal_drive_hz']!s:6s} CS {r['cs_drive_hz']!s:6s} "
              f"1st {None if not r['first_order'] else r['first_order']['n_active_drive']!s:4s} "
              f"pm {r['premotor_hz']} mn {r['leg_mn_hz']} act {r['mns_active']:3d} sd {r['joint_sd_deg']:5.2f} "
              f"I1 {','.join(r['i1_spiking']) or '-'} (max {r['i1_max_hz']})")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
