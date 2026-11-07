"""Hidden constants: numeric literals in the worm's model code that are not read from the ledger.

Scans src/wormemu/mech/*.py, brain.py, brain_layers.py, the body driver (src/wormemu/body/*.py and
third_party/metaworm/driver/run_body.cpp) and, beyond that list, the NMODL files the brain compiles
(src/wormemu/nmodl/*.mod). Writes data/worm/catalog/hidden_constants.json (file:line list); the ledger build reads
its summary into the catalog.

What counts. Python (AST): every int or float literal except
  - literals that feed a Spec (inside a Spec(...) call, or inside a module-level name the SPECS expression reads,
    followed one level down): those are in the ledger already;
  - literals inside a scene Param(...) (body/scene.py): each carries value, unit, label, range and source, and the
    catalog lists them as rows scene_*;
  - 0, 1, -1 (and 0.0, 1.0): arithmetic, not parameters;
  - subscripts and slices (indexing).
C++ and NMODL (regex, comments and strings removed): every numeric literal except 0 and 1; NMODL PARAMETER
defaults are skipped when the Python side sets the same variable from a Spec (brain.py setattr), and listed
otherwise.

Each literal gets a kind: shape or count (an argument of zeros, linspace, range, reshape and the like), unit
conversion (a power of ten, 60, 3600, 6e4 or 3.6e6 that multiplies or divides), numerical guard (|x| < 1e-6 or
>= 1e9, or the name says eps / tol / clip / max), small integer (2 or 3), function default, named constant
(module-level NAME = ...), or inline. A literal whose value equals a ledger template (the same module's SPECS; the
body ledger for the driver) is marked as duplicating that row when its name shares a word with the row id or the
value has three or more significant digits (so 0.5 does not match every half).

Then the hand review (data/worm/catalog/hidden_review.csv: file, value, code substring -> verdict, catalog row,
owner, note; the most specific match wins) gives each literal a verdict: parameter or initial condition (the catalog
now has a row for it, origin "hidden", and the owner's code should read it), duplicate of a catalog row (the code
should read the row), mirrors a catalog row, ported-mode fallback (literature_overrides off only), mod default
overwritten, default shadowed by a catalog row, test stand-in, analysis, structure, numerics, arithmetic or unit
conversion. Literals the review does not cover take the verdict of their kind, or "unreviewed" for the named,
default and inline kinds. "code_side" lists what the owners need to change.

    PYTHONPATH=src:scripts/worm python scripts/worm/hidden_constants.py
"""
from __future__ import annotations

import ast
import json
import re
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/worm/catalog/hidden_constants.json"
PY = [*sorted((ROOT / "src/wormemu/mech").glob("*.py")), ROOT / "src/wormemu/brain.py",
      ROOT / "src/wormemu/brain_layers.py", *sorted((ROOT / "src/wormemu/body").glob("*.py"))]
CPP = [ROOT / "third_party/metaworm/driver/run_body.cpp"]
MOD = sorted((ROOT / "src/wormemu/nmodl").glob("*.mod"))
UNIT = {1e-15, 1e-12, 1e-9, 1e-6, 1e-4, 1e-3, 1e-2, 0.1, 10, 100, 1e3, 1e4, 1e6, 1e9, 1e12, 60, 3600, 86400, 6e4,
        3.6e6}
SHAPE_CALLS = {"zeros", "ones", "empty", "full", "linspace", "arange", "range", "reshape", "unpack", "_read",
               "frombuffer", "norm", "sum", "ion_style"}
REVIEW = ROOT / "data/worm/catalog/hidden_review.csv"
BODY_LEDGER = ROOT / "data/worm/ledger/metaworm_parameters.csv"
AUTO_VERDICT = {"unit conversion": "unit conversion", "numerical guard": "numerics", "small integer": "arithmetic",
                "shape or count": "structure"}
