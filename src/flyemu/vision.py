"""Vision: the compound eyes, and what this graph cannot tell us about them.

The primary graph carries real photoreceptor identities - 3,377 R1-R6, the
pale and yellow R7/R8 subtypes, the dorsal-rim R7d/R8d, and the seven-cell
Hofbauer-Buchner eyelet - and the body model renders 721 ommatidia per eye in
two spectral channels. What is missing between them is the map.

**There is no retinotopy available.** `male-cns:v1.0` gives a photoreceptor no
column, no hex coordinate and no position: its only spatial annotation is
"lamina, right". `optic-lobe:v1.1` has no `olHex` coordinates either. So which
ommatidium a given photoreceptor looks through cannot be established from these
releases, and inventing an assignment would give the network spatially
structured input with a scrambled map - which would look like working vision
while being nothing of the kind.

So this channel is deliberately NON-RETINOTOPIC: each photoreceptor is driven
by the mean luminance of the ommatidia matching its spectral type and eye. That
is real visual information - overall brightness per eye, which supports
phototaxis and looming-independent responses - and it is honest about what it
is not. Retinotopy is registered as unresolved with its full instance count.

Counts, for the record: a fly has roughly 800 ommatidia per eye and six R1-R6
each, so about 9,600 R1-R6 in total. This graph holds 3,377. The primary graph
does not contain one photoreceptor per ommatidium per eye.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .registry import Registry, Status

# Photoreceptor class -> which rendered channel it reads.
# The renderer returns two channels per ommatidium, yellow and pale, which are
# the two ommatidial subtypes. R1-R6 are broadband and read both.
CHANNEL_OF_TYPE: dict[str, str] = {
    "R1-R6": "both",
    "R7p": "pale", "R8p": "pale",
    "R7y": "yellow", "R8y": "yellow",
    # Dorsal rim ommatidia are specialised for POLARISATION, which the renderer
    # does not produce. Driven by luminance, and recorded as unresolved.
    "R7d": "both", "R8d": "both",
    # These have no spectral assignment in the annotation.
    "R7_unclear": "both", "R8_unclear": "both", "R7R8_unclear": "both",
}

# The Hofbauer-Buchner eyelet is extraretinal and circadian: it does not look
# through an ommatidium at all, so the eye render cannot drive it.
EXTRARETINAL = {"HBeyelet"}


@dataclass
class Vision:
    rows: np.ndarray            # network row index per photoreceptor
    eye: np.ndarray             # 0 left, 1 right
    channel: np.ndarray         # 'both' | 'pale' | 'yellow'
    gain_mv: float
    baseline_mv: float
    n_neurons: int
    sample_every: int           # timesteps between eye renders
    _last: np.ndarray | None = None

    def drive(self, readouts: np.ndarray) -> np.ndarray:
        """Turn one ommatidia readout into per-neuron membrane drive, in mV.

        `readouts` has shape (2 eyes, n_ommatidia, 2 channels). A zero means
        that ommatidium is of the other type, so the mean is taken over
        non-zero entries only.
        """
        out = np.zeros(self.n_neurons, dtype=np.float32)
        yellow = readouts[:, :, 0]
        pale = readouts[:, :, 1]

        def mean_nonzero(a: np.ndarray) -> float:
            nz = a[a > 0]
            return float(nz.mean()) if nz.size else 0.0

        per_eye = {
            (e, "yellow"): mean_nonzero(yellow[e]) for e in (0, 1)
        }
        per_eye.update({(e, "pale"): mean_nonzero(pale[e]) for e in (0, 1)})
        per_eye.update({
            (e, "both"): mean_nonzero(readouts[e]) for e in (0, 1)
        })

        for e in (0, 1):
            for ch in ("both", "pale", "yellow"):
                sel = (self.eye == e) & (self.channel == ch)
                if sel.any():
                    out[self.rows[sel]] = (
                        self.baseline_mv + self.gain_mv * per_eye[(e, ch)]
                    )
        self._last = out
        return out

    def last(self) -> np.ndarray:
        """The most recent drive, for the timesteps between eye renders."""
        if self._last is None:
            return np.zeros(self.n_neurons, dtype=np.float32)
        return self._last


def build(reg: Registry, conn, *, timestep_ms: float, sample_hz: float = 100.0
          ) -> Vision:
    n = conn.neurons
    ol = n[n.superclass == "ol_sensory"].copy()

    inst = ol.instance.fillna("")
    eye = np.where(inst.str.endswith("_L"), 0, 1)
    types = ol.type.fillna("unknown")

    keep = types.isin(CHANNEL_OF_TYPE)
    ol_keep, eye_keep = ol[keep], eye[keep.to_numpy()]
    rows = conn.index_of(ol_keep.bodyId.to_numpy())
    ok = rows >= 0
    rows, eye_keep = rows[ok], eye_keep[ok]
    channel = np.array(
        [CHANNEL_OF_TYPE[t] for t in ol_keep.type.fillna("unknown")]
    )[ok]

    gain = reg.require(
        "photoreceptor:all", "luminance_gain",
        units="mV per unit luminance",
        model_use="phototransduction: rendered luminance to membrane drive",
        subsystem="sensory_transduction", instances=int(rows.size),
        minimal=10.0,
        minimal_note="declared default photoreceptor gain",
        uncertainty="no calibration between rendered luminance and "
                    "photoreceptor membrane potential; fly photoreceptors are "
                    "GRADED, not spiking, which model family M v1 does not "
                    "represent at all",
    )
    baseline = reg.require(
        "photoreceptor:all", "dark_drive", units="mV",
        model_use="photoreceptor drive in darkness",
        subsystem="sensory_transduction", instances=int(rows.size),
        minimal=1.0, minimal_note="declared default dark drive",
    )

    # --- what this channel is not -------------------------------------------
    reg.provide(
        "photoreceptor:all", "retinotopy", None,
        units="ommatidium index",
        model_use="which ommatidium each photoreceptor looks through",
        status=Status.UNRESOLVED,
        evidence="male-cns:v1.0 gives photoreceptors no column, hex "
                 "coordinate or position (their only spatial annotation is the "
                 "lamina ROI), and optic-lobe:v1.1 carries no olHex "
                 "coordinates either. Assigning ommatidia arbitrarily would "
                 "give spatially structured input through a scrambled map",
        subsystem="sensory_transduction", instances=int(rows.size),
        uncertainty="without it there is no spatial vision: no motion, no "
                    "looming, no position. Only per-eye luminance",
    )
    reg.provide(
        "photoreceptor:dorsal rim", "polarisation_sensitivity", None,
        units="dimensionless",
        model_use="omitted from M v1",
        status=Status.UNRESOLVED,
        evidence="dorsal-rim R7d and R8d are polarisation sensitive; the "
                 "renderer produces luminance only",
        subsystem="sensory_transduction",
        instances=int(types.isin(["R7d", "R8d"]).sum()),
    )
    reg.provide(
        "photoreceptor:HBeyelet", "transduction_model", None,
        units="dimensionless",
        model_use="omitted from M v1",
        status=Status.UNRESOLVED,
        evidence="the Hofbauer-Buchner eyelet is extraretinal and circadian; "
                 "it does not look through an ommatidium, so the eye render "
                 "cannot drive it",
        subsystem="circadian",
        instances=int(types.isin(list(EXTRARETINAL)).sum()),
    )
    reg.provide(
        "photoreceptor:all", "count", int(rows.size), units="neurons",
        model_use="the population this channel drives",
        status=Status.MEASURED,
        evidence="male-cns:v1.0 superclass ol_sensory with a photoreceptor "
                 "type label. A fly has ~800 ommatidia per eye and six R1-R6 "
                 "each, about 9,600 R1-R6 in total; this graph holds 3,377, "
                 "so it does not contain one photoreceptor per ommatidium",
        subsystem="sensory_transduction", instances=int(rows.size),
        uncertainty="the reconstructed photoreceptor population is a subset "
                    "of the animal's",
    )

    every = max(1, int(round(1000.0 / sample_hz / timestep_ms)))
    reg.provide(
        "photoreceptor:all", "sampling_rate", sample_hz, units="Hz",
        model_use="how often the eyes are rendered",
        status=Status.ASSUMED,
        evidence=f"eyes rendered every {every} timesteps. Measured cost is "
                 "11.5 ms per readout, two 512x450 renders plus the hex "
                 "conversion",
        subsystem="sensory_transduction", instances=int(rows.size),
        uncertainty="fly photoreceptors respond well above 100 Hz; flicker "
                    "fusion is faster than this sampling rate",
    )

    return Vision(
        rows=rows.astype(np.int64), eye=eye_keep.astype(np.int64),
        channel=channel, gain_mv=gain, baseline_mv=baseline,
        n_neurons=conn.n, sample_every=every,
    )
