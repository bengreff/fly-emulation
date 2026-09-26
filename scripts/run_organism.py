"""Run the whole-organism closed loop and write its inventory and provenance.

    uv run python scripts/run_organism.py --policy minimal --duration-ms 200

Policies (docs/archive/PLAN_sessions2-3.md step 6), reported together:

    strict        refuses to run; the requirements it refuses on are the result
    minimal       one declared default per subsystem
    conventional  what the published precedents assume

Every run writes a provenance record and the requirement inventory the model
actually reached for.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from flyemu import profiles
from flyemu.organism import Organism, StrictRefusal
from flyemu.provenance import RunRecord
from flyemu.registry import Policy, Unresolved

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "data" / "cache"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="minimal",
                    choices=[p.value for p in Policy])
    ap.add_argument("--duration-ms", type=float, default=200.0)
    ap.add_argument("--timestep-ms", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE,
                    help="parameter profile (default: the working model); 'none' for bare defaults")
    ap.add_argument("--min-synapses", type=int, default=profiles.WORKING_MIN_SYNAPSES)
    ap.add_argument("--tag", default="")
    ap.add_argument("--spike-cap", type=int, default=None,
                    help="abort if more than this many neurons spike in a step")
    ap.add_argument("--set", action="append", default=[], metavar="ENTITY|PROP=V",
                    help="override an assumed scalar, e.g. "
                         "'connection_class:all|efficacy_per_synapse=0.3'")
    args = ap.parse_args()
    overrides = {}
    for item in args.set:
        key, _, val = item.partition("=")
        overrides[key] = float(val)

    run_id = f"organism-{args.policy}-{args.duration_ms:g}ms-n{args.min_synapses}"
    if args.tag:
        run_id += f"-{args.tag}"
    out = REPO / "runs" / run_id
    rec = RunRecord(run_id, out, description="whole-organism closed loop, "
                                             f"policy={args.policy}")
    rec.add_config(vars(args))
    for name in ["male_cns_neurons.parquet", "male_cns_edges.parquet",
                 "male_cns_sensorimotor_roiinfo.parquet"]:
        p = CACHE / name
        if p.exists():
            rec.add_input(name, p, note="male-cns:v1.0 via neuPrint")
    rec.declare_scaffold(
        "background membrane noise substitutes for every input the CNS "
        "receives that is not modelled (vision, olfaction, taste, wind, "
        "gravity, audition, temperature, and all neuromodulation)"
    )
    rec.declare_scaffold(
        "body joint stiffness, damping and force limits are NeuroMechFly "
        "defaults, not measured fly mechanics"
    )

    try:
        org = Organism(
            timestep_ms=args.timestep_ms, policy=args.policy, seed=args.seed,
            min_synapses=args.min_synapses, overrides=overrides,
            profile=None if args.profile in ("none", "") else args.profile,
        )
    except Unresolved as exc:
        req = exc.requirement
        print(f"REFUSED at construction: {req.entity}.{req.property} "
              f"[{req.units}] needed by {req.model_use}")
        rec.result("refused_on", f"{req.entity}.{req.property}")
        rec.finish(status="refused")
        return 0

    print(f"body:    {org.body.summary()}")
    print(f"network: {org.conn.n:,} neurons, {org.conn.n_edges:,} edges, "
          f"{org.conn.weight_syn.sum():,.0f} synapses")
    print(f"motor:   {len(org.nm.mn_index):,} motor neurons mapped to "
          f"{len(set(org.nm.actuator_index.tolist()))} actuators; "
          f"{len(org.nm.unmapped):,} unmapped")
    print(f"sensory: {org.aff.rows.size:,} afferents wired")

    try:
        trace = org.run(args.duration_ms, spike_cap_per_step=args.spike_cap)
    except StrictRefusal as exc:
        print()
        print(f"REFUSED TO INTEGRATE under policy={args.policy}")
        print(f"  {exc}")
        print()
        rows = sorted(exc.refusals, key=lambda r: -r.instances)
        width = max(len(f"{r.entity}.{r.property}") for r in rows)
        print(f"  {'requirement':<{width}}  {'elements':>12}  needed by")
        for r in rows:
            print(f"  {r.entity + '.' + r.property:<{width}}  "
                  f"{r.instances:>12,}  {r.model_use}")
        inv_path = org.write_inventory(out / "inventory.csv")
        rec.result("refused_count", len(rows))
        rec.result("refused_elements", sum(r.instances for r in rows))
        rec.result("refused_requirements",
                   [f"{r.entity}.{r.property}" for r in rows])
        path = rec.finish(status="refused")
        print(f"\nrun record:  {path}")
        print(f"inventory:   {inv_path}")
        return 0

    trace.to_csv(out / "trace.csv", index=False)
    inv_path = org.write_inventory(out / "inventory.csv")
    rates = org.population_rates()
    rates.to_csv(out / "population_rates.csv")

    total_spikes = int(org.spike_counts.sum())
    mean_hz = total_spikes / org.conn.n / (org.duration_ms / 1000.0)
    displacement = float(
        np.hypot(trace.thorax_x.iloc[-1] - trace.thorax_x.iloc[0],
                 trace.thorax_y.iloc[-1] - trace.thorax_y.iloc[0])
    )
    summary = org.reg.summary()

    print()
    print(f"spikes:       {total_spikes:,} total, {mean_hz:.2f} Hz mean")
    print(f"active:       {(org.spike_counts > 0).mean() * 100:.1f}% of neurons")
    print(f"displacement: {displacement:.3f} mm in {org.duration_ms:g} ms")
    print(f"inventory:    {summary['rows']} requirement rows covering "
          f"{summary['model_elements']:,} model elements")
    for status, d in sorted(summary["by_status"].items()):
        print(f"  {status:<13} {d['rows']:>4} rows, "
              f"{int(d['instances']):>12,} elements")
    print()
    print(rates.round(3).to_string())

    rec.result("neurons", org.conn.n)
    rec.result("edges", org.conn.n_edges)
    rec.result("synapses", int(org.conn.weight_syn.sum()))
    rec.result("total_spikes", total_spikes)
    rec.result("mean_hz", round(mean_hz, 4))
    rec.result("frac_active", round(float((org.spike_counts > 0).mean()), 4))
    rec.result("displacement_mm", round(displacement, 4))
    rec.result("motor_neurons_mapped", int(len(org.nm.mn_index)))
    rec.result("motor_neurons_unmapped", int(len(org.nm.unmapped)))
    rec.result("afferents_wired", int(org.aff.rows.size))
    rec.result("inventory", summary)
    path = rec.finish()
    print(f"\nrun record:  {path}")
    print(f"inventory:   {inv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
