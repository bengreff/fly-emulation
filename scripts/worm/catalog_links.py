"""Check every distinct source URL in the worm catalog once.

Writes data/worm/catalog/link_check.csv (url, status, final_url, n_rows, checked_at). The ledger build reads it and
flags rows whose link answered 404 or 410 or did not answer. Publisher pages that refuse scripted requests (401, 403,
406, 429) are recorded but not flagged, since a browser opens them.

    PYTHONPATH=src:scripts/worm python scripts/worm/catalog_links.py
"""
from __future__ import annotations

import csv
import subprocess
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/worm/model/catalog.csv"
OUT = ROOT / "data/worm/catalog/link_check.csv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
DEAD = {"404", "410", "000"}


def check(url: str) -> tuple[str, str]:
    status, final = "000", ""
    for _ in range(3):
        p = subprocess.run(["curl", "-s", "-L", "-o", "/dev/null", "--max-time", "30", "-A", UA,
                            "-w", "%{http_code} %{url_effective}", url], capture_output=True, text=True)
        status, _, final = p.stdout.strip().partition(" ")
        if status not in DEAD and status != "429":
            break
        time.sleep(2)
    return status or "000", final


def main() -> None:
    with CATALOG.open() as f:
        n = Counter(u for r in csv.DictReader(f) if (u := r["source_url"].strip()))
    urls = sorted(n)
    with ThreadPoolExecutor(4) as ex:
        res = dict(zip(urls, ex.map(check, urls)))
    stamp = time.strftime("%Y-%m-%d %H:%M %Z")
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["url", "status", "final_url", "n_rows", "checked_at"])
        for u in urls:
            w.writerow([u, res[u][0], res[u][1], n[u], stamp])
    tally = Counter(s for s, _ in res.values())
    print(f"{len(urls)} distinct URLs: " + ", ".join(f"{k}: {v}" for k, v in sorted(tally.items())))
    for u in urls:
        if res[u][0] not in {"200"}:
            print(res[u][0], u, "->", res[u][1])


if __name__ == "__main__":
    main()
