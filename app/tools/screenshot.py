"""Headless screenshots of Fly Workbench, plus a contact sheet.

    python app/tools/screenshot.py [--url http://127.0.0.1:8765/] [--out runs/app/shots]
        [--shot name:query ...] [--width 1600 --height 1000]

Each --shot is a name and a URL query (e.g. "flow:view=flow&t=500"). Starts its
own server on a free port unless --url is given, and stops it afterwards. Fails
if the page reports an error or a canvas is blank.
"""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent

DEFAULT = [
    "anatomy:t=600",
    "flow:t=600&view=flow&colour=layer",
    "groups:t=600&view=groups",
    "selected:t=600&sel=800184",
    "run-dark:t=1200&theme=dark&colour=nt",
]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def canvas_stats(page, sel):
    """Fraction of pixels differing from the corner colour, read from the canvas."""
    return page.evaluate("""sel => {
      const c = document.querySelector(sel); const w = c.width, h = c.height;
      const t = document.createElement('canvas'); t.width = w; t.height = h;
      const g = t.getContext('2d'); g.drawImage(c, 0, 0);
      const d = g.getImageData(0, 0, w, h).data; const r0 = d[0], g0 = d[1], b0 = d[2];
      let n = 0; for (let i = 0; i < d.length; i += 16) if (Math.abs(d[i]-r0)+Math.abs(d[i+1]-g0)+Math.abs(d[i+2]-b0) > 24) n++;
      return n / (d.length / 16);
    }""", sel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--out", type=Path, default=REPO / "runs" / "app" / "shots")
    ap.add_argument("--shot", action="append")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=1000)
    ap.add_argument("--select-type", help="search box text to try (checks search and selection)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    srv = None
    url = a.url
    if not url:
        port = free_port()
        srv = subprocess.Popen([sys.executable, str(APP / "server" / "serve.py"), "--port", str(port)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        url = f"http://127.0.0.1:{port}/"
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), 0.2).close()
                break
            except OSError:
                time.sleep(0.1)
    shots, failures = [], []
    try:
        with sync_playwright() as p:
            br = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            for spec in a.shot or DEFAULT:
                name, q = spec.split(":", 1)
                pg = br.new_page(viewport={"width": a.width, "height": a.height})
                errors = []
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                t0 = time.time()
                pg.goto(url + "?" + q)
                try:
                    pg.wait_for_selector("body.ready", timeout=120_000)
                except Exception:
                    errors.append("page never became ready: " + pg.inner_text("#status"))
                load_s = time.time() - t0
                pg.wait_for_timeout(1500)
                if "run" in name:
                    pg.click("#tabs button[data-tab=run]")
                stats = {c: canvas_stats(pg, "#" + c) for c in ("body", "brain", "traces")}
                path = a.out / f"{name}.png"
                pg.screenshot(path=str(path))
                shots.append((name, path))
                blank = [c for c, v in stats.items() if v < 0.005]
                print(f"{name}: loaded in {load_s:.1f} s; non-background fraction "
                      + ", ".join(f"{c} {v:.3f}" for c, v in stats.items())
                      + (f"; BLANK {blank}" if blank else "") + (f"; ERRORS {errors[:3]}" if errors else ""))
                if blank or errors:
                    failures.append(name)
                pg.close()
            br.close()
    finally:
        if srv:
            srv.terminate()
            srv.wait(5)
    # contact sheet: two columns at half size
    ims = [Image.open(p) for _, p in shots]
    w, h = ims[0].width // 2, ims[0].height // 2
    sheet = Image.new("RGB", (w * 2, (h + 20) * ((len(ims) + 1) // 2)), "white")
    d = ImageDraw.Draw(sheet)
    for k, ((name, _), im) in enumerate(zip(shots, ims)):
        x, y = (k % 2) * w, (k // 2) * (h + 20)
        sheet.paste(im.resize((w, h)), (x, y + 20))
        d.text((x + 6, y + 4), name, fill="black")
    sheet.save(a.out / "contact.png")
    print(f"wrote {len(shots)} shots and {a.out / 'contact.png'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
