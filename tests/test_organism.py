"""Meaning-based checks on the whole-organism model.

These are not coverage tests. Each one encodes a way the model could look
correct while being wrong, of the kind that cost session 1 two reversed
conclusions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

CACHE = REPO / "data" / "cache"
HAVE_GRAPH = (CACHE / "male_cns_edges.parquet").exists() and (
    CACHE / "male_cns_neurons.parquet"
).exists()
needs_graph = pytest.mark.skipif(
    not HAVE_GRAPH, reason="run scripts/fetch_male_cns.py first"
)


# --- body units ----------------------------------------------------------

def test_the_fly_weighs_about_ten_micronewtons():
    """Model units must be mm/s/g, or every torque number is meaningless.

    The body model is unit-agnostic, so nothing in it declares that a torque of
    1.0 means 1 uN*mm. This pins it: a real fly is about 1 mg, so its weight in
    the model's own force unit has to come out near 10.
    """
    from flyemu.body import Body

    b = Body()
    m = b.sim.mj_model
    mass = float(m.body_mass.sum())
    g = abs(float(m.opt.gravity[2]))
    weight = mass * g
    assert 0.5 < mass * 1e3 < 2.0, f"fly mass is {mass * 1e3:.2f} mg, expected ~1"
    assert 5.0 < weight < 20.0, f"fly weight is {weight:.1f} force units, expected ~10"


def test_a_silent_network_produces_no_torque():
    """Muscle activation must come only from spikes.

    If the motor interface leaked any resting drive, the body would move on its
    own and every behavioural result would be measuring the leak.
    """
    from flyemu.neuromuscular import Neuromuscular

    nm = Neuromuscular(
        adhesion_index=np.array([], dtype=np.int64),
        adhesion_rows=np.array([], dtype=np.int64),
        n_adhesion=0,
        mn_index=np.array([0, 1]), actuator_index=np.array([0, 1]),
        drive_sign=np.array([1.0, -1.0], dtype=np.float32),
        force_per_spike=np.array([1.0, 1.0], dtype=np.float32),
        n_actuators=4, tau_act_ms=30.0,
        unmapped=__import__("pandas").DataFrame(),
    )
    for _ in range(1000):
        torque = nm.step(np.array([], dtype=np.int64), 0.1)
    assert np.all(torque == 0.0), "torque appeared with no spikes"


# --- the registry cannot launder a guess ---------------------------------

def test_one_shared_guess_is_one_row_not_millions():
    """A single assumed conductance propagated to every edge adds no evidence.

    The failure this guards against is an inventory that looks nearly complete
    because one guess filled 25 million slots. The guess must stay one row, with
    its reach recorded as an instance count rather than as independent support.
    """
    from flyemu.registry import Policy, Registry, Status

    reg = Registry(Policy.MINIMAL)
    reg.require("connection_class:all", "efficacy_per_synapse", units="mV",
                model_use="synaptic current", subsystem="synaptic_efficacy",
                instances=25_862_574, minimal=0.1)
    inv = reg.inventory()
    assert len(inv) == 1
    row = inv.iloc[0]
    assert row.status == Status.ASSUMED.value
    assert row.instances == 25_862_574
    measured = inv[inv.status == Status.MEASURED.value]
    assert measured.empty, "an assumed default was recorded as measured"


@needs_graph
def test_fragments_are_not_simulated_as_neurons():
    """An untyped orphan fragment is not a cell and must not get a threshold.

    The neuPrint :Neuron label includes ~9,300 untyped, unproofread fragments.
    Each would otherwise become a whole LIF neuron. Typed photoreceptors with
    no status set are real identified cells and must stay (F-COUNT-2).
    """
    from flyemu import connectome
    from flyemu.registry import Policy, Registry

    n, _ = connectome.load_tables()
    conn = connectome.build(Registry(Policy.MINIMAL))
    kept = n.bodyId.isin(conn.neurons.bodyId)
    assert not (kept & (n.status != "Traced") & n.type.isna()).any()
    r16 = n.type == "R1-R6"
    assert kept[r16].all(), "identified photoreceptors were dropped"
    assert (n.status == "Traced").sum() <= conn.n < len(n)


def test_an_overridden_value_is_never_measured():
    """Sweeping a parameter must not promote it to evidence."""
    from flyemu.registry import Policy, Registry, Status

    reg = Registry(Policy.MINIMAL)
    reg.overrides["motor_unit:all|force_per_spike"] = 10.0
    v = reg.require("motor_unit:all", "force_per_spike", units="uN*mm",
                    model_use="motor torque", subsystem="neuromuscular",
                    instances=328, minimal=1.0)
    assert v == 10.0
    row = reg.inventory().iloc[0]
    assert row.status == Status.ASSUMED.value
    assert "override" in row.evidence


def test_missing_and_absent_stay_distinguishable():
    """`unresolved` and a real zero are different claims.

    Unknown gap-junction coupling must not become measured absence, which is a
    correction the pack author made to session 1's framing.
    """
    from flyemu.registry import Policy, Registry, Status

    reg = Registry(Policy.MINIMAL)
    reg.provide("graph:x", "electrical_coupling", None, units="nS",
                model_use="omitted", status=Status.UNRESOLVED,
                evidence="no electrical reconstruction in these releases")
    reg.provide("graph:x", "measured_zero", 0.0, units="nS",
                model_use="a real zero", status=Status.MEASURED,
                evidence="measured and found absent")
    inv = reg.inventory().set_index("property")
    assert inv.loc["electrical_coupling", "status"] == "unknown"
    assert inv.loc["measured_zero", "status"] == "measured"
    # An unresolved row carries no value and a measured zero carries 0.0. Note
    # that the exported value column cannot by itself carry this distinction:
    # pandas renders a missing value as NaN, which a measurement could also be.
    # `status` is the authoritative field, and any consumer of the inventory
    # must read it rather than inferring from an empty value.
    import pandas as pd

    assert pd.isna(inv.loc["electrical_coupling", "value"])
    assert inv.loc["measured_zero", "value"] == 0.0


# --- the model as built ---------------------------------------------------

@needs_graph
def test_strict_refuses_and_names_what_it_lacks():
    """C0 must not run, and its refusal list is the result.

    A model that quietly substitutes a default for a missing biological
    quantity is the specific failure this project is built to avoid.
    """
    from flyemu.organism import Organism, StrictRefusal

    org = Organism(policy="strict")
    with pytest.raises(StrictRefusal) as exc:
        org.run(1.0)
    refusals = exc.value.refusals
    assert len(refusals) > 5
    named = {f"{r.entity}.{r.property}" for r in refusals}
    assert "connection_class:all.efficacy_per_synapse" in named
    assert "transmitter:glutamate.sign" in named


@needs_graph
def test_unreceivable_motor_output_is_recorded_not_dropped():
    """Motor neurons the body cannot receive must appear as unresolved rows.

    Silently discarding them would make the neuromuscular interface look
    complete while a third of the motor output went nowhere (F-BODY-1).
    """
    from flyemu.organism import Organism

    org = Organism(policy="minimal")
    assert len(org.nm.unmapped) > 0
    inv = org.reg.inventory()
    unmapped_rows = inv[
        inv.entity.str.contains("unmapped") & (inv.status == "unknown")
    ]
    assert not unmapped_rows.empty
    assert unmapped_rows.instances.sum() == len(org.nm.unmapped)


# --- interface completeness ------------------------------------------------

def test_absent_interface_channels_are_registered_not_silent():
    """A channel with no implementation must appear as an unresolved row.

    The failure this guards against is the one Ben named: an interface that
    looks complete because the parts that are missing are simply not mentioned.
    Vision, olfaction, hearing and the wing motor system are absent; the
    inventory has to say so, with counts.
    """
    from flyemu import interface
    from flyemu.registry import Policy, Registry

    reg = Registry(Policy.MINIMAL)
    channels = interface.register(reg)
    inv = reg.inventory()

    assert len(inv) == len(channels), "a channel went unrecorded"
    absent = inv[inv.status.isin(["absent", "unknown"])]
    assert len(absent) >= 30, "far too few channels recorded as absent"

    named = set(inv.entity)
    for required in ["interface:wing_power_motor", "interface:photoreceptors",
                     "interface:johnstons_organ", "interface:unsteady_aerodynamics",
                     "interface:cuticle_deformation"]:
        assert required in named, f"{required} is not in the channel table"


def test_unknown_in_the_animal_is_not_measured_absence():
    """Two kinds of absence must stay distinguishable.

    Gut stretch receptors are unestablished in Drosophila itself; the wing motor
    system is well characterised and merely unimplemented here. Recording both
    the same way would turn a gap in science into a claim about the animal.
    """
    from flyemu import interface
    from flyemu.registry import Policy, Registry

    reg = Registry(Policy.MINIMAL)
    interface.register(reg)
    inv = reg.inventory().set_index("entity")

    animal_gap = inv.loc["interface:gut_pharyngeal_sensory"]
    model_gap = inv.loc["interface:wing_power_motor"]
    assert animal_gap.status == "unknown"
    assert model_gap.status == "absent"
    assert "Unknown in the animal" in animal_gap.evidence
    assert "Unknown in the animal" not in model_gap.evidence
    assert "not measured absence" in animal_gap.uncertainty


def test_partial_channels_are_not_counted_as_working():
    """A channel reading the wrong physical variable is not an implementation.

    Campaniform sensilla transduce cuticular strain. This model drives them from
    rigid-body contact force, which is a different quantity, so the row must
    carry that rather than pass as done.
    """
    from flyemu import interface

    ch = interface.load().set_index("channel")
    cs = ch.loc["campaniform_sensilla"]
    assert cs.implemented == "partial"
    assert "NOT strain" in cs.note


# --- the physics that was missing ------------------------------------------

@needs_graph
def test_the_fly_can_collide_with_itself():
    """Legs must not pass through each other or through the thorax.

    Both body models ship with every geom at contype=0 and conaffinity=0, so
    nothing collides except through explicit ground pairs. MuJoCo also prunes
    candidate pairs at the BODY level first, so enabling the geom masks alone
    changes nothing - which is exactly the bug this guards against.
    """
    import mujoco as mj

    from flyemu.body import Body

    b = Body(self_collision=True)
    m = b.sim.mj_model
    prefix = f"{b.fly.name}/"

    colliding = {
        (mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or "").removeprefix(prefix)
        for g in range(m.ngeom)
        if (mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or "").startswith(prefix)
        and m.geom_contype[g]
    }
    assert colliding, "nothing collides"

    # Every body must have a collision surface. The bug this guards against
    # chose geoms by name suffix, which silently dropped the WINGS and all six
    # FEET - the surfaces that matter most - because their geoms are named
    # `_membrane` and `_brown` rather than `_body`.
    bodies_with_collision = {
        int(m.geom_bodyid[g]) for g in range(m.ngeom)
        if (mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or "").startswith(prefix)
        and m.geom_contype[g]
    }
    fly_bodies = {
        int(m.geom_bodyid[g]) for g in range(m.ngeom)
        if (mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or "").startswith(prefix)
    }
    assert bodies_with_collision == fly_bodies, (
        "some body has no collision surface at all"
    )
    for required in ["l_wing_membrane", "r_wing_membrane",
                     "lf_tarsus5_brown", "rh_tarsus5_brown"]:
        assert required in colliding, f"{required} must collide"

    # Colour overlays occupy the same space as the segment they decorate, so
    # colliding them duplicates every contact. Measured cost of getting this
    # wrong: 5073 us per step against 963.
    for overlay in ["c_head_red", "c_head_black", "c_thorax_black",
                    "l_wing_brown"]:
        assert overlay not in colliding, f"{overlay} should not collide"

    # MuJoCo prunes candidate pairs at the BODY level before it reaches the
    # geoms, so the body masks have to be set too.
    assert all(m.body_contype[b_] for b_ in fly_bodies), (
        "body-level masks not set; MuJoCo prunes before reaching the geoms"
    )


def test_nested_segments_do_not_collide_with_each_other():
    """Segments that nest at their joints must not fight their own joints.

    A convex hull of the rostrum overlaps the haustellum it sits inside, so
    colliding them would generate permanent contact. Collision is enabled
    across anatomical regions, not within them.
    """
    from flyemu.body import _ALL_REGION_BITS, _region_index

    # Within one region the masks must not admit a contact.
    for name_a, name_b in [("c_rostrum_body", "c_haustellum_body"),
                           ("lf_tarsus1_body", "lf_tibia_body")]:
        ia, ib = _region_index(name_a), _region_index(name_b)
        assert ia == ib, f"{name_a} and {name_b} should share a region"
        ct_a, ca_b = 1 << ia, _ALL_REGION_BITS & ~(1 << ib)
        assert not (ct_a & ca_b), "nested segments would collide"

    # Across regions it must admit one.
    ia, ib = _region_index("lf_tibia_body"), _region_index("c_thorax_body")
    assert ia != ib
    assert (1 << ia) & (_ALL_REGION_BITS & ~(1 << ib)), (
        "a leg must be able to collide with the thorax"
    )


@needs_graph
def test_campaniform_afferents_read_load_not_ground_contact():
    """Campaniform sensilla transduce cuticular strain.

    A leg can be loaded with no ground contact at all - pushed by another leg,
    or bearing the body through a different foot. Driving these afferents from
    ground contact force is a different physical quantity.
    """
    from flyemu.organism import Organism

    org = Organism(policy="minimal")
    inv = org.reg.inventory().set_index(["entity", "property"])
    row = inv.loc[("afferent:campaniform sensilla", "transduced_variable")]
    assert "cfrc_int" in row.evidence or "transmitted" in row.evidence
    assert "RIGID" in (row.uncertainty or ""), (
        "the rigid-segment limitation must stay recorded"
    )


@needs_graph
def test_retinotopy_is_derived_and_actually_spatial():
    """Retinotopy is labelled derived (not measured), and it really is spatial.

    Session 5 derived each photoreceptor's ommatidium from terminal positions
    (F-VISION-2). The failure mode guarded against earlier, a scrambled map
    that looks like vision, is now guarded by the R7/R8 concordance check in
    scripts/retinotopy.py; here we check labelling and that a local light
    spot drives only the cells mapped to it.
    """
    from flyemu.organism import Organism
    import numpy as np

    org = Organism(policy="minimal")
    assert org.vis is not None and org.vis.rows.size > 1000
    inv = org.reg.inventory().set_index(["entity", "property"])
    row = inv.loc[("photoreceptor:all", "retinotopy")]
    assert row.status == "derived" and row.basis == "derived"
    assert "inferred" in (row.uncertainty or "")

    om = org.vis.ommatidium
    assert om is not None and (om >= 0).mean() > 0.9
    readouts = np.zeros((2, 721, 2), dtype=np.float32)
    readouts[0, 100, 0] = 1.0            # one bright ommatidium, left eye
    drive = org.vis.drive(readouts)
    lit = (org.vis.eye == 0) & (om == 100)
    dark = (org.vis.eye == 0) & (om >= 0) & (om != 100)
    if lit.any():
        assert drive[org.vis.rows[lit]].min() > drive[org.vis.rows[dark]].max()


def test_a_borrowed_profile_is_assumed_and_cites_its_source():
    """A value fitted in another paper to another specimen is not measured."""
    from flyemu import profiles
    from flyemu.registry import Policy, Registry, Status

    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, "shiu2024")
    v = reg.require("cell_type:all", "v_rest", units="mV", model_use="x",
                    instances=10, minimal=-60.0)
    assert v == -52.0
    row = reg.inventory().iloc[0]
    assert row.status == Status.INFERRED.value      # borrowed, never measured
    assert "Shiu" in row.evidence


def test_shuffled_control_preserves_degrees_and_destroys_wiring():
    """The control must differ from the real graph only in who targets whom."""
    from flyemu.connectome import Connectome, shuffled
    import pandas as pd

    rng = np.random.default_rng(0)
    n, e = 200, 4000
    pre = np.sort(rng.integers(0, n, e))
    post = rng.integers(0, n, e).astype(np.int32)
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(pre, minlength=n), out=indptr[1:])
    w = rng.integers(1, 20, e).astype(np.float32)
    c = Connectome(pd.DataFrame({"bodyId": np.arange(n)}), indptr, post, w,
                   np.ones(n, np.float32), np.full(e, 0.1, np.float32))
    s = shuffled(c, np.random.default_rng(1))
    assert np.array_equal(np.bincount(s.indices, minlength=n),
                          np.bincount(c.indices, minlength=n))
    assert np.array_equal(s.indptr, c.indptr)
    assert (s.indices != c.indices).mean() > 0.9


def test_adaptation_slows_a_constantly_driven_neuron():
    """With adaptation on, late firing under constant drive is slower than early."""
    from flyemu.connectome import Connectome
    from flyemu.lif import LIFParams, Network
    import pandas as pd

    n = 1
    c = Connectome(pd.DataFrame({"bodyId": [0]}), np.zeros(2, np.int64),
                   np.zeros(0, np.int32), np.zeros(0, np.float32),
                   np.ones(1, np.float32), np.zeros(0, np.float32))
    full = lambda v: np.full(n, v, np.float32)
    counts = {}
    for a in (0.0, 2.0):
        p = LIFParams(full(20.0), full(-52.0), full(-45.0), full(-52.0),
                      full(2.2), 5.0, 18, 0.0, True, a, 200.0)
        net = Network(c, p, 0.1)
        early = late = 0
        for s in range(10000):
            k = net.step(external_mv=np.array([12.0], np.float32)).size
            early += k if s < 1000 else 0
            late += k if s >= 9000 else 0
        counts[a] = (early, late)
    assert counts[0.0][0] == counts[0.0][1] > 0
    assert counts[2.0][1] < counts[2.0][0]


def _toy_conn(n=300, e=6000, seed=0):
    from flyemu.connectome import Connectome
    import pandas as pd
    rng = np.random.default_rng(seed)
    pre = np.sort(rng.integers(0, n, e))
    post = rng.integers(0, n, e).astype(np.int32)
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(pre, minlength=n), out=indptr[1:])
    types = np.array([f"T{i % 7}" for i in range(n)], dtype=object)
    types[:5] = None
    gain = rng.uniform(0, 2, n).astype(np.float32)
    nrn = pd.DataFrame({"bodyId": np.arange(n), "type": types})
    return Connectome(nrn, indptr, post, rng.integers(1, 9, e).astype(np.float32),
                      np.ones(n, np.float32), (0.1 * gain[post]).astype(np.float32),
                      psp_mv=0.1, post_gain=gain), pre


def test_rewired_controls_recompute_postsynaptic_efficacy():
    """Postsynaptic factors (sensory mask, size) must follow the NEW target."""
    from flyemu.connectome import shuffled, type_shuffled
    c, _ = _toy_conn()
    for f in (shuffled, type_shuffled):
        s = f(c, np.random.default_rng(3))
        assert np.allclose(s.efficacy_mv, 0.1 * c.post_gain[s.indices])


def test_type_shuffle_preserves_type_blocks_and_moves_neurons():
    from flyemu.connectome import type_shuffled
    import pandas as pd
    c, pre = _toy_conn()
    s = type_shuffled(c, np.random.default_rng(4))
    t = c.neurons.type.fillna("#").to_numpy()
    key = lambda post: pd.Series(1, index=pd.MultiIndex.from_arrays(
        [t[pre], t[post]])).groupby(level=[0, 1]).size().sort_index()
    assert key(c.indices).equals(key(s.indices))
    assert np.array_equal(np.bincount(s.indices, minlength=c.n),
                          np.bincount(c.indices, minlength=c.n))
    assert (s.indices != c.indices).mean() > 0.5


def test_a_spike_arrives_exactly_one_delay_later():
    """Delay semantics: a spike at step t reaches its target's current at t + D."""
    from flyemu.connectome import Connectome
    from flyemu.lif import LIFParams, Network
    import pandas as pd

    c = Connectome(pd.DataFrame({"bodyId": [0, 1]}), np.array([0, 1, 1]),
                   np.array([1], np.int32), np.array([1.0], np.float32),
                   np.ones(2, np.float32), np.array([1.0], np.float32))
    full = lambda v: np.full(2, v, np.float32)
    D = 18
    net = Network(c, LIFParams(full(20.0), full(-52.0), full(-45.0), full(-52.0),
                               full(2.2), 5.0, D, 0.0, True), 0.1)
    net.step(kick=(np.array([0]), 100.0))          # neuron 0 fires at step 0
    arrive = None
    for s in range(1, 40):
        net.step()
        if arrive is None and net.i_syn[1] > 0:
            arrive = s
    assert arrive == D


