"""Joint constraints on the worm's numbers: relations between rows that per-row bounds cannot express (wranges,
7 Nov 2026). `constraints(led)` lists them from the current ledger; the build writes them to
data/worm/model/constraints.yaml; `check(values, led)` returns every violation for one worm's numbers (the
WormSpec.values of wormemu.brain.sample_worm: param_id -> float, or a Series by element).

Kinds (the `kind` field; the `check` field of each constraint says the same in words):
  between      lo < x < hi for every x (elementwise for per-element rows; lo and hi may be a max / min of rows)
  less         a < b
  sum_le       sum of weight_i x_i <= limit, per element (per cell) where the rows are per cell
  pool_volume  a pool volume <= the whole volume of every cell it is applied to (cell_sizes.csv, derived)
  passive_rin  1 / (sum g_pas x area) >= the lowest measured input resistance, per cell (a necessary condition:
               active channels only lower the input resistance); the upper end needs a simulated step (method given)
  gate_window  every steady state of a channel mod in [0, 1] and every time constant in the tau_gate hard bounds,
               over V in [-120, 60] mV and free Ca in [0.01, 100] uM (scripts/worm/ranges/gates.py)
  vhalf_order  the half point of the inactivation steady state below that of activation, where the worm fits order them

`python scripts/worm/ranges/joint.py` checks the template worm and prints the violations (the template should pass;
any that do not are listed in the night file).
"""
from __future__ import annotations

import math
import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cellsize  # noqa: E402
import gates  # noqa: E402
import hard  # noqa: E402

PACKING = hard.RULES["packing_per_um2"]                    # channels per um2 (HARD_BOUNDS_LIT section 1)
GHK = ("Goldman-Hodgkin-Katz: a current through channels permeable to several ions reverses between the most "
       "negative and the most positive reversal of the ions it carries (Hille 2001, Ion Channels of Excitable "
       "Membranes, 3rd ed., ch. 14)")
KCC = ("Cl- is extruded by K-Cl cotransport (KCC-2 in C. elegans neurons, Tanis et al. 2009 J Neurosci 29:9943), "
       "which cannot push E_Cl below E_K (Payne et al. 2003 Trends Neurosci 26:199); no primary-active Cl pump is "
       "known in C. elegans neurons")


def _template_values(led) -> dict:
    vals = {}
    for r in led.parameters.itertuples():
        t = led.values(r.param_id)
        if t is None:
            vals[r.param_id] = float(r.value_template) if not pd.isna(r.value_template) else np.nan
        else:
            vals[r.param_id] = pd.Series(pd.to_numeric(t.value, errors="coerce").to_numpy(float),
                                         index=t.element.to_numpy())
    return vals


@lru_cache(None)
def _kin_map(ids: frozenset) -> dict:
    """mod -> {PARAMETER name: param_id} for the kin_<mod>_<name> rows."""
    mods = sorted({p.stem for d in gates.DIRS for p in d.glob("*.mod")}, key=len, reverse=True)
    out: dict = {}
    for pid in ids:
        if not pid.startswith("kin_"):
            continue
        rest = pid[4:]
        for mod in mods:
            if rest.startswith(mod + "_") and rest[len(mod) + 1:] in gates.parse(mod)[0]:
                out.setdefault(mod, {})[rest[len(mod) + 1:]] = pid
                break
    return out


