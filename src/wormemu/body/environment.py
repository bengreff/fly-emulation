"""The plate the worm lives on (audit row 22, wbody, night of 6 Nov 2026): food lawn, O2 and CO2 fields, a salt
plug, a temperature gradient, the experimenter's touches and taps, and the medium.

The world reaches the brain only through BodyToBrain (INTERFACE.md) and so only through the sensory modules of row
17: this module writes the head / tail channel dicts, contact_force_uN, nose_force_uN and tap, nothing else.

Plate coordinates (mm, the plate plane; the worm lies on its side, so the plate normal is the lateral axis of the
rest frame, scene.LATERAL_AXIS): origin at the nose's rest position, a = forward (the rest frame's -z), b = dorsal
(+x). Body.observe passes the nose, the tail tip and the 49 midline samples in these coordinates.

Fields (each a toggle; the nested form is the INTERFACE.md default plate, uniform, so Environment(all uniform) gives
exactly env=None):
- food (env_food "lawn" | "off"): a bordered OP50 lawn, a disk of radius lawn_radius_mm with a thicker rim (Gray et
  al. 2004: bacteria pile up at the border), density B(x) in OD units; food_OD at the head = B.
- O2 (env_o2 "demir2020" | "uniform"): Demir et al. 2020 eLife 9:e52781 eq 2, dO/dt = D_O lap O + f (O_am - O) - sink,
  O in % of air, D_O 2e-5 cm^2/s and f 0.65 1/s as published. Their sink is k_c W with W the worm density (bacteria
  taken proportional to worms); with one worm and a lawn the sink is the lawn's: q_b * B / B_lawn (inferred structure,
  q_b guessed), clipped at O = 0 (respiration stops without O2). Solved on a grid (explicit, env_dt_s steps) from
  its steady state; a scheduled ambient change (e.g. 21 -> 7 %, Zimmer et al. 2009) relaxes with 1/f.
  The rim's length scale sqrt(D_O / f) = 55 um (derived) is resolved by the 50 um grid.
- CO2 (env_co2 "lawn" | "uniform"): the same equation for CO2 with D 1.9e-5 cm^2/s (water, measured), the same f
  (inferred) and a source RQ * (S_O2 / S_CO2) * the O2 sink (respiratory quotient guessed 1; the Henry's-law
  solubility ratio converts moles of O2 used into the CO2 partial-pressure rise, derived).
- salt (env_salt "plug" | "uniform"): NGM background 50 mM plus a plug spread by 2D diffusion for plug_age_h,
  C = bg + A exp(-r^2 / (4 D t)) (point source; inferred geometry), D(NaCl) 1.6e-3 mm^2/s (water, measured).
- temperature (env_temp "gradient" | "uniform"): linear, T = T0 + g a along the forward axis (thermotaxis plates use
  0.5 C/cm, 0.18-1.5 in published protocols; Wang et al. 2013, Yeon et al. 2023, opened; protocol value).
- events (the experimenter, `events` list): ("tap", t_s, uN) one-exchange impulse on obs.tap; ("eyelash", t0_s,
  t1_s, s_centre, uN) a normal force spread over the midline samples within eyelash_halfwidth of s_centre;
  ("nose", t0_s, t1_s, uN) axial force on the nose; ("o2_ambient", t_s, pct) a step in O_am.
- medium: MEDIA, world flags for Body (driver flags). agar_film is the template (RFT, ct 3.2, cn 128 Pa s, the
  agar groove); water and viscous are Newtonian RFT with ct, cn scaled by viscosity. A viscoelastic (Maxwell)
  medium is not in the driver (Open).
"""
from __future__ import annotations

import numpy as np

from wormemu.mech.senses_base import spec

