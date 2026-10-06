"""The status a run is recorded with (manifest profile_status). One rule for the recorder
(record.py), the server's protocol check (sessions.py) and the Fidelity build; the page
mirrors it in fidelity.js configStatus, and a test holds the two together. No model
imports, so the server can use it without building anything.
"""
from __future__ import annotations

NAMED = {"m4": "regression reference", "m10p": "candidate, not adopted", "m10q": "candidate, not adopted"}


def profile_status(profile: str | None, overrides: dict, extra_rows: bool, working: str) -> str:
    """`profile` as the recorder resolves it: a missing config.profile is the working
    profile (callers fill it in); null, "" or "none" mean no profile."""
    added = " and ".join(w for w, on in (("overrides", overrides), ("extra per-type rows", extra_rows)) if on)
    if profile == working:
        return f"adopted profile with {added}: custom, not validated" if added else "adopted (working profile)"
    named = NAMED.get(profile or "")
    if named and added:     # a named profile changed is no longer that profile
        return f"{profile} ({named}) with {added}: custom, not validated"
    return named or "custom, not validated"