def test_depression_weakens_repeated_spikes_and_recovers():
    from flyemu.connectome import Connectome
    from flyemu.lif import LIFParams, Network
    import pandas as pd
    c = Connectome(pd.DataFrame({"bodyId": [0, 1]}), np.array([0, 1, 1]),
                   np.array([1], np.int32), np.array([1.0], np.float32),
                   np.ones(2, np.float32), np.array([1.0], np.float32))
    full = lambda v: np.full(2, v, np.float32)
    p = LIFParams(full(20.0), full(-52.0), full(-45.0), full(-52.0), full(2.2),
                  5.0, 1, 0.0, True, 0.0, 200.0, 0.5, 500.0)
    net = Network(c, p, 0.1)
    net.step(kick=(np.array([0]), 100.0)); net.step()
    first = float(net.i_syn[1])
    for _ in range(30): net.step()
    net.i_syn[:] = 0
    net.step(kick=(np.array([0]), 100.0)); net.step()
    second = float(net.i_syn[1])
    assert second < 0.7 * first
    for _ in range(30000): net.step()
    assert net.x_res[0] > 0.99


def test_conductance_mode_matches_a_single_psp_at_rest():
    """Near rest, one EPSP and one IPSP match the current-based model."""
    from flyemu.connectome import Connectome
    from flyemu.lif import LIFParams, Network
    import pandas as pd
    for sgn in (1.0, -1.0):
        c = Connectome(pd.DataFrame({"bodyId": [0, 1]}), np.array([0, 1, 1]),
                       np.array([1], np.int32), np.array([1.0], np.float32),
                       np.array([sgn, 1.0], np.float32), np.array([0.5], np.float32))
        full = lambda v: np.full(2, v, np.float32)
        peaks = []
        for cond in (False, True):
            p = LIFParams(full(20.0), full(-52.0), full(-45.0), full(-52.0), full(2.2),
                          5.0, 1, 0.0, True, cond=cond)
            net = Network(c, p, 0.1)
            net.step(kick=(np.array([0]), 100.0))
            vs = [net.step() is not None and float(net.v[1]) for _ in range(400)]
            peaks.append(max(vs) if sgn > 0 else min(vs))
        dev = [x + 52.0 for x in peaks]
        assert abs(dev[0]) > 0.05 and abs(dev[1] - dev[0]) < 0.05 * abs(dev[0])