CODE_SIDE = ("parameter (catalog row)", "initial condition (catalog row)", "duplicate of a catalog row")
GUARD_NAME = re.compile(r"eps|tol|clip|max|min|floor|cap|guard|tiny", re.I)
PHYS = ("named constant", "function default", "inline")


def _parents(tree):
    par = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            par[ch] = node
    return par


def _call_name(node) -> str:
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def _assigns(tree) -> dict:
    """Module-level NAME = value and NAME: type = value."""
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            out.update({t.id: n.value for t in n.targets if isinstance(t, ast.Name)})
        elif isinstance(n, ast.AnnAssign) and n.value is not None and isinstance(n.target, ast.Name):
            out[n.target.id] = n.value
    return out


def _spec_aliases(tree) -> set[str]:
    """Spec, every module-level name bound to it (brain_layers: S = Spec) and every module-level function that returns
    a Spec call (neuromod: def S(...): return Spec(...))."""
    names = {"Spec"}
    for k, v in _assigns(tree).items():
        if isinstance(v, (ast.Name, ast.Attribute)) and (getattr(v, "id", "") or getattr(v, "attr", "")) in names:
            names.add(k)
    for f in tree.body:
        if isinstance(f, ast.FunctionDef) and any(isinstance(r, ast.Return) and isinstance(r.value, ast.Call)
                                                   and _call_name(r.value) in names for r in ast.walk(f)):
            names.add(f.name)
    return names


def _grows_specs(stmt) -> bool:
    """A module-level statement that adds to SPECS (SPECS += [...], or a loop calling SPECS.append / extend): every
    literal in it feeds a Spec."""
    for n in ast.walk(stmt):
        if isinstance(n, ast.AugAssign) and getattr(n.target, "id", "") == "SPECS":
            return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("append", "extend") \
                and getattr(n.func.value, "id", "") == "SPECS":
            return True
    return False


def _spec_names(tree) -> set[str]:
    """Module-level names the SPECS expression reads, followed down (tables of Spec values)."""
    assigns = _assigns(tree)
    seen, todo = set(), ["SPECS"]
    while todo:
        name = todo.pop()
        if name in seen or name not in assigns:
            continue
        seen.add(name)
        todo += [n.id for n in ast.walk(assigns[name]) if isinstance(n, ast.Name)]
    return seen


def _context(node, par) -> tuple[str, str]:
    """(kind hint, name): the enclosing function, keyword or assignment target."""
    n, kw = node, ""
    while n in par:
        p = par[n]
        if isinstance(p, ast.keyword) and not kw:
            kw = p.arg or ""
        if isinstance(p, ast.arguments):
            return "function default", kw or _default_name(p, n)
        if isinstance(p, (ast.Assign, ast.AnnAssign)) and isinstance(par.get(p), ast.Module):
            t = p.targets[0] if isinstance(p, ast.Assign) else p.target
            return "named constant", getattr(t, "id", "")
        if isinstance(p, ast.Assign) and not kw:
            kw = getattr(p.targets[0], "id", "") or getattr(p.targets[0], "attr", "")
        if isinstance(p, (ast.FunctionDef, ast.ClassDef)):
            return "inline", f"{p.name}" + (f"({kw}=)" if kw else "")
        n = p
    return "inline", kw


def _default_name(args: ast.arguments, node) -> str:
    pos = args.posonlyargs + args.args
    for a, d in zip(pos[len(pos) - len(args.defaults):], args.defaults):
        if d is node or any(x is node for x in ast.walk(d)):
            return a.arg
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        if d is not None and (d is node or any(x is node for x in ast.walk(d))):
            return a.arg
    return ""


def _kind(v: float, hint: str, name: str, muldiv: bool = False, shape: bool = False) -> str:
    if shape:
        return "shape or count"
    if abs(v) in UNIT and muldiv:
        return "unit conversion"
    if v != 0 and (abs(v) < 1e-6 or abs(v) >= 1e9):
        return "numerical guard"
    if GUARD_NAME.search(name or ""):
        return "numerical guard"
    if float(v).is_integer() and abs(v) in (2, 3):
        return "small integer"
    return hint


