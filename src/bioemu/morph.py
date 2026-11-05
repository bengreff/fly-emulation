"""Morphology I/O: NeuroML2 <segment> lists to SWC, so any reconstruction can feed Jaxley/NEURON/Arbor."""
import xml.etree.ElementTree as ET


def nml_to_swc(nml_path, swc_path):
    """Convert a NeuroML2 cell (segments with proximal/distal points) to SWC.

    Soma segments get SWC type 1, others type 3. A segment's proximal point is used only for the
    root; children start from their parent's distal point (NeuroML fractionAlong is ignored).
    Returns (n_points, total neurite length um).
    """
    root = ET.parse(nml_path).getroot()
    segs = [e for e in root.iter() if e.tag.endswith("}segment") or e.tag == "segment"]
    rows, length = [], 0.0
    pid = {}
    for s in segs:
        sid = int(s.get("id"))
        name = s.get("name", "")
        kids = {c.tag.split("}")[-1]: c for c in s}
        dist = kids["distal"]
        par = kids.get("parent")
        x, y, z, d = (float(dist.get(k)) for k in ("x", "y", "z", "diameter"))
        typ = 1 if "soma" in name.lower() else 3
        if par is None:
            pid[sid] = len(rows) + 1
            rows.append((pid[sid], 1, x, y, z, d / 2, -1))
            continue
        p = pid[int(par.get("segment"))]
        prox = kids.get("proximal")
        if prox is not None and typ != 1:
            px, py, pz = (float(prox.get(k)) for k in ("x", "y", "z"))
        else:
            px, py, pz = rows[p - 1][2:5]
        length += ((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2) ** 0.5
        pid[sid] = len(rows) + 1
        rows.append((pid[sid], typ, x, y, z, d / 2, p))
    with open(swc_path, "w") as f:
        f.write(f"# converted from {nml_path} by bioemu.morph.nml_to_swc\n")
        for r in rows:
            f.write("%d %d %.4f %.4f %.4f %.5f %d\n" % r)
    return len(rows), length