def _vhalf(a: np.ndarray) -> float:
    a = a[len(gates.CA_UM) // 2]
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-6:
        return np.nan
    s = np.sign(a - (lo + hi) / 2)
    i = np.flatnonzero(np.diff(s) != 0)
    return float(gates.V[i[0]]) if len(i) == 1 else np.nan


INACT = {"hinf", "hfinf", "hsinf", "sinf", "hcavinf"}         # inactivation-type steady states (decreasing in V)
ACT = {"minf", "mcavinf"}


def constraints(led) -> list[dict]:
    p = led.parameters
    ids = set(p.param_id)
    has = lambda *xs: all(x in ids for x in xs)  # noqa: E731
    out = []

    def add(**c):
        out.append(c)

    # 1. reversal order (physics)
    leak = [x for x in ("pas_soma_epas", "pas_neurite_epas", "mpas_epas", "glia_e_leak_mV", "other_e_leak_mV",
                        "sens_glia_e_leak_mV", "endo_e_leak_mV") if x in ids]
    add(id="reversal_leak_between_EK_ENa", kind="between", lo=["ion_ek"], hi=["ion_ena"], x=leak,
        statement="E_K < E_leak < E_Na in every neuron, muscle, glia and other cell", strength="hard", basis="physics",
        source=GHK + "; the leak is K, Na and Cl (NCA, TWK, Cl leak), and E_Cl lies between E_K and E_Na",
        check="elementwise: max(lo) < x < min(hi) for every element of every x row")
    cation = [x for x in p.param_id[p.hard_class == "reversal_cation"]
              if not re.search(r"(_ca_|eca|vCa|VGCC|_boyle_)", x) and not x.startswith(("c302_", "bwm_du_", "awa_liu"))]
    add(id="reversal_cation_between_EK_ENa", kind="between", lo=["ion_ek"], hi=["ion_ena"], x=cation,
        statement="every non-selective cation channel (ACh, Glu, GABA-cation receptors, CNG, TRPV, MEC, opsin) "
                  "reverses between E_K and E_Na", strength="hard", basis="physics", source=GHK,
        check="max(lo) < x < min(hi)")
    chloride = [x for x in p.param_id[p.hard_class.isin(["reversal_Cl", "reversal_inhibitory"])]]
    add(id="reversal_Cl_above_EK", kind="between", lo=["ion_ek"], hi=["ion_ena"], x=chloride,
        statement="E_K <= E_Cl < E_Na for every Cl channel and the inhibitory synapse", strength="hard",
        basis="physics", source=KCC, check="max(lo) <= x < min(hi)", inclusive_lo=True)
    for name, k, l, h in (("c302_muscle", ["c302_muscle_k_slow_erev", "c302_muscle_k_fast_erev"],
                           "c302_muscle_leak_erev", "c302_muscle_ca_boyle_erev"),
                          ("bwm_du", ["bwm_du_ek_mV"], "bwm_du_el_mV", "bwm_du_ena_mV"),
                          ("ph_sh", ["ph_sh_v_k"], "ph_sh_v_l", "ph_sh_v_na"),
                          ("awa_liu", ["awa_liu_vK"], "awa_liu_vL", "awa_liu_vCa")):
        if has(*k, l, h):
            add(id=f"reversal_order_{name}", kind="between", lo=k, hi=[h], x=[l],
                statement=f"{name}: E_K < E_leak < E_{'Ca' if 'ca' in h.lower() else 'Na'} within its own model",
                strength="hard", basis="physics", source=GHK, check="max(lo) < x < min(hi)")

    # 2. time-constant order (definition: the rise is the faster of the two)
    pairs = [(a, a.replace("_tau_rise_ms", "_tau_off_ms")) for a in sorted(ids) if a.endswith("_tau_rise_ms")]
    pairs = [(a, b if b in ids else a.replace("_tau_rise_ms", "_tau_decay_ms")) for a, b in pairs]
    for a, b in pairs:
        if b in ids:
            add(id=f"tau_rise_lt_decay_{a.replace('_tau_rise_ms', '')}", kind="less", a=a, b=b,
                statement=f"{a} < {b}", strength="hard", basis="physics",
                source="a double-exponential's rise is by definition its faster time constant; swapping them "
                       "describes the same curve with the labels exchanged (Roth and van Rossum 2009, in "
                       "Computational Modeling Methods for Neuroscientists, ch. 6)", check="a < b")

    # 3. channel packing (physics)
    fam = hard.RULES["families"]
    cell_rows = [x for x in p.param_id[(p.hard_class == "conductance_density") & (p.grain == "cell")]]
    w = {x: 1000.0 / fam[hard.family(x)] for x in cell_rows}            # nS/um2 -> channels/um2
    add(id="channel_packing_per_cell", kind="sum_le", x=cell_rows, weight=w, limit=PACKING,
        statement="channels per um2 summed over every channel of a cell (g / unitary g) <= the packing limit",
        strength="hard", basis="physics",
        source=f"{PACKING:g} channels per um2 (HARD_BOUNDS_LIT section 1: the densest measured, Na channels at nodes "
               f"of Ranvier; the closest packing of channel footprints); unitary g by family {fam}",
        check="per element (cell): sum_i weight_i x_i <= limit; weight = 1000 / gamma_pS for nS/um2")
    cls_rows = p[(p.hard_class == "conductance_density") & (p.grain == "class") & p.param_id.str.startswith("dens_")]
    by_cls: dict = {}
    for x in cls_rows.param_id:
        by_cls.setdefault(x.rsplit("_", 1)[1], []).append(x)
    for c, xs in sorted(by_cls.items()):
        if len(xs) > 1:
            add(id=f"channel_packing_class_{c}", kind="sum_le", x=xs,
                weight={x: 1e4 / fam[hard.family(x)] for x in xs}, limit=PACKING,
                statement=f"class {c}: channels per um2 over its channel-library densities <= the packing limit",
                strength="hard", basis="physics", source="as channel_packing_per_cell",
                check="sum_i weight_i x_i <= limit; weight = 1e4 / gamma_pS for S/cm2")

    # 4. Ca pool volume (geometry)
    sz = cellsize.load()
    neurons = [e for e in (led.values("pas_soma_epas").element if led.values("pas_soma_epas") is not None else [])]
    vols = sz.loc[[n for n in neurons if n in sz.index], "volume_um3"]
    if "capool_vcell" in ids and len(vols):
        add(id="ca_pool_volume_le_cell", kind="pool_volume", x="capool_vcell", limit=float(vols.min()),
            smallest=str(vols.idxmin()), when={"ca_pool_volume": ["fixed", "off"]},
            applies_when="toggle ca_pool_volume = fixed or off (one capool_vcell for every neuron)",
            statement="the one Ca pool volume <= the whole volume of the smallest neuron it is applied to",
            strength="hard", basis="physics",
            source="cell volumes from the BAAIWorm hoc 3D points (scripts/worm/ranges/cell_sizes.csv, derived; area "
                   "matches NEURON's to 0.01%)", check="x <= limit")
    for pid, part in (("pump_vol_neuron_um3", vols),):
        if pid in ids and len(part):
            add(id=f"{pid}_inside_cells", kind="between", lo_value=float(part.min()), hi_value=float(part.max()),
                x=[pid], statement=f"{pid} (a typical neuron's volume) between the smallest and largest neuron volume",
                strength="hard", basis="physics", source="cell_sizes.csv (derived)", check="lo <= x <= hi",
                inclusive_lo=True)

    # 5. passive input resistance (necessary condition), measured range
    if has("pas_soma_gpas", "pas_neurite_gpas"):
        add(id="passive_rin_neurons", kind="passive_rin", soma="pas_soma_gpas", neurite="pas_neurite_gpas",
            min_gohm=0.2, max_gohm=5.0,
            statement="each neuron's passive input resistance 1 / (g_pas,soma A_soma + g_pas,neurite A_neurite) >= "
                      "0.2 GOhm; its simulated input resistance at rest in [0.2, 5] GOhm",
            strength="prior", basis="measured_spread",
            source="docs/worm/research/param_ranges.csv A3 (Goodman et al. 1998 J Neurosci 18:2729; Mellem et al. "
                   "2008 Neuron; inferred, low confidence); areas from cell_sizes.csv",
            check="static: per neuron 1e8 / (gs As + gn An) / 1e9 >= min_gohm (g in S/cm2, A in um2); simulated: "
                  "at rest, a -1 pA step for 300 ms, R_in = dV / dI in [min_gohm, max_gohm]")

    # 6. gate windows and half-point order, per channel mod
    km = _kin_map(frozenset(ids))
    for mod in sorted(km):
        add(id=f"gate_window_{mod}", kind="gate_window", mod=mod, params=km[mod],
            statement=f"{mod}: every steady state in [0, 1] and every time constant in [{gates.TAU_MIN:g}, "
                      f"{gates.TAU_MAX:g}] ms over V -120..60 mV and Ca 0.01..100 uM", strength="hard",
            basis="physics", source="a gate is a probability; tau_gate hard bounds (rules.yaml); the mod's own "
                                    "formulas (gates.py)", check="gates.check(mod, {name: value}) == []")
        g = gates.gate_values(mod)
        act = [k for k in g if k in ACT]
        ina = [k for k in g if k in INACT]
        if act and ina:
            vm, vh = _vhalf(g[act[0]]), _vhalf(g[ina[0]])
            if not np.isnan(vm) and not np.isnan(vh) and vh < vm:
                add(id=f"vhalf_order_{mod}", kind="vhalf_order", mod=mod, params=km[mod], act=act[0], inact=ina[0],
                    statement=f"{mod}: V1/2 of {ina[0]} below V1/2 of {act[0]} (published {vh:g} < {vm:g} mV)",
                    strength="hard", basis="measured_spread",
                    source="the order of the worm channel's own fit (BAAIWorm, from Nicoletti 2019 / Liu 2018 data); "
                           "inactivation half points lie below activation for transient channels (Hille 2001 ch. 3)",
                    check="half points from gates.gate_values at the middle Ca: V1/2(inact) < V1/2(act)")
    # 7. the closed-form sums behind some gate windows (a fitter can use these linear forms directly)
    for mod, sums in (("kqt3", [("aw", "bw"), ("as", "bs")]), ("kqt1", [("s1", "s4")])):
        for a, b in sums:
            if mod in km and a in km[mod] and b in km[mod]:
                add(id=f"gate_sum_{mod}_{a}_{b}", kind="sum_le", x=[km[mod][a], km[mod][b]],
                    weight={km[mod][a]: 1.0, km[mod][b]: 1.0}, limit=1.0,
                    statement=f"{mod}: {a} + {b} <= 1 (the gate's steady state reaches {a} + {b})", strength="hard",
                    basis="physics", source="a gate is a probability (the mod formula)", check="x_a + x_b <= 1")
    for c in out:
        c.setdefault("applies_when", "always")
    return out


def _arr(values, pid):
    x = values.get(pid)
    if x is None:
        return None
    return x if isinstance(x, pd.Series) else pd.Series([float(x)])


def check(values: dict, led, cons: list[dict] | None = None, toggles: dict | None = None) -> list[str]:
    """Every violation of the constraints by these numbers (an empty list = the worm is allowed). A constraint with
    a `when` (toggle -> forms) is checked only when the toggles (default: the ledger's defaults) select one of them."""
    cons = cons if cons is not None else constraints(led)
    if toggles is None:
        m = led.mechanisms
        toggles = {r.toggle: r.default for r in m.itertuples() if isinstance(r.toggle, str) and r.toggle}
    bad = []
    sz = cellsize.load()
    for c in cons:
        if any(toggles.get(t) not in forms for t, forms in c.get("when", {}).items()):
            continue
        k = c["kind"]
        if k == "between":
            lo = max([float(_arr(values, x).max()) for x in c.get("lo", []) if _arr(values, x) is not None] +
                     ([c["lo_value"]] if "lo_value" in c else []), default=-np.inf)
            hi = min([float(_arr(values, x).min()) for x in c.get("hi", []) if _arr(values, x) is not None] +
                     ([c["hi_value"]] if "hi_value" in c else []), default=np.inf)
            for x in c["x"]:
                a = _arr(values, x)
                if a is None:
                    continue
                a = a.dropna()
                low = (a < lo) if c.get("inclusive_lo") else (a <= lo)
                if low.any() or (a >= hi).any():
                    bad.append(f"{c['id']}: {x} in [{a.min():g}, {a.max():g}] not inside ({lo:g}, {hi:g})")
        elif k == "less":
            a, b = _arr(values, c["a"]), _arr(values, c["b"])
            if a is not None and b is not None and not float(a.max()) < float(b.min()):
                bad.append(f"{c['id']}: {c['a']} {float(a.max()):g} >= {c['b']} {float(b.min()):g}")
        elif k == "sum_le":
            tot = None
            for x in c["x"]:
                a = _arr(values, x)
                if a is None:
                    continue
                term = a * c["weight"][x]
                tot = term if tot is None else (tot.add(term, fill_value=0) if isinstance(term, pd.Series) and
                                                len(term) > 1 else tot + float(term.iloc[0]))
            if tot is not None and (tot > c["limit"] * (1 + 1e-9)).any():
                bad.append(f"{c['id']}: sum up to {float(tot.max()):g} > {c['limit']:g}"
                           + (f" (element {tot.idxmax()})" if len(tot) > 1 else ""))
        elif k == "pool_volume":
            a = _arr(values, c["x"])
            if a is not None and float(a.max()) > c["limit"]:
                bad.append(f"{c['id']}: {c['x']} {float(a.max()):g} um3 > {c['limit']:g} um3 ({c['smallest']}; "
                           f"applies when {c['applies_when']})")
        elif k == "passive_rin":
            gs, gn = _arr(values, c["soma"]), _arr(values, c["neurite"])
            j = sz.reindex(gs.index)
            g = gs * j.soma_area_um2 * 1e-8 + gn.reindex(gs.index) * j.neurite_area_um2 * 1e-8
            rin = 1.0 / g / 1e9
            low = rin[rin < c["min_gohm"]]
            if len(low):
                bad.append(f"{c['id']}: {len(low)} neurons below {c['min_gohm']} GOhm passive (lowest {low.idxmin()} "
                           f"{low.min():.3g} GOhm)")
        elif k in ("gate_window", "vhalf_order"):
            ov = {name: float(_arr(values, pid).iloc[0]) for name, pid in c["params"].items()
                  if _arr(values, pid) is not None}
            if k == "gate_window":
                bad += [f"{c['id']}: {b}" for b in gates.check(c["mod"], ov)]
            else:
                g = gates.gate_values(c["mod"], ov)
                vm, vh = _vhalf(g[c["act"]]), _vhalf(g[c["inact"]])
                if not (vh < vm):
                    bad.append(f"{c['id']}: V1/2 {c['inact']} {vh:g} >= {c['act']} {vm:g} mV")
    return bad


class Mem:
    """The build's rows and value tables as a ledger, for constraints() before anything is written."""

    def __init__(self, rows, values, mechs):
        self.parameters = pd.DataFrame(rows)
        self._v = values
        self.mechanisms = pd.DataFrame(mechs)
        for col in ("toggle", "neutral", "source", "notes", "absent_reason"):
            if col not in self.mechanisms:
                self.mechanisms[col] = None

    def values(self, pid):
        return self._v.get(pid)


UNKNOWN = ("guessed", "absent")


def _known(r, values) -> np.ndarray:
    """A row's known numbers: its measured / published / derived / inferred elements, or its template when the
    whole row is known."""
    t = values.get(r["param_id"])
    if t is not None and "label" in t:
        return pd.to_numeric(t.value[~t.label.isin(UNKNOWN)], errors="coerce").dropna().to_numpy(float)
    v = hard._num(r.get("value_template"))
    return np.array([] if r.get("label") in UNKNOWN or np.isnan(v) else [v])


def _has_unknown(r, values) -> bool:
    t = values.get(r["param_id"])
    if t is not None and "label" in t:
        return bool(t.label.isin(UNKNOWN).any())
    return r.get("label") in UNKNOWN


def narrow(rows: list[dict], values: dict, mechs: list[dict], passes: int = 3) -> list[dict]:
    """Narrow the box (bio_min, bio_max) of every row with unknown numbers where a hard constraint that always
    applies sets it against KNOWN numbers (a known leak reversal of -75 mV caps E_K at -75; a known rise time floors
    the decay). Kinds between and less; a box only shrinks; every move is written into bound_basis_detail and
    returned. The template must stay inside (it obeys the constraints, checked after the build)."""
    by = {r["param_id"]: r for r in rows}
    cons = [c for c in constraints(Mem(rows, values, mechs)) if c["strength"] == "hard" and c["applies_when"] ==
            "always" and c["kind"] in ("between", "less")]
    kn = {pid: _known(r, values) for pid, r in by.items()}
    ext = lambda ids, f: [float(f(kn[i])) for i in ids if i in kn and len(kn[i])]  # noqa: E731
    moves = []

    def move(pid, lo=None, hi=None, why=""):
        r = by[pid]
        if not _has_unknown(r, values):
            return
        olo, ohi = hard._num(r["bio_min"]), hard._num(r["bio_max"])
        nlo = max(olo, lo) if lo is not None and not np.isnan(olo) else olo
        nhi = min(ohi, hi) if hi is not None and not np.isnan(ohi) else ohi
        if nlo == olo and nhi == ohi:
            return
        assert nlo <= nhi, f"{pid}: constraints leave no room ({nlo}, {nhi}) ({why})"
        r["bio_min"], r["bio_max"] = nlo, nhi
        if not pd.isna(r.get("span_decades")) and nlo > 0:
            r["span_decades"] = round(math.log10(nhi / nlo), 3)
        r["bound_basis_detail"] = (str(r.get("bound_basis_detail") or "") +
                                   f"; narrowed [{olo:g}, {ohi:g}] -> [{nlo:g}, {nhi:g}] by {why}").strip("; ")
        moves.append(dict(param_id=pid, old_min=olo, old_max=ohi, new_min=nlo, new_max=nhi, by=why))

    for _ in range(passes):
        for c in cons:
            if c["kind"] == "between":
                kl = max(ext(c.get("lo", []), np.max) + ([c["lo_value"]] if "lo_value" in c else []), default=None)
                kh = min(ext(c.get("hi", []), np.min) + ([c["hi_value"]] if "hi_value" in c else []), default=None)
                kx_lo, kx_hi = min(ext(c["x"], np.min), default=None), max(ext(c["x"], np.max), default=None)
                for L in c.get("lo", []):
                    if L in by:
                        cap = min([v for v in (kx_lo, kh) if v is not None], default=None)
                        move(L, hi=cap, why=f"{c['id']} (below the lowest known x {kx_lo} and known hi {kh})")
                for H in c.get("hi", []):
                    if H in by:
                        flo = max([v for v in (kx_hi, kl) if v is not None], default=None)
                        move(H, lo=flo, why=f"{c['id']} (above the highest known x {kx_hi} and known lo {kl})")
                for X in c["x"]:
                    if X in by:
                        move(X, lo=kl, hi=kh, why=f"{c['id']} (between the known lo {kl} and hi {kh})")
            else:
                a, b = c["a"], c["b"]
                if a in by and len(kn.get(b, [])):
                    move(a, hi=float(kn[b].min()), why=f"{c['id']} ({b} known {kn[b].min():g})")
                if b in by and len(kn.get(a, [])):
                    move(b, lo=float(kn[a].max()), why=f"{c['id']} ({a} known {kn[a].max():g})")
    return moves


def to_yaml(cons: list[dict]) -> str:
    import yaml
    head = dict(
        generated_by="scripts/worm/build_ledger.py via scripts/worm/ranges/joint.py (wranges, 7 Nov 2026)",
        how_to_check="from joint import check; check(spec.values, led) -> [] when every constraint holds "
                     "(spec = wormemu.brain.sample_worm(seed); run with scripts/worm/ranges on sys.path)",
        strengths="hard: physics or definition, a fitter must never leave it; prior: a measured range, a fitter "
                  "pays to leave it",
        n_constraints=len(cons))
    return yaml.safe_dump(dict(**head, constraints=cons), sort_keys=False, width=200, allow_unicode=True)


if __name__ == "__main__":
    from bioemu import ledger
    root = HERE.parents[2] / "data/worm/model"
    led = ledger.load(root)
    cons = constraints(led)
    from collections import Counter
    print(len(cons), "constraints:", dict(Counter(c["kind"] for c in cons)))
    vals = _template_values(led)
    bad = check(vals, led, cons)
    print(f"template worm, default toggles: {len(bad)} violations")
    for b in bad:
        print("  ", b)
    bad = check(vals, led, cons, toggles={"ca_pool_volume": "fixed"})
    print(f"template worm, ca_pool_volume fixed: {len(bad)} violations")
    for b in bad:
        print("  ", b)
    # the checker must catch a broken worm
    broken = dict(vals, ion_ek=0.0, kin_kqt3_aw=0.9, rec_lacr_tau_rise_ms=10.0, pas_soma_gpas=vals["pas_soma_gpas"] * 1e3)
    bad = check(broken, led, cons)
    print(f"broken worm (E_K 0, kqt3 aw 0.9, lacr rise 10 ms, soma g_pas x1000): {len(bad)} violations")
    for b in bad[:12]:
        print("  ", b)
