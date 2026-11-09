"""Which RATE_MODS reach the build with a tadj (wbody2, 9 Nov 2026): brain._neuron patches temperature's rate factor
into BAAIWorm's mods only, so the own mods listed in temperature.RATE_MODS (Nicoletti's channels, AWA's Liu mod,
du_bwm, wsyn) may load without one, and temperature.Mech skips a missing tadj silently. Prints, for each RATE_MODS
stem, its suffix and whether h has tadj_<suffix>. -> runs/worm/wbody2/tadj_reach.json"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu import brain as B  # noqa: E402
from wormemu.mech import temperature as T  # noqa: E402

h = B._neuron()
mods = sorted((B.BAAI / "mod").glob("*.mod")) + sorted((B.C302 / "mod").glob("*.mod")) + sorted(B.OWN_MODS.rglob("*.mod"))
stems = {m.stem: m for m in mods}
res = {}
for stem, (cls, _) in T.RATE_MODS.items():
    m = stems[stem]
    sfx = T.mod_suffix(m.read_text())
    res[stem] = dict(cls=cls, suffix=sfx, own=m.parent != B.BAAI / "mod", has_tadj=hasattr(h, f"tadj_{sfx}"))
out = ROOT / "runs/worm/wbody2/tadj_reach.json"
out.write_text(json.dumps(res, indent=1))
for k, v in res.items():
    print(f"{k:28s} {v['cls']:8s} own={v['own']!s:5s} tadj={v['has_tadj']}")
