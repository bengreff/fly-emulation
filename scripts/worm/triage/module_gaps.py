"""Per mech module: its Spec ids that are active gaps/rules in params.catalog() (wtriage).
Usage: PYTHONPATH=src .venv/bin/python scripts/worm/triage/module_gaps.py MODULE [MODULE ...]"""
import importlib
import sys

from wormemu import params

cat = params.catalog().set_index("id")
for name in sys.argv[1:]:
    m = importlib.import_module(f"wormemu.mech.{name}")
    rows = []
    for s in getattr(m, "SPECS", []):
        if s.id in cat.index:
            r = cat.loc[s.id]
            rows.append(f"  {s.id} [{r.role}{'' if r.active else ' inactive:' + str(r.inactive_why)[:30]}] "
                        f"{r.label} t={r.template:g} [{r.lo:g}, {r.hi:g}] mech={s.mechanism}")
    print(name, len(rows))
    print("\n".join(rows))
