"""Contact sheet for the bypass assay frames (s13): one row per run (frames_<pattern>_<level>.npy, each frame two
views side by side), one column per frame time, labelled with the run's thorax height and verdict from the JSON.

    uv run python scripts/probes/bypass_sheet.py runs/s13/bypass/s1/support runs/s13/bypass/s1/coact --out docs/media/s13_bypass_s1.png
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames-ms", default="0,250,1000,3000", help="labels for the frame columns")
    ap.add_argument("--scale", type=float, default=0.5)
    a = ap.parse_args()
    cols = a.frames_ms.split(",")
    rows = []
    many = len({Path(x).resolve().parent for x in a.dirs}) > 1
    for d in map(Path, a.dirs):
        tag = f"{d.parent.name} " if many else ""
        js = {}
        for f in d.glob("*.json"):
            j = json.loads(f.read_text())
            for r in j.get("runs", []):
                js[(r["pattern"], f"{r['level']:g}")] = r
            if "drive_mv" in j:   # S2/S3: one run per file, keyed by its tag (s2_<tag>.json, frames_<tag>.npy)
                js[tuple(f.stem[3:].rsplit("_", 1))] = j
        num = lambda x: float(re.sub(r"[^0-9.]", "", x) or 0)
        for f in sorted((x for x in d.glob("frames_*.npy") if x.stem.count("_") == 2), key=lambda p: (p.stem.split("_")[1], num(p.stem.split("_")[2]))):
            _, pat, lv = f.stem.split("_", 2)
            r = js.get((pat, lv), {})
            if "drive_mv" in r:
                rz = r["rates_hz"]
                lab = (f"{pat} {lv} (forced drive)  DN {rz['stim_drive']} Hz  premotor {rz['premotor_drive']} Hz  "
                       f"leg MN {rz['leg_mn_drive']} Hz  act max {r['activation_drive_max']}  "
                       f"{'PASS' if r['passes'] else 'fails'}")
            else:
                ok = r.get("holds_prereg", r.get("holds"))
                lab = (f"{tag}{pat} a={lv}  z {r.get('z_place', '?')}->{r.get('z_final', '?')} mm  "
                       f"legF/W {r.get('leg_floor_force_over_weight_last1s', '?')}  "
                       f"trunk {r.get('trunk_touch_frac', '?')}  pitch {r.get('pitch_change_deg', {}).get('max_abs', '?')}  "
                       f"{'HOLDS' if ok else 'fails'}")
            rows.append((lab, np.load(f)))
    if not rows:
        raise SystemExit("no frames found")
    h, w = rows[0][1].shape[1:3]
    sh, sw = int(h * a.scale), int(w * a.scale)
    top, lab_h = 18, 16
    sheet = Image.new("RGB", (sw * len(cols), top + len(rows) * (sh + lab_h)), "white")
    dr = ImageDraw.Draw(sheet)
    for j, c in enumerate(cols):
        dr.text((j * sw + 4, 2), f"t = {c} ms", fill="black")
    for i, (lab, fr) in enumerate(rows):
        y = top + i * (sh + lab_h)
        dr.text((4, y + 1), lab, fill="black")
        for j in range(min(len(cols), len(fr))):
            sheet.paste(Image.fromarray(fr[j]).resize((sw, sh)), (j * sw, y + lab_h))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