MECHANISMS = [
    ("env_food", "World: bordered bacterial lawn (food_OD at the head)", "world", "lawn"),
    ("env_o2", "World: O2 field, Demir et al. 2020 reaction-diffusion with the lawn's consumption", "world",
     "demir2020"),
    ("env_co2", "World: CO2 field from the lawn's respiration (same equation)", "world", "lawn"),
    ("env_salt", "World: NaCl plug spreading by diffusion on the NGM background", "world", "plug"),
    ("env_temp", "World: linear temperature gradient", "world", "gradient"),
    ("env_events", "World: experimenter taps, eyelash and nose touches, O2 steps", "world", "schedule"),
    ("env_medium", "World: the medium (agar film, water, viscous) as body-driver flags", "world", "agar_film"),
]
DEMIR = "Demir et al. 2020 eLife 9:e52781, Methods eq 2 (read 6 Nov 2026)"
SPECS = [
    spec("lawn_radius_mm", "env_food", "mm", 5.0, 2.0, 15.0, "guessed",
         "none opened: a 20-50 uL OP50 spot spreads to ~1 cm",
         notes="opened 9 Nov 2026: '40 uL drops, which spread to a diameter of 11.2 mm on average' (Madirolas et "
               "al. 2023 Commun Biol, PMC10425387, methods): radius 5.6 mm (derived), inside the range. The template "
               "stays 5.0 until a battery runs on 5.6 (the vitals plate uses this lawn)"),
    spec("lawn_od", "env_food", "OD600", 1.0, 0.1, 10.0, "guessed", "none opened: lawn interior bacterial density",
         notes="the seeded culture, not the grown lawn, is what papers give: OD 0.5 (Madirolas et al. 2023 Commun "
               "Biol, PMC10425387, methods, opened 9 Nov 2026); no lawn density after growth found"),
    spec("lawn_rim_ratio", "env_food", "1", 2.0, 1.0, 5.0, "guessed",
         "Gray et al. 2004 Nature 430:317 (bacteria thicker at the border; ratio not read)"),
    spec("lawn_rim_width_mm", "env_food", "mm", 0.5, 0.1, 1.0, "guessed", "none opened"),
    spec("lawn_edge_ahead_mm", "env_food", "mm", -2.0, -5.0, 10.0, "guessed",
         "placement: the lawn edge this far ahead of the nose; negative = the worm starts on food (template: the "
         "head 2 mm inside the edge, the worm on its culture lawn)"),
    spec("o2_D_cm2_s", "env_o2", "cm^2/s", 2e-5, 1.9e-5, 2.1e-5, "published_fit", DEMIR),
    spec("o2_f_per_s", "env_o2", "1/s", 0.65, 0.3, 1.0, "published_fit", DEMIR + " (air-to-surface penetration)"),
    spec("o2_ambient_pct", "env_o2", "%", 21.0, 0.0, 21.0, "measured", "air"),
    spec("o2_lawn_sink_pct_s", "env_o2", "%/s", 7.0, 0.5, 13.65, "guessed",
         "none opened: q_b; steady interior O2 = O_am - q_b / f = 10 % at the template; range from a 1 % drop to "
         "full depletion (Demir 2020 measured < 0.1 % in a bacterial suspension)",
         notes="the paper that would pin it: an O2 microsensor profile across an OP50 lawn on NGM"),
    spec("co2_D_cm2_s", "env_co2", "cm^2/s", 1.9e-5, 1.6e-5, 2.0e-5, "measured", "CO2 in water at 25 C"),
    spec("co2_ambient_pct", "env_co2", "%", 0.04, 0.03, 0.05, "measured", "air"),
    spec("co2_rq", "env_co2", "1", 1.0, 0.7, 1.2, "guessed", "respiratory quotient of aerobic E. coli (none opened)",
         notes="searched 9 Nov 2026, none measured free for E. coli on peptone or in a lawn. Proxy only: in a glucose "
               "chemostat 'the RQ decreased from 1.5 to 0.7 during the first 50 s of the feast phase, and increased "
               "back to the initial value after approximately 200 s' (Vasilakou, van Loosdrecht & Wahl 2020 Microb "
               "Cell Fact, PMC7260802, results), a transient, not a steady RQ. Andersen & von Meyenburg 1980 (J "
               "Bacteriol, PMC294601) is a scan; no RQ read from it"),
    spec("co2_o2_solubility_ratio", "env_co2", "1", 0.039, 0.035, 0.045, "derived",
         "Henry's law at 25 C: O2 1.3 mM/atm over CO2 33.4 mM/atm (measured constants); converts the O2 drop in % "
         "of an atmosphere into the CO2 rise for the same moles"),
    spec("salt_bg_mM", "env_salt", "mM", 50.0, 0.0, 100.0, "measured", "NGM recipe (~51 mM NaCl)"),
    spec("salt_plug_excess_mM", "env_salt", "mM", 50.0, 0.0, 100.0, "guessed",
         "Kunitomo and Iino 2013 (secondary): 100 mM plug; the excess at the centre after spreading not read",
         notes="opened protocols (9 Nov 2026), not this geometry: a 9 cm plate with a gradient of ~35 to ~95 mM "
               "(Suwazono et al. 2025 Genes Cells, PMC12120540, methods, citing Kunitomo et al. 2013); two 14.5 mm "
               "agar blocks of 0 and 150 mM on an NaCl-free 8.5 cm plate (Park et al. 2021 eLife, PMC7834019, "
               "methods). Kunitomo's 60 mM span fits inside this range; Park's 150 mM block is above its 100 mM top at the "
               "block itself (the spread profile after 18-20 h is not reported)"),
    spec("salt_D_mm2_s", "env_salt", "mm^2/s", 1.6e-3, 1.2e-3, 1.6e-3, "measured", "NaCl in water at 25 C"),
    spec("salt_plug_age_h", "env_salt", "h", 12.0, 1.0, 24.0, "guessed", "overnight plug (protocol, secondary)",
         notes="opened: the blocks 'were removed after 18 to 20 hr, just before assay' (Park et al. 2021 eLife, "
               "PMC7834019, methods; two-block geometry), inside this range (9 Nov 2026)"),
    spec("salt_plug_ahead_mm", "env_salt", "mm", 10.0, 0.0, 40.0, "guessed", "placement: plug centre ahead of nose"),
    spec("temp_T0_C", "env_temp", "C", 20.0, 15.0, 25.0, "measured", "protocol: cultivation temperature at start"),
    spec("temp_grad_C_per_cm", "env_temp", "C/cm", 0.5, 0.18, 1.5, "measured",
         "protocol: 'linear thermal gradients of 0.5, 1.0, and 1.5 [deg]C/cm' (Wang, O'Halloran, Goodman & Arshavsky "
         "2013 J Gen Physiol 142:437, PMC3787776, methods, opened; the catalog's source); 23-28 C at 0.5 C/cm on 10 cm "
         "plates (Yeon et al. 2023 G3, PMC10542565, methods, opened)",
         notes="range: 0.18 C/cm low edge from 19-23 C on a 22.5 cm plate (Chen, Harris & Sengupta 2024 microPubl "
               "Biol, PMC11603155, methods, opened; derived, if linear), 1.5 high edge Wang 2013's steepest. Not "
               "used for the range: a radial 17-25 C over a 9 cm plate's 4.5 cm radius, mean 1.78 C/cm (Mohri et "
               "al. 2005 Genetics, PMC1449549, opened; derived, not linear). Yeon 2023's figure legends say 0.05 "
               "C/cm, which their methods' 5 C over 10 cm contradicts. Was 0.1-2.0 citing Hedgecock and Russell "
               "1975 and Luo et al. 2014, neither opened (re-sourced 9 Nov 2026)"),
    spec("eyelash_halfwidth", "env_events", "body length", 0.03, 0.01, 0.1, "inferred",
         "an eyelash tip is ~50 um wide (half width 0.025-0.03 of a 1 mm body)"),
    spec("eyelash_force_uN", "env_events", "uN", 26.0, 3.8, 177.0, "measured",
         "the force people deliver in the classical touch assay: 'the median force from all trials was 26 uN', mean "
         "61 uN, log-normal, coefficient of variation 1.7 (Nekimken, Mazzochette, Goodman & Pruitt 2017 PLoS ONE, "
         "PMC5438190, results, opened 9 Nov 2026; volunteers with eyebrow hairs on a calibrated cantilever)",
         notes="range 3.8-177 uN: the 5-95 % of one log-normal with median 26 and CV 1.7 (sigma 1.166, derived; it "
               "implies a mean of 51 uN against the reported 61, so one log-normal is approximate). "
               "The response saturates near 2 uN (catalog env_touch_saturation_uN); the assay force is over ten "
               "times that (the paper's point). Was 2 (0.1-10, guessed). No default run uses it: the vitals "
               "battery has no events; standard_events (wbody_loop_check --env=standard) does"),
    spec("tap_uN", "env_events", "uN", 5.0, 0.5, 50.0, "guessed", "none opened (Rankin et al. 1990 tapper)"),
    spec("nose_force_uN", "env_events", "uN", 2.0, 0.1, 10.0, "guessed", "none opened (Kaplan and Horvitz 1993)",
         notes="searched 9 Nov 2026, no nose-touch force measured free. Kaplan & Horvitz 1993 (PMC46059) is a scan; "
               "the behavioural assay is the worm moving 'forward into an eyelash in the path of the worm' and the "
               "imaging stimulus is a displacement: a probe 'moved toward the worm so that it could probe ~8 um into "
               "the side of the worm's nose' for 1 s (Chatzigeorgiou & Schafer 2011 Neuron, PMC3145979, methods). "
               "A force from it needs the head's indentation stiffness (Park, Goodman & Pruitt 2007 PNAS, "
               "PMC2077264: force-displacement linear; full text not in PMC's XML, no number read)"),
    spec("viscosity_mPa_s", "env_medium", "mPa s", 1.0, 0.9, 28000.0, "measured",
         "water at 20 C; Fang-Yen et al. 2010 PNAS 107:20323 used up to ~28 Pa s"),
]
P = {s.id: s.template for s in SPECS}
DEFAULTS = {m[0]: m[3] for m in MECHANISMS}
UNIFORM = {"env_food": "off", "env_o2": "uniform", "env_co2": "uniform", "env_salt": "uniform",
           "env_temp": "uniform", "env_events": "none", "env_medium": "agar_film"}
