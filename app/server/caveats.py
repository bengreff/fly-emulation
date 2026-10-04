"""Caveats generated from a recording, so the viewer never shows stale text.

Each caveat is {id, text, basis}: basis says whether the statement was measured
from this run, read from the model's configuration, or is a standing project
finding (with its reference).
"""
from __future__ import annotations

import numpy as np

R16_FLY_TYPICAL = 9600     # R1-R6 photoreceptors in a fly, as used by src/flyemu/vision.py (inferred)


def generate(manifest: dict, static: dict, org=None) -> list[dict]:
    c = []
    n = manifest["n_rows"]
    cfg = manifest["config"]
    s = manifest.get("summary", {})

    def add(i, text, basis):
        c.append({"id": i, "text": text, "basis": basis})

    add("network", f"{n:,} neurons and {manifest['n_edges']:,} connections "
        f"({manifest['n_synapses']:,} synapses) from {cfg['scan']}: proofread or typed cells, "
        f"connections of at least {cfg['min_synapses']} synapses.", "configuration")
    add("profile", f"Profile {cfg['profile']}: {manifest['profile_status']}."
        + (f" Overrides: {', '.join(f'{k} = {v:g}' for k, v in cfg['overrides'].items())}."
           if cfg["overrides"] else ""), "configuration")
    prep = manifest.get("preparation", {})
    if prep.get("coupling") == "brain_only":
        add("preparation", "Open loop, brain only: the network received only the protocol's "
            "stimulus; no senses, no motor output, and the body was never stepped, so the fly "
            "shown does not move. This is the preparation of the model's pathway assays "
            "(scripts/assay_pathways.py)." + (" Kicks drawn from that script's random stream."
                                              if prep.get("kick_rng") == "assay" else ""),
            "configuration")
    add("start", "Every neuron starts at rest with no synaptic history and the body starts "
        "above the ground; the opening fall and the first tens of ms are transients of that "
        "choice, not behaviour.", "configuration")
    if s:
        rate = s["mean_rate_hz"]
        add("activity", f"{s['spikes_total']:,} spikes, mean {rate:.2f} Hz per neuron over "
            f"{manifest['duration_ms']:g} ms." + (" The network was silent." if s["spikes_total"] == 0 else ""),
            "measured in this run")
        add("speed", f"Computed at {s['wall_s_per_sim_s']:.0f} s of wall time per simulated second "
            f"on {manifest['provenance'].get('host', '?')}.", "measured in this run")
    g = int(static["graded"].sum())
    if g:
        add("graded", f"{g:,} cells are graded (non-spiking) in this profile; their activity "
            "does not appear in the spike map, only in watched voltages.", "configuration")
    mapped = int(static["mn_mapped"].sum())
    nmn = int(static["mn_rows"].size)
    add("motor", f"{mapped} of {nmn} motor neurons drive a muscle in the body model; the other "
        f"{nmn - mapped} spike but move nothing.", "configuration")
    clip = np.asarray(s.get("torque_clip_fraction", []))
    if clip.size and clip.max() > 0:
        k = int((clip > 0.01).sum())
        add("clipping", f"{k} of {clip.size} actuators sat at their torque limit in more than 1% "
            f"of samples (worst {clip.max():.0%}); clipped torque is marked in the torque panel.",
            "measured in this run")
    if org is not None and getattr(org, "vis", None) is not None:
        add("vision", f"The eyes are flygym's 721 ommatidia per eye sampled at 100 Hz. The "
            f"connectome holds about a third of the R1-R6 photoreceptors of a fly "
            f"(~{R16_FLY_TYPICAL:,} in a fly, inferred), so many ommatidia drive no cell.",
            "configuration; src/flyemu/vision.py")
    nts = static.get("nt_source")
    if nts is not None:
        add("transmitter", f"Transmitter per cell: {int((nts == 0).sum()):,} from the EM classifier, "
            f"{int((nts == 1).sum()):,} from the dataset's consensus call where it differs, "
            f"{int((nts == 2).sum()):,} filled by the project's hemilineage rule (inferred).",
            "configuration")
    for e in manifest.get("protocol", {}).get("resolved", {}).get("events", []):
        if e.get("approximation"):
            add("stim-" + e["effector"], f"{e['effector']} on {e['n']} cells is an approximation: "
                f"{e['approximation']}.", "configuration")
    return c
