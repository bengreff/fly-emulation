"""Run provenance capture.

Every substantial run records: code commits, data hashes, config, environment,
timing and peak memory. See docs/VALIDATION.md "Experiment record".
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]


def file_sha256(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def git_commit(repo: str | Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def git_dirty(repo: str | Path) -> bool | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        return bool(out.stdout.strip())
    except Exception:
        return None


def peak_rss_gb() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Darwin reports bytes, Linux reports kibibytes.
    scale = 1 << 30 if sys.platform == "darwin" else 1 << 20
    return ru / scale


def environment() -> dict[str, Any]:
    import jax
    import numpy
    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "hostname": platform.node(),
        "numpy": numpy.__version__,
        "jax": jax.__version__,
        "jax_devices": [str(d) for d in jax.devices()],
        "jax_default_backend": jax.default_backend(),
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
    }
    try:
        import diffrax
        env["diffrax"] = diffrax.__version__
    except Exception:
        pass
    return env


class RunRecord:
    """Accumulates provenance for one experiment run and writes it as JSON."""

    def __init__(self, run_id: str, out_dir: str | Path, description: str = ""):
        self.run_id = run_id
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.t0 = time.time()
        self.rec: dict[str, Any] = {
            "run_id": run_id,
            "description": description,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "code": {
                "flyemu_commit": git_commit(REPO),
                "flyemu_dirty": git_dirty(REPO),
            },
            "environment": environment(),
            "inputs": {},
            "config": {},
            "scaffolds": [],
            "results": {},
        }

    def add_code(self, name: str, repo: str | Path) -> None:
        self.rec["code"][name] = {
            "path": str(repo),
            "commit": git_commit(repo),
            "dirty": git_dirty(repo),
        }

    def add_input(self, name: str, path: str | Path, note: str = "") -> None:
        p = Path(path)
        self.rec["inputs"][name] = {
            "path": str(p),
            "bytes": p.stat().st_size if p.exists() else None,
            "sha256": file_sha256(p) if p.exists() else None,
            "note": note,
        }

    def add_config(self, cfg: Any) -> None:
        try:
            from omegaconf import OmegaConf
            self.rec["config"] = OmegaConf.to_container(cfg, resolve=True)
        except Exception:
            self.rec["config"] = json.loads(json.dumps(cfg, default=str))

    def declare_scaffold(self, what: str) -> None:
        """Record any imposed stimulation, supplied rhythm or non-biological substitute.

        Required by docs/VALIDATION.md "Controls that matter".
        """
        self.rec["scaffolds"].append(what)

    def result(self, key: str, value: Any) -> None:
        self.rec["results"][key] = value

    def finish(self, status: str = "ok") -> Path:
        self.rec["status"] = status
        self.rec["wall_seconds"] = round(time.time() - self.t0, 3)
        self.rec["peak_rss_gb"] = round(peak_rss_gb(), 3)
        path = self.out_dir / f"{self.run_id}.provenance.json"
        path.write_text(json.dumps(self.rec, indent=2, default=str))
        return path