# RFT drag coefficients per unit length (Pa s) for water as the driver uses them; Newtonian media scale with viscosity.
WATER_CT, WATER_CN = 0.00357, 0.005675
MEDIA = {
    "agar_film": {"scale": "worm_1mm", "fluid": "agar_rft", "substrate": "agar_film"},
    "agar_plate": {"scale": "worm_1mm", "fluid": "agar_rft", "substrate": "agar_plate"},
    "water": {"scale": "worm_1mm", "fluid": "viscous_rft_water", "substrate": "none_published"},
    "published": {},
}


def medium(name: str = "agar_film", viscosity_mPa_s: float | None = None) -> dict:
    """Body world flags for a medium; "viscous" = water's RFT coefficients times viscosity / 1 mPa s."""
    if name == "viscous":
        mu = (viscosity_mPa_s or P["viscosity_mPa_s"]) / 1.0
        return {**MEDIA["water"], "ct": WATER_CT * mu, "cn": WATER_CN * mu}
    return dict(MEDIA[name])


class Grid:
    """dX/dt = D lap X + f (X_am - X) + src, on a square grid (mm, s), zero-flux edges, explicit steps."""

    def __init__(self, x0, n, dx, D_mm2_s, f, amb, src):
        self.x0, self.n, self.dx, self.D, self.f, self.src = np.asarray(x0, float), n, dx, D_mm2_s, f, src
        self.amb = amb
        self.X = np.full((n, n), float(amb))
        self.h = 0.2 * dx * dx / D_mm2_s                      # max explicit step (stability 0.25 dx^2 / D)

    def step(self, dt_s):
        k = max(1, int(np.ceil(dt_s / self.h)))
        h = dt_s / k
        for _ in range(k):
            Xp = np.pad(self.X, 1, mode="edge")
            lap = (Xp[2:, 1:-1] + Xp[:-2, 1:-1] + Xp[1:-1, 2:] + Xp[1:-1, :-2] - 4 * self.X) / self.dx ** 2
            self.X = np.maximum(self.X + h * (self.D * lap + self.f * (self.amb - self.X) + self.src(self.X)), 0.0)

    def at(self, pts):
        """Bilinear sample at points [m, 2] (a, b) mm."""
        u = (np.atleast_2d(pts) - self.x0) / self.dx
        u = np.clip(u, 0, self.n - 1.000001)
        i, j = u[:, 0].astype(int), u[:, 1].astype(int)
        fi, fj = u[:, 0] - i, u[:, 1] - j
        X = self.X
        return ((1 - fi) * (1 - fj) * X[i, j] + fi * (1 - fj) * X[i + 1, j] + (1 - fi) * fj * X[i, j + 1]
                + fi * fj * X[i + 1, j + 1])


