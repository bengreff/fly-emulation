"""Check every distinct source URL in the worm catalog once, and every paper-text quote against its cited free text.

Writes data/worm/catalog/link_check.csv (url, status, final_url, n_rows, checked_at). The ledger build reads it and
flags rows whose link answered 404 or 410 or did not answer. Publisher pages that refuse scripted requests (401, 403,
406, 429) are recorded but not flagged, since a browser opens them.

Writes data/worm/catalog/quote_check.csv (id, status, searched, found_in, missing, quote_sha, checked_at). A quote is
searched for, piece by piece (pieces split at "..." or "[...]"; case, whitespace, format characters, dashes and quote
marks aside), in: the free full text of each PMC id the row cites (Europe PMC, else the PMC page or NCBI efetch when
Europe PMC serves only the front matter); a PubMed id's or DOI's PMC full text, else its abstract; a vendored model
file the source names (published/NAME, with COPASI references written <name>); a saved excerpt
(data/worm/catalog/excerpts/) the source names or that names a cited PMC id. Status: found; not found (a full text was
searched and a piece is missing: the build flags it); no free full text (only an abstract, or nothing, could be
fetched). Research-file quotes are checked by the build itself. Complete fetches are cached in
~/.cache/wormcatalog/fulltext. A bot check (captcha) is a stop, not something to get past.

    PYTHONPATH=src:scripts/worm python scripts/worm/catalog_links.py
"""
from __future__ import annotations

import csv
import html
import json
import re
import subprocess
import time
import unicodedata
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ledger_catalog import QUOTE, quote_sha

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/worm/model/catalog.csv"
OUT = ROOT / "data/worm/catalog/link_check.csv"
QUOTES = ROOT / "data/worm/catalog/quote_check.csv"
EXCERPTS = ROOT / "data/worm/catalog/excerpts"
CACHE = Path.home() / ".cache/wormcatalog/fulltext"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
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


# ------------------------------------------------------------------------------------------------------ the quotes
def _get(url: str) -> str:
    p = subprocess.run(["curl", "-s", "-L", "--max-time", "40", "-A", UA, url], capture_output=True, text=True)
    time.sleep(1)                                            # one request at a time, spaced
    return p.stdout


def _strip(x: str) -> str:
    x = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", x)
    return html.unescape(re.sub(r"<[^>]+>", " ", x))


def _cached(key: str, fetch) -> str:
    """fetch() -> (text, complete); only a complete answer is kept (a failed or partial one is retried next run)."""
    f = CACHE / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', key)}.txt"
    if f.exists():
        return f.read_text()
    t, complete = fetch()
    if complete and t.strip():
        CACHE.mkdir(parents=True, exist_ok=True)
        f.write_text(t)
    return t


def _error(x: str) -> bool:
    return bool(re.search(r'"status":\s*5\d\d|captcha|Just a moment', x[:5000], re.I)) or len(x.strip()) < 2000


def pmc_text(pmc: str) -> str:
    def fetch() -> tuple[str, bool]:
        x = _get(f"{EPMC}/{pmc}/fullTextXML")
        t, complete = ("", False) if _error(x) else (_strip(x), True)
        if len(t) < 20000:                 # Europe PMC often serves only the front matter; the PMC page has the body
            for url in (f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/",
                        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc[3:]}"):
                h = _get(url)
                if _error(h):
                    complete = False
                elif len(h := _strip(h)) > len(t):
                    t = h
                if len(t) >= 20000:
                    return t, True
        return t, complete
    return _cached(pmc, fetch)


def record_text(query: str) -> tuple[str, str, bool]:
    """(what was searched, its text, is it a full text) for a Europe PMC search (a PubMed id or a DOI)."""
    def fetch() -> tuple[str, bool]:
        x = _get(f"{EPMC}/search?" + urllib.parse.urlencode({"query": query, "format": "json", "resultType": "core"}))
        return x, '"resultList"' in x
    raw = _cached("rec " + query, fetch)
    try:
        res = json.loads(raw)["resultList"]["result"]
    except (ValueError, KeyError):
        res = []
    if not res:
        return query, "", False
    if res[0].get("pmcid"):
        return res[0]["pmcid"], pmc_text(res[0]["pmcid"]), True
    return f"abstract {res[0].get('id', query)}", _strip(res[0].get("abstractText", "")), False


