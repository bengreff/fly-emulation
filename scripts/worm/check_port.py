"""Port check: Jaxley composite membrane (bioemu.jx_membrane + wormemu.nicoletti) vs NEURON on the original
.mod files, same single compartment, same protocol, same dt. Prints RMS difference per current step.

usage: check_port.py <neuron_ref.npz> [dt_ms]
"""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np
import jax, jax.numpy as jnp
import jaxley as jx
from bioemu.jx_membrane import make_membrane
from wormemu import nicoletti as lib

jax.config.update("jax_enable_x64", True)
ref = np.load(sys.argv[1])
cfg = json.loads(str(ref["cfg"]))
dt = float(sys.argv[2]) if len(sys.argv) > 2 else cfg.get("dt", 0.4)
T = cfg.get("tstop", 11000)


def build_single(cfg):
    L = math.sqrt(cfg["surf"] / math.pi) * 1e4  # um, cylinder with L = diam (as the Nicoletti scripts)
    comp = jx.Compartment()
    cell = jx.Cell([jx.Branch([comp], ncomp=1)], parents=[-1])
    cell.set("length", L)
    cell.set("radius", L / 2)
    cell.set("capacitance", cfg["cm"])
    cell.set("axial_resistivity", 100.0)
    Mem = make_membrane(lib)
    cell.insert(Mem())
    for c, val in cfg["g_nS"].items():
        cell.set(f"Mem_g_{c}", val * 1e-9 / cfg["surf"])
    cell.set("Mem_eL", cfg["eL"])
    cell.set("Mem_sv", cfg["surf"] / cfg["vol"])
    if "eCa" in cfg:
        cell.set("Mem_eCa", cfg["eCa"])
    cell.set("v", cfg.get("v_init", -65.0))
    cell.init_states(delta_t=dt)
    cell.branch(0).comp(0).record("v", verbose=False)
    return cell


if __name__ == "__main__":
    cell = build_single(cfg)
    amps = np.linspace(-0.015, 0.035, 11)

    def sim(a):
        s = jx.step_current(1000.0, 5000.0, a, dt, T)
        ds = cell.branch(0).comp(0).data_stimulate(s)
        return jx.integrate(cell, data_stimuli=ds, delta_t=dt)[0]

    V = np.array(jax.jit(jax.vmap(sim))(jnp.asarray(amps)))
    n = min(V.shape[1], ref["v"].shape[1])
    step = max(1, int(round(dt / cfg.get("dt", 0.4))))
    vr = ref["v"][:, ::step] if dt > cfg.get("dt", 0.4) else ref["v"]
    n = min(V.shape[1], vr.shape[1])
    rms = np.sqrt(np.mean((V[:, :n] - vr[:, :n]) ** 2, axis=1))
    mx = np.max(np.abs(V[:, :n] - vr[:, :n]), axis=1)
    print(json.dumps({"ref": sys.argv[1], "dt": dt, "rms_mV": [round(x, 3) for x in rms], "max_abs_mV": [round(x, 2) for x in mx],
                      "rest_jx": round(float(V[3, int(900 / dt)]), 2), "rest_nrn": round(float(vr[3, int(900 / dt)]), 2)}))
    np.save(sys.argv[1].replace(".npz", "_jx.npy"), V)