class Environment:
    def __init__(self, toggles: dict | None = None, params: dict | None = None, events: list | None = None,
                 dx_mm: float = 0.05, dt_s: float = 0.1):
        self.tog = {**DEFAULTS, **(toggles or {})}
        self.p = {**P, **(params or {})}
        self.events = list(events or []) if self.tog["env_events"] != "none" else []
        self.dt_s = dt_s
        p = self.p
        self.lawn_c = np.array([p["lawn_edge_ahead_mm"] + p["lawn_radius_mm"], 0.0])
        self.o2 = self.co2 = None
        self.o2_amb = p["o2_ambient_pct"]
        if self.tog["env_food"] == "lawn" and (self.tog["env_o2"] == "demir2020" or self.tog["env_co2"] == "lawn"):
            half = p["lawn_radius_mm"] + 2.0
            n = int(round(2 * half / dx_mm)) + 1
            x0 = self.lawn_c - half
            a = x0[0] + dx_mm * np.arange(n)
            b = x0[1] + dx_mm * np.arange(n)
            Bg = self.lawn(np.stack(np.meshgrid(a, b, indexing="ij"), -1).reshape(-1, 2)).reshape(n, n)
            rel = Bg / p["lawn_od"]
            q = p["o2_lawn_sink_pct_s"]
            self.o2 = Grid(x0, n, dx_mm, p["o2_D_cm2_s"] * 100, p["o2_f_per_s"], self.o2_amb,
                           lambda X: -q * rel * (X > 0))
            if self.tog["env_o2"] == "uniform":
                self.o2.src = lambda X: 0.0 * X
            if self.tog["env_co2"] == "lawn":
                o2 = self.o2
                self.co2 = Grid(x0, n, dx_mm, p["co2_D_cm2_s"] * 100, p["o2_f_per_s"], p["co2_ambient_pct"],
                                lambda X: p["co2_rq"] * p["co2_o2_solubility_ratio"] * q * rel * (o2.X > 0))
            for _ in range(int(30.0 / dt_s)):                 # 30 s = 20 / f: the steady state
                self._advance_fields(dt_s)
        self.t_field_s = 0.0
        self._fired = set()

    # --- fields ---------------------------------------------------------------------------------------------------
    def lawn(self, pts):
        """Bacterial density (OD) at points [m, 2]: the interior plus a rim rising toward the edge."""
        if self.tog["env_food"] != "lawn":
            return np.zeros(len(np.atleast_2d(pts)))
        p = self.p
        r = np.linalg.norm(np.atleast_2d(pts) - self.lawn_c, axis=1)
        d = p["lawn_radius_mm"] - r                            # depth inside the lawn
        rim = 1.0 + (p["lawn_rim_ratio"] - 1.0) * np.exp(-np.maximum(d, 0) / p["lawn_rim_width_mm"])
        return np.where(d >= 0, p["lawn_od"] * rim, 0.0)

    def salt(self, pts):
        p = self.p
        if self.tog["env_salt"] != "plug":
            return np.full(len(np.atleast_2d(pts)), p["salt_bg_mM"])
        r2 = np.sum((np.atleast_2d(pts) - np.array([p["salt_plug_ahead_mm"], 0.0])) ** 2, axis=1)
        age = p["salt_plug_age_h"] * 3600.0 + self.t_field_s
        return p["salt_bg_mM"] + p["salt_plug_excess_mM"] * np.exp(-r2 / (4 * p["salt_D_mm2_s"] * age))

    def temperature(self, pts):
        p = self.p
        g = p["temp_grad_C_per_cm"] / 10.0 if self.tog["env_temp"] == "gradient" else 0.0
        return p["temp_T0_C"] + g * np.atleast_2d(pts)[:, 0]

    def _advance_fields(self, dt_s):
        if self.o2 is not None:
            self.o2.amb = self.o2_amb
            self.o2.step(dt_s)
        if self.co2 is not None:
            self.co2.step(dt_s)

    def o2_at(self, pts):
        if self.o2 is None or self.tog["env_o2"] != "demir2020":
            return np.full(len(np.atleast_2d(pts)), self.o2_amb)
        return self.o2.at(pts)

    def co2_at(self, pts):
        if self.co2 is None:
            return np.full(len(np.atleast_2d(pts)), self.p["co2_ambient_pct"])
        return self.co2.at(pts)

    # --- one exchange ---------------------------------------------------------------------------------------------
    def sample(self, t_ms: float, head_ab, tail_ab, s, mid_ab=None) -> dict:
        """BodyToBrain fields for this exchange: head, tail (channel dicts, only the channels of the fields that are
        on), contact_force_uN [len(s)], nose_force_uN, tap."""
        t_s = t_ms / 1000.0
        while self.t_field_s + self.dt_s <= t_s + 1e-12:
            self.t_field_s += self.dt_s
            for e in self.events:                            # O2 steps take effect on the field clock
                if e[0] == "o2_ambient" and self.t_field_s >= e[1]:
                    self.o2_amb = float(e[2])
            self._advance_fields(self.dt_s)
        pts = np.array([head_ab, tail_ab], float)
        tg, head, tail = self.tog, {}, {}                  # only the channels of fields that are on (the uniform
        if tg["env_food"] == "lawn":                       # forms leave the scene's / default plate's value)
            head["food_OD"] = float(self.lawn(pts[:1])[0])
        if tg["env_o2"] == "demir2020" or self.o2_amb != self.p["o2_ambient_pct"]:
            head["o2_pct"] = float(self.o2_at(pts[:1])[0])
        if self.co2 is not None:
            head["co2_pct"] = float(self.co2_at(pts[:1])[0])
        if tg["env_salt"] == "plug":
            head["nacl_mM"], tail["nacl_mM"] = (float(x) for x in self.salt(pts))
        if tg["env_temp"] == "gradient":
            head["temperature_C"] = float(self.temperature(pts[:1])[0])
        F = np.zeros(len(s))
        nose = tap = 0.0
        for k, e in enumerate(self.events):
            kind = e[0]
            if kind == "tap" and k not in self._fired and t_s >= e[1]:
                tap += float(e[2])
                self._fired.add(k)
            elif kind == "eyelash" and e[1] <= t_s < e[2]:
                sel = np.abs(np.asarray(s) - e[3]) <= self.p["eyelash_halfwidth"]
                if sel.any():
                    F[sel] += float(e[4]) / sel.sum()
            elif kind == "nose" and e[1] <= t_s < e[2]:
                nose += float(e[3])
        return dict(head=head, tail=tail, contact_force_uN=F, nose_force_uN=nose, tap=tap)


def standard_events(p=P):
    """The everything-on check's stimulus schedule: a tap at 3 s, anterior and posterior eyelash touches at 5 s and
    7 s (0.3 s each), a nose touch at 8.5 s (0.3 s)."""
    return [("tap", 3.0, p["tap_uN"]), ("eyelash", 5.0, 5.3, 0.25, p["eyelash_force_uN"]),
            ("eyelash", 7.0, 7.3, 0.8, p["eyelash_force_uN"]), ("nose", 8.5, 8.8, p["nose_force_uN"])]