def _sig_digits(v: float) -> int:
    return len(f"{abs(v):.12g}".split("e")[0].replace(".", "").strip("0"))


def _words(s: str) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", s.lower()) if len(w) >= 2}


def _dups(v: float, name: str, templates: dict) -> list[str]:
    """Rows whose template equals v, when the name shares a word with the row id or v has 3+ significant digits."""
    if v in (2, 3):
        return []
    hit = [pid for pid, t in templates.items() if t is not None and abs(t - v) <= 1e-12 * max(1, abs(v))]
    return [pid for pid in hit if _sig_digits(v) >= 3 or _words(name) & _words(pid)][:3]


def _muldiv_shape(node, par) -> tuple[bool, bool]:
    """(the literal multiplies or divides something, it is an argument of a shape or count call)."""
    q = par.get(node)
    if isinstance(q, ast.UnaryOp):
        node, q = q, par.get(q)
    muldiv = isinstance(q, ast.BinOp) and isinstance(q.op, (ast.Mult, ast.Div, ast.FloorDiv))
    n = node
    while n in par and not isinstance(par[n], ast.stmt):
        p = par[n]
        if isinstance(p, ast.keyword) and p.arg == "axis":
            return muldiv, True
        if isinstance(p, ast.Call) and n is not p.func:
            return muldiv, _call_name(p) in SHAPE_CALLS
        n = p
    return muldiv, False


def scan_python(path: Path, templates: dict) -> tuple[list, Counter]:
    src = path.read_text()
    tree, lines = ast.parse(src), src.splitlines()
    par, spec_names, skipped = _parents(tree), _spec_names(tree), Counter()
    in_specs, assigns, aliases = set(), _assigns(tree), _spec_aliases(tree)
    for k in spec_names:
        in_specs |= {id(x) for x in ast.walk(assigns[k])}
    for stmt in tree.body:
        if _grows_specs(stmt):
            in_specs |= {id(x) for x in ast.walk(stmt)}
    in_param = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and (_call_name(n) in aliases or _call_name(n).endswith("Spec")):
            in_specs |= {id(x) for x in ast.walk(n)}
        elif isinstance(n, ast.Call) and _call_name(n) == "Param":
            in_param |= {id(x) for x in ast.walk(n)}
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
                and not isinstance(node.value, bool)):
            continue
        p = par.get(node)
        v = -node.value if isinstance(p, ast.UnaryOp) and isinstance(p.op, ast.USub) else node.value
        if id(node) in in_specs:
            skipped["in a Spec (ledger)"] += 1
            continue
        if id(node) in in_param:
            skipped["in a scene Param (catalog rows scene_*)"] += 1
            continue
        if v in (0, 1, -1):
            skipped["0, 1 or -1"] += 1
            continue
        q, sub = node, False
        while q in par and not isinstance(q, ast.stmt):
            if isinstance(par[q], ast.Subscript) and par[q].slice is q or isinstance(par[q], ast.Slice):
                sub = True
                break
            q = par[q]
        if sub:
            skipped["index or slice"] += 1
            continue
        hint, name = _context(node, par)
        kind = _kind(float(v), hint, name, *_muldiv_shape(node, par))
        out.append(dict(file=str(path.relative_to(ROOT)), line=node.lineno, value=v, kind=kind, name=name,
                        code=lines[node.lineno - 1].strip()[:160], duplicates=_dups(v, name, templates)))
    return out, skipped


NUM = re.compile(r"(?<![\w.])-?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?[fF]?(?![\w.])")


