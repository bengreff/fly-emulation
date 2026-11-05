import glob, os, re, math, csv, sys
D = os.path.expanduser("~/worm-data/morphologies/CElegansNeuroML/CElegans/generatedNeuroML2/")
pt = re.compile(r'<(proximal|distal) x="([-\d.eE]+)" y="([-\d.eE]+)" z="([-\d.eE]+)" diameter="([-\d.eE]+)"')
seg = re.compile(r'<segment id="(\d+)"[^>]*>(.*?)</segment>', re.S)
par = re.compile(r'<parent segment="(\d+)"')
w = csv.writer(sys.stdout); w.writerow(["name", "soma_x", "soma_y", "soma_z", "soma_diam_um", "area_um2", "length_um", "n_seg"])
for f in sorted(glob.glob(D + "*.cell.nml")):
    s = open(f).read(); name = os.path.basename(f).split(".")[0]
    segs = {}
    for m in seg.finditer(s):
        body = m.group(2); pts = {k: (float(x), float(y), float(z), float(d)) for k, x, y, z, d in pt.findall(body)}
        pm = par.search(body); segs[int(m.group(1))] = (pts, int(pm.group(1)) if pm else None)
    area = length = 0.0
    for i, (pts, p) in segs.items():
        d = pts["distal"]; pr = pts.get("proximal") or (segs[p][0]["distal"] if p is not None else d)
        L = math.dist(pr[:3], d[:3]); r1, r2 = pr[3] / 2, d[3] / 2
        if L == 0:  # spherical soma written as a zero-length segment
            area += math.pi * d[3] ** 2
        else:
            area += math.pi * (r1 + r2) * math.sqrt(L ** 2 + (r1 - r2) ** 2); length += L
    s0 = segs[0][0]["proximal"]
    w.writerow([name, *s0[:3], s0[3], round(area, 2), round(length, 1), len(segs)])
