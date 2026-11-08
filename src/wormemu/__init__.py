"""The worm model. The data model is wormemu.simulate(theta, experiment): wormemu.datamodel, docs/worm/DATA_MODEL.md."""


def simulate(theta, experiment):
    from wormemu.datamodel import simulate as run
    return run(theta, experiment)