def _strip(text: str, cpp: bool) -> str:
    """Blank out comments and strings, keep line numbers."""
    if cpp:
        text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
    else:
        text = re.sub(r"COMMENT.*?ENDCOMMENT", lambda m: re.sub(r"[^\n]", " ", m.group()), text, flags=re.S)
        text = re.sub(r":[^\n]*", "", text)
        text = re.sub(r"\b(TITLE|UNITS|VERBATIM)\b[^\n]*", "", text)
    return re.sub(r'"[^"\n]*"', '""', text)


def scan_text(path: Path, cpp: bool, set_from_spec: set, templates: dict) -> tuple[list, Counter]:
    raw = path.read_text()
    lines, text = raw.splitlines(), _strip(raw, cpp)
    out, skipped, block = [], Counter(), ""
    for i, ln in enumerate(text.splitlines(), 1):
        m = re.match(r"\s*(PARAMETER|ASSIGNED|STATE|NEURON|UNITS|INITIAL|BREAKPOINT|DERIVATIVE|PROCEDURE|FUNCTION|"
                     r"NET_RECEIVE|KINETIC)\b", ln)
        if not cpp and m:
            block = m.group(1)
        if not cpp and block in ("NEURON", "UNITS", "STATE", "ASSIGNED"):
            continue
        if cpp and re.match(r"\s*#\s*include", ln):
            continue
        for mm in NUM.finditer(ln):
            v = float(mm.group(0).rstrip("fF"))
            if v in (0, 1, -1):
                skipped["0, 1 or -1"] += 1
                continue
            if cpp and re.search(r"\[[^\]]*" + re.escape(mm.group(0)) + r"[^\[]*\]", ln):
                skipped["index or slice"] += 1
                continue
            var = re.match(r"\s*(\w+)\s*=", ln)
            name = var.group(1) if var else ""
            if not cpp and block == "PARAMETER" and name in set_from_spec:
                skipped["NMODL PARAMETER set from a Spec"] += 1
                continue
            hint = "named constant" if (not cpp and block == "PARAMETER") or (cpp and re.match(
                r"\s*(static\s+)?(const|constexpr)\b", ln)) else "inline"
            muldiv = bool(re.search(r"[*/]\s*$", ln[:mm.start()]) or re.match(r"\s*[*/]", ln[mm.end():]))
            local = re.findall(r"(\w+)\s*=[^=,;]*$", ln[:mm.start()])
            nm = name or (local[-1] if local else "")
            out.append(dict(file=str(path.relative_to(ROOT)), line=i, value=v, kind=_kind(v, hint, nm, muldiv),
                            name=nm, code=lines[i - 1].strip()[:160], duplicates=_dups(v, nm, templates)))
    return out, skipped


def _set_from_spec() -> set:
    """NMODL variables brain.py and mech/*.py set from the ledger (setattr(pp, q, ...) or pp.q = sv(...))."""
    names = set()
    for f in PY:
        t = f.read_text()
        names |= set(re.findall(r"setattr\(\w+, ['\"](\w+)['\"]", t))
        names |= set(re.findall(r"\.(\w+) = (?:sv|self\.spec\.v|p\[|params\[)", t))
        for q in re.findall(r"for q in \(([^)]*)\)", t):
            names |= set(re.findall(r"['\"](\w+)['\"]", q))
    return names


def _templates() -> dict:
    """{module file: {spec id: template}} so a literal can be matched against its own module's ledger rows."""
    import importlib
    out = {}
    for f in PY:
        mod = "wormemu." + ".".join(f.relative_to(ROOT / "src/wormemu").with_suffix("").parts)
        try:
            m = importlib.import_module(mod.replace(".__init__", ""))
        except Exception:  # noqa: BLE001 (a module that does not import is still scanned, without the match)
            continue
        out[str(f.relative_to(ROOT))] = {s.id: float(s.template) for s in getattr(m, "SPECS", [])
                                         if isinstance(getattr(s, "template", None), (int, float))}
    return out