def test_every_value_is_labelled_measured_derived_or_inferred():
    """Project rule: each quantity says whether it was measured, derived or inferred."""
    from flyemu.registry import Policy, Registry, Status
    reg = Registry(Policy.MINIMAL)
    reg.provide("a", "x", 1.0, units="mV", model_use="t", status=Status.MEASURED)
    reg.provide("b", "x", 1.0, units="mV", model_use="t", status=Status.DERIVED)
    reg.require("c", "x", units="mV", model_use="t", minimal=1.0)          # assumed
    reg.provide("d", "x", 1.0, units="mV", model_use="t", status=Status.FITTED)
    reg.overrides["e|x"] = 2.0
    reg.require("e", "x", units="mV", model_use="t", minimal=1.0)          # override
    inv = reg.inventory().set_index("entity")
    assert inv.basis.to_dict() == {"a": "measured", "b": "derived", "c": "guessed",
                                   "d": "inferred", "e": "guessed"}
    assert inv.iterate.to_dict() == {"a": False, "b": False,
                                                         "c": True, "d": False, "e": True}


def test_an_odour_drives_only_receptors_tuned_to_it_on_the_near_antenna():
    """Olfactory drive comes from measured tuning and the antenna's own position."""
    from flyemu.organism import Organism
    from flyemu.world import OdourSource
    import numpy as np

    org = Organism(policy="minimal")
    xpos = org.body.sim.mj_data.xpos
    la, ra = org.chem.antenna_bodies
    tun = org.chem.tuning
    odour = tun.columns[tun.astype(bool).sum().argmax()]      # widely tested odour
    org.world.odours = [OdourSource(odour, xpos[la] + np.array([0, 3.0, 0]), 1e-4, 1.0)]
    d = org.chem.drive(org.world, xpos)[org.chem.rows]
    r = tun[odour].to_numpy()
    orn = org.chem.kind == "orn"
    left, right = orn & (org.chem.side == 0), orn & (org.chem.side == 1)
    # untuned receptors get only their clean-air (spontaneous) drive; the
    # near (left) antenna gets more
    rates = np.zeros(len(r)); rates[orn] = org.chem.last_rate_hz
    assert np.allclose(rates[orn & (r == 0)], org.chem.sfr_hz[orn & (r == 0)])
    typ = org.conn.neurons.type.to_numpy()[org.chem.rows]
    diffs = [rates[left & (typ == t)].mean() - rates[right & (typ == t)].mean()
             for t in np.unique(typ[orn & (r > 0.5)])
             if (left & (typ == t)).any() and (right & (typ == t)).any()]
    assert diffs and min(diffs) >= 0 and np.mean(diffs) > 0
    inv = org.reg.inventory().set_index(["entity", "property"])
    assert inv.loc[("orn:all", "odour_tuning")].basis == "measured"
    assert inv.loc[("orn:all", "max_drive")].basis == "guessed"