def model_file_text(f: Path) -> str:
    t = html.unescape(f.read_text(errors="replace"))
    t = re.sub(r"<CN=Root[^>]*,Vector=\w+\[((?:\\.|[^\]\\])*)\],Reference=\w+>",
               lambda m: "<" + re.sub(r"\\(.)", r"\1", m.group(1)) + ">", t)
    return t


def norm(s: str) -> str:
    # format characters (MathML's invisible times, soft hyphens) out; dashes, quote marks and micro signs unified
    s = "".join(ch for ch in unicodedata.normalize("NFKC", s) if unicodedata.category(ch) != "Cf")
    for a in "−–—‐‑":
        s = s.replace(a, "-")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("µ", "μ")
    return re.sub(r"\s+", "", s.lower())


def texts_for(r: dict) -> list[tuple[str, str, bool]]:
    s = f"{r['source_url']} {r['source']}"
    out = []
    pmcs = list(dict.fromkeys(re.findall(r"PMC\d+", s)))
    for p in pmcs:
        out.append((p, pmc_text(p), True))
    if not pmcs:
        for m in dict.fromkeys(re.findall(r"(?:PMID:?\s*|MED/|pubmed\.ncbi\.nlm\.nih\.gov/)(\d+)", s)):
            out.append(record_text(f"EXT_ID:{m} AND SRC:MED"))
        for d in dict.fromkeys(re.findall(r"doi\.org/(10\.\d{4,}/[^\s,;]+)", r["source_url"])):
            out.append(record_text(f'DOI:"{d.rstrip(".)")}"'))
    for name in dict.fromkeys(re.findall(r"published/([\w.-]+\.\w+)", s)):
        for f in sorted((ROOT / "src").glob(f"**/published/{name}"))[:1]:
            out.append((f"published/{name}", model_file_text(f), True))
    for f in sorted(EXCERPTS.glob("*.txt")):
        t = f.read_text()
        if f.name in s or any(p in t for p in pmcs):
            out.append((f"excerpts/{f.name}", t, True))
    return out


def check_quote(r: dict) -> dict:
    q = r["source_quote"].strip()
    texts = [(k, norm(t), full) for k, t, full in texts_for(r) if t.strip()]
    pieces = [p for p in re.split(r"\s*(?:\[\.\.\.\]|\.\.\.|…)\s*", q) if norm(p)]
    missing = [p for p in pieces if not any(norm(p) in t for _, t, _ in texts)]
    status = ("found" if texts and not missing else
              "not found" if any(full for _, _, full in texts) else "no free full text")
    found_in = [k for k, t, _ in texts if any(norm(p) in t for p in pieces)]
    return dict(id=r["id"], status=status, searched="; ".join(k for k, _, _ in texts), found_in="; ".join(found_in),
                missing=missing[0][:80] if missing and status == "not found" else "", quote_sha=quote_sha(q))


def check_quotes(rows: list[dict], stamp: str) -> None:
    todo = [r for r in rows if r["source_quote"].strip() and not QUOTE.match(r["source_quote"].strip())]
    res = [check_quote(r) for r in todo]
    with QUOTES.open("w", newline="") as f:
        w = csv.DictWriter(f, ["id", "status", "searched", "found_in", "missing", "quote_sha", "checked_at"])
        w.writeheader()
        for x in res:
            w.writerow({**x, "checked_at": stamp})
    tally = Counter(x["status"] for x in res)
    print(f"{len(res)} paper-text quotes: " + ", ".join(f"{k}: {v}" for k, v in sorted(tally.items())))
    for x in res:
        if x["status"] == "not found":
            print("  not found", x["id"], f"({x['searched']}):", x["missing"])


def main() -> None:
    with CATALOG.open() as f:
        rows = list(csv.DictReader(f))
    n = Counter(u for r in rows if (u := r["source_url"].strip()))
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
    check_quotes(rows, stamp)


if __name__ == "__main__":
    main()
