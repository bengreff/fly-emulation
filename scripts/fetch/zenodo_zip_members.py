"""Fetch individual members of a large remote zip by HTTP range requests.

Reads the zip's central directory from the end of the file, then downloads
only the requested members (deflate or stored). Used for Agrawal et al. 2020
(Zenodo 4307018, Ephys_data.zip, 7.5 GB, CC0), which Zenodo serves at < 1 MB/s.

    uv run python scripts/fetch/zenodo_zip_members.py --list
    uv run python scripts/fetch/zenodo_zip_members.py "Ephys data/13Balpha_RMP_swings.mat"
"""
import argparse
import struct
import urllib.request
import zlib
from pathlib import Path

URL = "https://zenodo.org/api/records/4307018/files/Ephys_data.zip/content"
OUT = Path(__file__).resolve().parents[2] / "data/raw/agrawal2020"


def rng(a, b):
    r = urllib.request.Request(URL, headers={"Range": f"bytes={a}-{b}"})
    return urllib.request.urlopen(r, timeout=600).read()


def size():
    r = urllib.request.urlopen(urllib.request.Request(URL, method="HEAD"), timeout=60)
    return int(r.headers["Content-Length"])


def directory():
    n = size()
    tail = rng(n - (1 << 20), n - 1)
    i = tail.rfind(b"PK\x05\x06")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    if cd_off == 0xFFFFFFFF:
        j = tail.rfind(b"PK\x06\x06")
        cd_size, cd_off = struct.unpack("<QQ", tail[j + 40:j + 56])
    cd = rng(cd_off, cd_off + cd_size - 1)
    ents, p = {}, 0
    while cd[p:p + 4] == b"PK\x01\x02":
        comp = struct.unpack("<H", cd[p + 10:p + 12])[0]
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nl, el, cl = struct.unpack("<HHH", cd[p + 28:p + 34])
        off = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + nl].decode(errors="replace")
        extra = cd[p + 46 + nl:p + 46 + nl + el]
        q = 0
        while q < len(extra):                       # zip64 extended information
            hid, hs = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                data, k = extra[q + 4:q + 4 + hs], 0
                if usize == 0xFFFFFFFF: usize = struct.unpack("<Q", data[k:k + 8])[0]; k += 8
                if csize == 0xFFFFFFFF: csize = struct.unpack("<Q", data[k:k + 8])[0]; k += 8
                if off == 0xFFFFFFFF: off = struct.unpack("<Q", data[k:k + 8])[0]; k += 8
            q += 4 + hs
        ents[name] = dict(comp=comp, csize=csize, usize=usize, off=off)
        p += 46 + nl + el + cl
    return ents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("members", nargs="*")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    ents = directory()
    if a.list:
        for k, v in sorted(ents.items(), key=lambda kv: kv[1]["csize"]):
            print(f"{v['csize'] / 1e6:8.1f} MB  {k}")
    OUT.mkdir(parents=True, exist_ok=True)
    for name in a.members:
        x = ents[name]
        h = rng(x["off"], x["off"] + 29)
        nl, el = struct.unpack("<HH", h[26:30])
        start = x["off"] + 30 + nl + el
        raw = rng(start, start + x["csize"] - 1)
        data = zlib.decompress(raw, -15) if x["comp"] == 8 else raw
        assert len(data) == x["usize"]
        (OUT / Path(name).name).write_bytes(data)
        print(OUT / Path(name).name, len(data))


if __name__ == "__main__":
    main()