def _body_templates() -> dict:
    """{body ledger row: value used} for the driver (run_body.cpp)."""
    import csv
    if not BODY_LEDGER.exists():
        return {}
    out = {}
    with BODY_LEDGER.open() as f:
        for r in csv.DictReader(f):
            try:
                out[r["param_id"]] = float(r["value_used"])
            except ValueError:
                pass
    return out


def _review() -> list[dict]:
    """Hand verdicts, most specific first (value and code substring, then substring, then value, then file)."""
    import csv
    if not REVIEW.exists():
        return []
    with REVIEW.open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["_v"] = float(r["value"]) if r["value"].strip() else None
    return sorted(rows, key=lambda r: (r["_v"] is None, not r["match"]))


def _verdict(x: dict, review: list[dict]) -> dict:
    for r in review:
        if r["file"] == x["file"] and (r["_v"] is None or abs(r["_v"] - x["value"]) <= 1e-12 * max(1, abs(x["value"]))) \
                and (not r["match"] or r["match"] in x["code"]):
            return dict(verdict=r["verdict"], row=r["row"], owner=r["owner"], note=r["note"])
    return dict(verdict=AUTO_VERDICT.get(x["kind"], "unreviewed"), row="", owner="", note="")


def main() -> None:
    tmpl = _templates()
    items, skipped = [], Counter()
    for f in PY:
        it, sk = scan_python(f, tmpl.get(str(f.relative_to(ROOT)), {}))
        items += it
        skipped += sk
    sfs = _set_from_spec()
    body = _body_templates()
    for f in CPP:
        it, sk = scan_text(f, True, sfs, body)
        items += it
        skipped += sk
    for f in MOD:
        it, sk = scan_text(f, False, sfs, {})
        items += it
        skipped += sk
    items.sort(key=lambda x: (x["file"], x["line"]))
    review = _review()
    for x in items:
        x.update(_verdict(x, review))
    by_verdict = Counter(x["verdict"] for x in items)
    code_side = [{k: x[k] for k in ("file", "line", "value", "verdict", "row", "owner", "note", "code")}
                 for x in items if x["verdict"] in CODE_SIDE]
    rows_added = sorted({r for x in items if x["verdict"].endswith("(catalog row)") for r in x["row"].split()})
    by_file = Counter(x["file"] for x in items)
    by_kind = Counter(x["kind"] for x in items)
    phys = [x for x in items if x["kind"] in PHYS]
    out = dict(generated_by="scripts/worm/hidden_constants.py", generated_at=time.strftime("%Y-%m-%d %H:%M %Z"),
               scanned=[str(f.relative_to(ROOT)) for f in [*PY, *CPP, *MOD]],
               total=len(items), needs_ledger_row=len(phys),
               duplicates_ledger=sum(1 for x in items if x["duplicates"]),
               by_file=dict(by_file.most_common()), by_kind=dict(by_kind.most_common()),
               by_file_needs_row=dict(Counter(x["file"] for x in phys).most_common()),
               by_verdict=dict(by_verdict.most_common()), unreviewed=by_verdict.get("unreviewed", 0),
               catalog_rows_added=rows_added, code_side=code_side,
               skipped=dict(skipped), items=items)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"{len(items)} literals not read from the ledger ({len(phys)} named, default or inline; "
          f"{out['duplicates_ledger']} duplicate a ledger template); skipped {dict(skipped)}")
    for k, v in by_file.most_common():
        print(f"  {v:4d}  {k}")
    print("  kinds:", dict(by_kind))
    print("  verdicts:", dict(by_verdict.most_common()))
    print(f"  code side ({len(code_side)}):")
    for x in code_side:
        print(f"    {x['file']}:{x['line']} {x['value']} -> {x['row']} ({x['owner']})")
    for x in items:
        if x["verdict"] == "unreviewed":
            print(f"  UNREVIEWED {x['file']}:{x['line']} {x['value']} [{x['kind']}] {x['code'][:90]}")


if __name__ == "__main__":
    main()
