"""Score warm_start.py runs against the session-8 pre-registration (DECISIONS s8).

    uv run python scripts/probes/score_warm.py runs/s8_warm/batch_default.jsonl [...]
"""
import json
import sys
from collections import defaultdict


def cfg_name(r):
    return "T" if any("efficacy_scale" in k for k in r["set"]) else "default"


def main():
    rows = [json.loads(l) for f in sys.argv[1:] for l in open(f) if l.strip()]
    by = defaultdict(dict)
    for r in rows:
        if "runaway_at_ms" in r:
            print("RUNAWAY", r); continue
        mode = r["kick"] if r["senses"] == "on" else "control"
        by[(cfg_name(r), r["noise"], r["seed"])][mode] = r
    verdict = defaultdict(list)
    print(f"{'cfg':8}{'σ':>5}{'seed':>5} | {'EPGact':>7}{'vec':>6}{'err':>6} B1 | {'PENfull':>8} B2 | "
          f"{'last100':>8}{'ctrl':>7} Q | PENwarm KCwarm")
    for (cfg, sig, seed), m in sorted(by.items()):
        if not all(k in m for k in ("local", "full", "control")):
            print("incomplete", cfg, sig, seed, sorted(m)); continue
        lo, fu, co = m["local"], m["full"], m["control"]
        b1 = (0.15 <= lo["epg_active_frac"] <= 0.40 and lo["epg_vector_strength"] >= 0.5
              and lo["bump_error_deg"] <= 45)
        b2 = fu["post_hz"]["PEN"] < 50
        lim = 1.2 * co["last100_noncx_hz"] + 0.05
        q = all(x["last100_noncx_hz"] <= lim for x in (lo, fu))
        verdict[(cfg, sig)].append(b1 and b2 and q)
        f = lambda b: "✓" if b else "✗"  # noqa: E731
        print(f"{cfg:8}{sig:>5}{seed:>5} | {lo['epg_active_frac']:>7.2f}{lo['epg_vector_strength']:>6.2f}"
              f"{lo['bump_error_deg']:>6.0f} {f(b1)}  | {fu['post_hz']['PEN']:>8.1f} {f(b2)}  | "
              f"{max(lo['last100_noncx_hz'], fu['last100_noncx_hz']):>8.3f}{co['last100_noncx_hz']:>7.3f} {f(q)} | "
              f"{lo['warm_hz']['PEN']:>6.1f} {lo['warm_hz']['KC']:>6.2f}")
    print()
    for k, v in sorted(verdict.items()):
        print(k, f"{sum(v)}/{len(v)} seeds pass", "PASS" if len(v) == 3 and all(v) else "FAIL")


if __name__ == "__main__":
    main()
