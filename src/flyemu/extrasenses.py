"""The remaining senses: taste, head touch, Johnston's organ, wing/haltere and
trunk proprioception, temperature change, and explicit zero-drive for
sensory neurons of unknown modality.

Channels select neurons by the sensory census organ (data/derived/
sensory_census.csv), so wiring and census cannot drift apart. Every gain and
every mapping is registered with its basis. Rules used here:

  taste (labellum)   tastant concentration of the food patch under the
                     labellum x per-type modality weight. Modality: LB3b/c
                     sugar, LB3a water, LB1a-d bitter, LB3d high salt, LB1e
                     amino acids (inferred: receptor-line projection matching,
                     male-CNS taste connectome, Cell 2026). Other taste types
                     respond weakly to every tastant (guessed).
  taste (leg, wing)  the same from tarsus-5 (or wing) contact with a food
                     patch; leg taste modality per type unknown, so all
                     tastants weakly (guessed).
  head touch         contact force on head-region bodies (BM_* bristles,
                     grooming bristles, taste-peg mechanosensors, pharyngeal
                     mechanosensors); phasic+tonic shape not modelled.
  Johnston's organ   a3 deflection proxy: gravity and wind projected on the
                     head's fore-aft axis (the body has no a2-a3 joint, so this
                     stands in for antennal mechanics; guessed stiffness).
                     C/E types alternate push/pull sign by type (guessed).
                     A/B (sound) see no sound source in the world.
  wing / haltere CS  |joint velocity| of the wing roll or haltere pitch joint
                     on the cell's side (guessed strain proxy).
  trunk proprio      abdominal / neck proprioceptors read |angle| of their
                     region's joints (guessed).
  thermo             phasic: hot cells max(0, dT/dt), cold cells max(0, -dT/dt)
                     of world temperature (inferred form, Budelli 2019).
  unknown            1,220+ cells with no identifiable modality get zero drive
                     (guessed: 'no stimulus'), and are otherwise simulated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd

from .registry import Registry, Status
from .world import World

REPO = Path(__file__).resolve().parents[2]
TASTANTS = ("sugar", "water", "bitter", "salt", "amino_acid")
LABELLAR_MODALITY = {"LB3b": "sugar", "LB3c": "sugar", "LB3a": "water",
                     "LB1a": "bitter", "LB1b": "bitter", "LB1c": "bitter", "LB1d": "bitter",
                     "LB3d": "salt", "LB1e": "amino_acid"}
HEAD_BODIES = ("c_head", "l_antenna", "r_antenna", "c_rostrum", "c_haustellum",
               "l_labrum", "r_labrum")


@dataclass
class FoodPatch:
    center: np.ndarray             # mm, on the ground (x, y)
    radius_mm: float
    tastants: dict                 # tastant -> concentration (M)


@dataclass
class Channel:
    name: str
    rows: np.ndarray
    side: np.ndarray               # 0 l, 1 r, 2 unknown
    weight: np.ndarray             # per cell: modality weight or push/pull sign
    extra: np.ndarray | None = None


@dataclass
class ExtraSenses:
    channels: dict
    gain: dict
    body_ids: dict
    joint_ids: dict
    n_neurons: int
    _last_temp: float | None = field(default=None, init=False)

    def _head_contact(self, m, d) -> dict:
        f = {k: 0.0 for k in HEAD_BODIES}
        ids = {v: k for k, v in self.body_ids.items() if k in HEAD_BODIES}
        c6 = np.zeros(6)
        for i in range(d.ncon):
            con = d.contact[i]
            for g in (con.geom1, con.geom2):
                b = int(m.geom_bodyid[g])
                if b in ids:
                    mj.mj_contactForce(m, d, i, c6)
                    f[ids[b]] += abs(c6[0])
        return f

    def drive(self, world: World, body, obs: dict, timestep_ms: float) -> np.ndarray:
        out = np.zeros(self.n_neurons, dtype=np.float32)
        m, d = body.sim.mj_model, body.sim.mj_data
        xpos = d.xpos

        def put(ch, val):
            out[ch.rows] = val.astype(np.float32)

        # --- taste ------------------------------------------------------------
        def tastants_at(p, touching):
            c = np.zeros(len(TASTANTS))
            if not touching:
                return c
            for fp in world.food:
                if np.linalg.norm(p[:2] - fp.center[:2]) <= fp.radius_mm:
                    c += np.array([fp.tastants.get(t, 0.0) for t in TASTANTS])
            return c

        hc = self._head_contact(m, d)
        if "taste_labellar" in self.channels:
            ch = self.channels["taste_labellar"]
            lab = [tastants_at(xpos[self.body_ids[f"{s}_labrum"]],
                               hc[f"{s}_labrum"] > 0 or hc["c_haustellum"] > 0) for s in "lr"]
            conc = np.where(ch.side[:, None] == 1, lab[1], lab[0])
            sat = conc / (conc + self.gain["taste_K"])
            put(ch, self.gain["taste"] * (sat * ch.extra).sum(1))
        if "taste_leg" in self.channels:
            ch = self.channels["taste_leg"]
            cf = np.linalg.norm(obs["contact_forces"], axis=-1)      # (n_contact_segments,)
            per_leg = []
            for leg in ("lf", "lm", "lh", "rf", "rm", "rh"):
                j = body.contact_names.index(f"{leg}_tarsus5")
                per_leg.append(tastants_at(xpos[self.body_ids[f"{leg}_tarsus5"]], cf[j] > 0))
            per_leg = np.array(per_leg)
            conc = np.where(ch.side[:, None] < 6, per_leg[np.clip(ch.side, 0, 5)],
                            per_leg.mean(0))
            sat = conc / (conc + self.gain["taste_K"])
            put(ch, self.gain["taste"] * (sat * ch.extra).sum(1))

        # --- leg touch not covered by sensory.py (subclass 'leg') -------------
        if "leg_touch" in self.channels:
            ch = self.channels["leg_touch"]
            cf = np.linalg.norm(obs["contact_forces"], axis=-1)
            per_leg = np.array([sum(cf[j] for j, nm in enumerate(body.contact_names) if nm.startswith(leg))
                                for leg in ("lf", "lm", "lh", "rf", "rm", "rh")])
            f = np.where(ch.side < 6, per_leg[np.clip(ch.side, 0, 5)], per_leg.mean())
            put(ch, self.gain["mech"] * np.tanh(f))

        # --- head touch -------------------------------------------------------
        if "head_touch" in self.channels:
            ch = self.channels["head_touch"]
            tot = sum(hc.values())
            put(ch, self.gain["mech"] * np.tanh(np.full(len(ch.rows), tot)))

        # --- Johnston's organ ---------------------------------------------------
        if "jo" in self.channels:
            ch = self.channels["jo"]
            R = d.xmat[self.body_ids["c_head"]].reshape(3, 3)
            fwd = R[:, 0]
            g = np.array([0, 0, -1.0])
            theta = self.gain["jo_gravity"] * float(g @ fwd) + \
                self.gain["jo_wind"] * float(np.asarray(world.wind_mm_s) @ fwd)
            put(ch, self.gain["mech"] * np.tanh(ch.weight * theta))

        # --- wing / haltere campaniforms ---------------------------------------
        jv = obs["joint_velocities"]
        for name in ("wing_cs", "haltere_cs"):
            if name in self.channels:
                ch = self.channels[name]
                jl, jr = self.joint_ids[name]
                v = np.where(ch.side == 1, abs(jv[jr]), abs(jv[jl]))
                put(ch, self.gain["mech"] * np.tanh(v / self.gain["cs_omega"]))

        # --- trunk proprioception ----------------------------------------------
        ja = obs["joint_angles"]
        for name in ("abdomen_proprio", "neck_proprio"):
            if name in self.channels:
                ch = self.channels[name]
                a = float(np.abs(ja[self.joint_ids[name]]).mean())
                put(ch, self.gain["mech"] * np.tanh(np.full(len(ch.rows), a)))

        # --- temperature change -------------------------------------------------
        if "thermo" in self.channels:
            ch = self.channels["thermo"]
            T = world.temperature_c
            dTdt = 0.0 if self._last_temp is None else (T - self._last_temp) / (timestep_ms / 1000.0)
            self._last_temp = T
            put(ch, self.gain["thermo"] * np.maximum(0.0, ch.weight * dTdt))
        return out


def build(reg: Registry, conn, body) -> ExtraSenses:
    cen = pd.read_csv(REPO / "data" / "derived" / "sensory_census.csv")
    n = conn.neurons.reset_index(drop=True)
    t = n.type.fillna("")
    grp = np.where(t == "", "untyped:" + n["class"].fillna("?") + "/" + n.subclass.fillna("?"), t)
    organ_of = dict(zip(cen.group, cen.organ))
    organ = pd.Series(grp).map(organ_of).fillna("").to_numpy()
    side_s = n.instance.fillna("").str.extract(r"_([LR])$")[0].map({"L": 0, "R": 1}).fillna(2).astype(int).to_numpy()

    m = body.sim.mj_model
    bid = {m.body(i).name.split("/")[-1]: i for i in range(m.nbody)}
    jnames = [m.joint(i).name.split("/")[-1] for i in range(m.njnt)]
    # joint_angles from flygym are over actuated/free joints in order of the fly's
    # jointdofs; map by name through the body helper
    dof_names = [getattr(j, "name", str(j)) for j in body.fly.get_jointdofs_order()]

    def jidx(fragment):
        if dof_names is None:
            return []
        return [i for i, x in enumerate(dof_names) if fragment in x]

    def g(key, units, val, note):
        return reg.require(f"sense:{key}", "gain", units=units, model_use=f"{key} transduction",
                           subsystem="sensory_transduction", instances=1, minimal=val,
                           minimal_note=note)

    gain = dict(
        taste=g("taste", "mV", 15.0, "guessed taste GRN drive at saturation"),
        taste_K=g("taste_K", "M", 0.05, "guessed half-saturation for all tastants"),
        mech=g("mechano_extra", "mV", 8.0, "guessed; same as leg afferent gain"),
        jo_gravity=g("jo_gravity", "rad per g", 0.3, "guessed a3 sag per unit gravity along the head axis"),
        jo_wind=g("jo_wind", "rad per mm/s", 1e-4, "guessed a3 deflection per unit wind"),
        cs_omega=g("cs_omega", "rad/s", 50.0, "guessed velocity scale of wing/haltere strain"),
        thermo=g("thermo", "mV per degC/s", 5.0, "guessed phasic temperature gain"),
    )

    channels, joint_ids = {}, {}

    def add(name, mask, weight=None, extra=None, side=None, basis=Status.GUESSED, why=""):
        idx = np.flatnonzero(mask)
        rows = conn.index_of(n.bodyId.to_numpy()[idx])
        ok = rows >= 0
        if not ok.any():
            return
        channels[name] = Channel(name, rows[ok].astype(np.int64),
                                 (side_s if side is None else side)[idx][ok],
                                 np.ones(ok.sum()) if weight is None else np.asarray(weight)[idx][ok],
                                 None if extra is None else np.asarray(extra)[idx][ok])
        reg.provide(f"sense:{name}", "transduction", "extrasenses.py", units="dimensionless",
                    model_use="physical variable -> afferent drive", status=basis,
                    subsystem="sensory_transduction", instances=int(ok.sum()),
                    evidence=why, uncertainty="gains guessed; see module docstring",
                    method="census organ selection")

    # taste
    lab = organ == "labellum / pharynx"
    w = np.full((len(n), len(TASTANTS)), 0.2)
    for ty, mod in LABELLAR_MODALITY.items():
        sel = t.eq(ty).to_numpy()
        w[sel] = 0.0
        w[sel, TASTANTS.index(mod)] = 1.0
    add("taste_labellar", lab, extra=w, basis=Status.INFERRED,
        why="labellar GRN modality by receptor-line projection matching (male-CNS taste "
            "connectome, Cell 2026); other labellar/pharyngeal types weak to all (guessed)")
    legtaste = organ == "leg / wing taste bristle"
    try:
        from .sensory import leg_from_roiinfo
        roi = pd.read_parquet(REPO / "data" / "cache" / "male_cns_sensorimotor_roiinfo.parquet")
        roi_leg = dict(zip(roi.bodyId, roi.roiInfo.map(leg_from_roiinfo)))
    except Exception:
        roi_leg = {}
    legs = ["lf", "lm", "lh", "rf", "rm", "rh"]
    lside = np.array([legs.index(roi_leg[b]) if roi_leg.get(b) in legs else 6 for b in n.bodyId])
    add("taste_leg", legtaste, extra=np.full((len(n), len(TASTANTS)), 0.2), side=lside,
        basis=Status.GUESSED, why="leg/wing taste modality per type unknown: weak response to "
                                  "every tastant; leg from dominant leg neuropil (derived)")
    # leg touch bristles in subclass 'leg' (not driven by sensory.py)
    sub = n.subclass.fillna("").to_numpy()
    legtouch = (organ == "mechanosensory bristle") & (sub != "mechanosensory bristle")
    add("leg_touch", legtouch, side=lside, basis=Status.INFERRED,
        why="leg tactile bristle neurons respond to contact (Walker 2000); contact force on "
            "their own leg's tarsi (leg from dominant leg neuropil, derived); gain guessed")
    # head touch
    head = np.isin(organ, ["head bristle (BM_*: interommatidial, vibrissae, palp, haustellum, occipital)",
                           "grooming-relevant bristles (head)", "taste peg mechanosensory neuron",
                           "pharyngeal mechanosensor"])
    add("head_touch", head, basis=Status.INFERRED,
        why="head bristle and taste-peg mechanosensors respond to contact (Hampel 2015; Eichler "
            "head bristle atlas); total head-region contact force (derived), gain guessed")
    # JO
    jo = np.isin(organ, ["Johnston's organ C/E", "Johnston's organ"])
    types_sorted = sorted(pd.unique(t[jo]))
    sign = np.array([1.0 if (ty in types_sorted and types_sorted.index(ty) % 2 == 0) else -1.0 for ty in t])
    add("jo", jo, weight=sign, basis=Status.GUESSED,
        why="JO-C/E respond to sustained a3 deflection, anterior vs posterior cells opposite "
            "(Kamikouchi 2009; Yorozu 2009); per-type push/pull unknown (alternating, guessed); "
            "deflection from gravity/wind along head axis (proxy, no a2-a3 joint)")
    # wing / haltere CS
    for name, org_name, frag in (("wing_cs", "wing campaniforms / tegula", "wing-roll"),
                                 ("haltere_cs", "haltere campaniforms", "haltere-pitch")):
        jl, jr = jidx(f"l_{frag}"), jidx(f"r_{frag}")
        if jl and jr:
            joint_ids[name] = (jl[0], jr[0])
            add(name, organ == org_name, basis=Status.GUESSED,
                why="wing/haltere campaniforms encode strain during the beat (Dickinson 1999; "
                    "Dickerson 2014); |joint velocity| proxy guessed")
    for name, org_name, frag in (("abdomen_proprio", "abdominal proprioceptor", "abdomen"),
                                 ("neck_proprio", "neck / notum proprioceptor", "c_thorax-c_head")):
        ids = jidx(frag)
        if ids:
            joint_ids[name] = ids
            add(name, organ == org_name, basis=Status.GUESSED,
                why="trunk proprioceptors read their region's joint angles (proxy, guessed)")
    thermo = t.isin(["TRN_VP2", "TRN_VP3a", "TRN_VP3b", "HRN_VP1l", "HRN_VP1d"]).to_numpy()
    tw = np.where(t.eq("TRN_VP2").to_numpy(), 1.0, -1.0)
    add("thermo", thermo, weight=tw, basis=Status.INFERRED,
        why="arista hot (VP2) and cool (VP3, VP1l putative) cells are phasic, driven by dT/dt "
            "(Gallio 2011; Budelli 2019); gain guessed")
    # explicit zero drive for unknown-modality sensory neurons
    unk = np.isin(organ, ["abdominal sensory", "sensory, modality unknown", "unassigned",
                          "body chemosensor", "mechanosensor, organ unassigned",
                          "leg proprioceptor, organ unassigned"])
    reg.provide("sense:unknown_modality", "drive", 0.0, units="mV",
                model_use="sensory neurons whose modality cannot be identified",
                status=Status.GUESSED, subsystem="sensory_transduction",
                instances=int(unk.sum()),
                evidence="no identifiable stimulus: simulated as neurons with zero sensory "
                         "drive; FOR ITERATION when their modality is identified")

    return ExtraSenses(channels=channels, gain=gain, body_ids=bid, joint_ids=joint_ids,
                       n_neurons=conn.n)
