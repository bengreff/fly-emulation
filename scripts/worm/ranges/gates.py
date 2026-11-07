"""Read the gate formulas of the worm channel mods, classify each constant by its place in them, and evaluate the
steady states and time constants over the voltage window (wranges, 7 Nov 2026).

The same name means different things in different mods (`etm` is a midpoint in egl19 and a slope in shk1), so a
constant's role comes from the formula, not its name:
  midpoint     X in (v - X), (v + X) or (X - v)
  slope        X in (... v ...) / X
  sensitivity  X in X * (... v ...)  (an exponential factor per mV)
  other        anything else (amplitudes, offsets, factors)

`gate_values(mod, params)` evaluates every assignment of the rate block for V on a grid (and Ca on a grid for the
slo mods), with the given parameter values, and returns each gate's inf and tau arrays. The joint constraint
`gate_window` (constraints.yaml) uses it: every inf in [0, 1] and every tau inside the tau_gate hard bounds.
CPU only; numpy.
"""
from __future__ import annotations

import ast
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DIRS = [ROOT / "third_party/baaiworm/mod", ROOT / "src/wormemu/nmodl/channels"]
V = np.linspace(-120.0, 60.0, 361)                  # mV; the slo mods switch branch at v = 60
CA_UM = np.geomspace(0.01, 100.0, 9)               # free Ca at the channel, uM
TAU_MIN, TAU_MAX = 0.01, 1.0e7                     # ms, the tau_gate hard bounds (rules.yaml)


def mod_path(mod: str) -> Path | None:
    for d in DIRS:
        p = d / f"{mod}.mod"
        if p.exists():
            return p
    return None


@lru_cache(None)
def parse(mod: str) -> tuple[dict, list[tuple[str, str]]]:
    """(PARAMETER name -> value, [(lhs, expression)] of the rate block in order)."""
    p = mod_path(mod)
    if p is None:
        return {}, []
    text = re.sub(r":.*", "", p.read_text().replace("\r", ""))
    par = {}
    m = re.search(r"PARAMETER\s*\{(.*?)\n\s*\}", text, re.S)
    for line in (m.group(1) if m else "").splitlines():
        q = re.match(r"\s*(\w+)\s*=\s*([-+0-9.eE]+)", line)
        if q:
            par[q.group(1)] = float(q.group(2))
    body = []
    for head in re.finditer(r"(?:PROCEDURE\s+(?:setparames|rates)|FUNCTION\s+\w+)\s*\(", text):
        i = text.index("{", head.end())
        depth, j = 0, i
        while j < len(text):                         # the block, matching nested braces
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            if depth == 0:
                break
            j += 1
        src = text[i + 1:j]
        src = re.sub(r"if\s*\(v\s*<\s*60\)\s*\{(.*?)\}\s*else\s*\{.*?\}", r"\1", src, flags=re.S)  # slo: v < 60
        for line in src.splitlines():
            q = re.match(r"\s*(\w+)\s*=\s*(.+?)\s*$", line)
            if q and not q.group(2).startswith("="):
                body.append((q.group(1), q.group(2)))
    return par, body


def _py(expr: str) -> str:
    return expr.replace("^", "**")


def _has_v(node) -> bool:
    return any(isinstance(n, ast.Name) and n.id == "v" for n in ast.walk(node))


def _linear_v(node) -> bool:
    """v, (v +- X), (X - v), or minus one of those."""
    node = node.operand if isinstance(node, ast.UnaryOp) else node
    if isinstance(node, ast.Name):
        return node.id == "v"
    return isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Sub, ast.Add)) and \
        any(isinstance(x, ast.Name) and x.id == "v" for x in (node.left, node.right))


