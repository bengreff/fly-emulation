"""Read a flyvis (Lappalainen et al. 2024) PyTorch checkpoint without torch.

The published ensemble (`flyvis download-pretrained`, results_pretrained_models.zip, sha256
71c78d40...281db1, MIT licence) stores each network's parameters as a torch zip pickle. This reads
the tensors into numpy arrays so the per-type values can be tabulated with the project venv.

    uv run python scripts/fetch/flyvis_checkpoint.py data/raw/flyvis_lappalainen2024/results/flow/0000/000/best_chkpt
"""
from __future__ import annotations

import collections
import io
import pickle
import sys
import zipfile

import numpy as np

_DT = {"FloatStorage": np.float32, "DoubleStorage": np.float64, "LongStorage": np.int64,
       "IntStorage": np.int32, "BoolStorage": np.bool_}


def load(path) -> dict:
    z = zipfile.ZipFile(path)
    root = z.namelist()[0].split("/")[0]

    class _Storage:
        def __init__(self, key, dt):
            self.a = np.frombuffer(z.read(f"{root}/data/{key}"), dtype=dt)

    def _tensor(storage, off, size, stride, *_a, **_k):
        if len(size) == 0:
            return storage.a[off]
        st = [s * storage.a.itemsize for s in stride]
        return np.lib.stride_tricks.as_strided(storage.a[off:], shape=size, strides=st).copy()

    class _U(pickle.Unpickler):
        def find_class(self, mod, name):
            if name == "_rebuild_tensor_v2":
                return _tensor
            if name == "_rebuild_parameter":
                return lambda data, *_a, **_k: data
            if mod.startswith("torch") and name.endswith("Storage"):
                return name
            if name == "OrderedDict":
                return collections.OrderedDict
            return super().find_class(mod, name)

        def persistent_load(self, pid):
            _, st, key, _loc, _n = pid
            return _Storage(key, _DT[st if isinstance(st, str) else st.__name__])

    return _U(io.BytesIO(z.read(f"{root}/data.pkl"))).load()


def _show(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict):
            _show(v, pre + k + ".")
        else:
            print(pre + k, getattr(v, "shape", v))


if __name__ == "__main__":
    _show(load(sys.argv[1]))
