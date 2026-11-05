"""Record a viewer run to MP4: headless Chrome steps the page frame by frame, ffmpeg encodes at the sim frame rate.

    .venv/bin/python scripts/worm/record_viewer_mp4.py p3_final [port]
Needs viewer/worm/serve.py running on 127.0.0.1:<port> (default 8781). Writes runs/worm/media/<run>.mp4 and a
contact sheet runs/worm/media/<run>_sheet.png (frames 0, 25%, 50%, 75%, last) for checking by eye.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
run = sys.argv[1] if len(sys.argv) > 1 else "p3_final"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8781
out = REPO / "runs" / "worm" / "media"
out.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory() as td, sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1600, "height": 900})
    pg.goto(f"http://127.0.0.1:{port}/?record=1&run={run}")
    pg.wait_for_function("window.viewer && window.viewer.ready", timeout=30000)
    n = pg.evaluate("window.viewer.nFrames()")
    for f in range(n):
        pg.evaluate(f"window.viewer.rotateWire({0.6 * f / n:.4f}); window.viewer.setFrame({f})")
        pg.screenshot(path=f"{td}/f{f:05d}.png")
    b.close()
    fps = 30
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{td}/f%05d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", str(out / f"{run}.mp4")], check=True)
    picks = [0, n // 4, n // 2, 3 * n // 4, n - 1]
    args = sum((["-i", f"{td}/f{k:05d}.png"] for k in picks), [])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex",
                    "".join(f"[{i}:v]scale=800:-1[s{i}];" for i in range(5)) + "".join(f"[s{i}]" for i in range(5))
                    + "vstack=inputs=5", str(out / f"{run}_sheet.png")], check=True)
print(out / f"{run}.mp4", n, "frames")