@lru_cache(None)
def roles(mod: str) -> dict[str, str]:
    par, body = parse(mod)
    out: dict[str, set] = {}
    for lhs, e in body:
        if lhs == "cain":                            # the nanodomain line; overridden by the Ca grid
            continue
        try:
            tree = ast.parse(_py(e), mode="eval")
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if not isinstance(n, ast.BinOp):
                continue
            a, b = n.left, n.right
            if isinstance(n.op, (ast.Sub, ast.Add)):
                for x, y in ((a, b), (b, a)):
                    if isinstance(x, ast.Name) and x.id == "v" and isinstance(y, ast.Name) and y.id in par:
                        out.setdefault(y.id, set()).add("midpoint")
            elif isinstance(n.op, ast.Div) and isinstance(b, ast.Name) and b.id in par and _linear_v(a):
                out.setdefault(b.id, set()).add("slope")
            elif isinstance(n.op, ast.Mult):
                for x, y in ((a, b), (b, a)):
                    x = x.operand if isinstance(x, ast.UnaryOp) else x
                    if isinstance(x, ast.Name) and x.id in par and _linear_v(y):
                        out.setdefault(x.id, set()).add("sensitivity")
    return {k: (next(iter(v)) if len(v) == 1 else "mixed") for k, v in out.items()}


def role(pid: str) -> str | None:
    """Role of a kin_<mod>_<name> row's constant, or None if the row is not a mod constant."""
    m = re.match(r"kin_(.+)$", pid)
    if not m:
        return None
    rest = m.group(1)
    for mod in sorted({p.stem for d in DIRS for p in d.glob("*.mod")}, key=len, reverse=True):
        if rest.startswith(mod + "_"):
            return roles(mod).get(rest[len(mod) + 1:], "other")
    return None


NP = {"exp": np.exp, "sqrt": np.sqrt, "log": np.log, "pow": np.power, "fabs": np.abs}
CONST = {"FARADAY": 96485.33212, "cai_to_uM": 1000.0, "mcav": 1.0}


def gate_values(mod: str, overrides: dict | None = None) -> dict[str, np.ndarray]:
    """Every variable the rate block assigns, as an array over (Ca, V), using the mod's PARAMETERs updated by
    `overrides` (name -> value). Ca enters as `ca` (mM, the slo iso mods), `cai` (mM) and `cain` (uM, the BAAIWorm
    slo mods' nanodomain Ca, overridden to the grid rather than the nanodomain formula)."""
    par, body = parse(mod)
    env = {**NP, **CONST, **par, **(overrides or {})}
    v = V[None, :]
    ca_um = CA_UM[:, None]
    env.update(v=v, ca=ca_um / 1000.0, cai=ca_um / 1000.0)
    out = {}
    with np.errstate(all="ignore"):
        for lhs, e in body:
            if lhs == "cain":
                env[lhs] = ca_um * np.ones_like(v)
                continue
            try:
                val = eval(compile(_py(e), mod, "eval"), {"__builtins__": {}}, env)
            except Exception:                        # noqa: BLE001 - a line this reader does not handle
                continue
            env[lhs] = val
            out[lhs] = np.broadcast_to(np.asarray(val, dtype=float), (len(CA_UM), len(V)))
    return out


def is_inf(name: str) -> bool:
    return name.endswith("inf") and name not in ("ahinf", "bhinf", "chinf", "dhinf")


def is_tau(name: str) -> bool:
    return re.fullmatch(r"(t[a-z]{1,4}|[a-z]tau|mtau|htau|stau|tmcav|thcav)", name) is not None


def check(mod: str, overrides: dict | None = None) -> list[str]:
    """Problems of one mod at these values: inf outside [0, 1], tau outside [TAU_MIN, TAU_MAX] ms, non-finite."""
    bad = []
    for k, a in gate_values(mod, overrides).items():
        if not (is_inf(k) or is_tau(k)):
            continue
        if not np.isfinite(a).all():
            bad.append(f"{mod}.{k} not finite")
            continue
        if is_inf(k) and (a.min() < -1e-9 or a.max() > 1 + 1e-9):
            bad.append(f"{mod}.{k} in [{a.min():.3g}, {a.max():.3g}], outside [0, 1]")
        if is_tau(k) and (a.min() < TAU_MIN or a.max() > TAU_MAX):
            bad.append(f"{mod}.{k} in [{a.min():.3g}, {a.max():.3g}] ms, outside [{TAU_MIN:g}, {TAU_MAX:g}]")
    return bad


def mods_with_gates() -> list[str]:
    return sorted(p.stem for d in DIRS for p in d.glob("*.mod") if parse(p.stem)[1])


if __name__ == "__main__":
    for mod in mods_with_gates():
        r = roles(mod)
        print(mod, {k: v for k, v in sorted(r.items())})
        g = gate_values(mod)
        print("   gates:", [k for k in g if is_inf(k) or is_tau(k)], "published values:", check(mod) or "ok")