def test_the_whole_organism_carries_required_evidence_fields():
    """Measured cites a source; derived states inputs; inferred justifies; guessed says why."""
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m2", min_synapses=5)
    assert org.reg.validate() == []
    inv = org.reg.inventory()
    assert set(inv.basis) <= {"measured", "derived", "inferred", "guessed",
                              "unknown", "absent", "inapplicable"}
    assert inv[inv.basis == "guessed"].iterate.all()


def test_orn_drive_reproduces_hallem_rates_in_the_network():
    """ORNs fire at Hallem SFR in clean air (Poisson), inside the real network."""
    from flyemu.organism import Organism
    import numpy as np
    import pandas as pd

    org = Organism(policy="minimal", profile="m2", min_synapses=5)
    ch = org.chem
    orn = np.flatnonzero(ch.kind == "orn")
    rt = pd.read_csv("data/params/orn_rates.csv", comment="#").set_index("orn_type")
    types = org.conn.neurons.type.to_numpy()[ch.rows[orn]]
    assert np.allclose(ch.sfr_hz[orn], rt.sfr_hz.reindex(types).to_numpy())
    rows = ch.rows[orn]
    n = np.zeros(orn.size)
    steps = int(1000 / org.timestep_ms)
    for _ in range(steps):
        spk = org.net.step(external_mv=ch.drive(org.world, org.body.sim.mj_data.xpos))
        n += np.isin(rows, spk)
    # pooled per type: Poisson count over 1 s, tolerance 4 sd + 1
    df = pd.DataFrame({"t": types, "n": n, "sfr": ch.sfr_hz[orn]}).groupby("t")
    got, want, k = df.n.sum(), df.sfr.first() * df.size(), df.size()
    assert np.all(np.abs(got - want) <= 4 * np.sqrt(want) + 1 + 0.03 * want)
    # pulses realise high rates too (Rmax at 1e-2), dead time compensated
    top = np.full(2000, 250.0)
    ch2 = type(ch)(**{**ch.__dict__, "t_ref_ms": np.full(2000, 2.2),
                      "pulse_mv": np.full(2000, 1e4)})
    v_ref, cnt = np.zeros(2000), np.zeros(2000)
    for s in range(steps):
        t = s * org.timestep_ms
        fire = (ch2.rate_to_pulses(top) > 0) & (t >= v_ref)
        cnt += fire
        v_ref[fire] = t + 2.2
    assert abs(cnt.mean() - 250) < 10
    inv = org.reg.inventory().set_index(["entity", "property"])
    assert inv.loc[("orn:hallem_types", "spontaneous_rate")].basis == "measured"
    assert inv.loc[("orn:other_types", "spontaneous_and_max_rate")].basis == "inferred"
