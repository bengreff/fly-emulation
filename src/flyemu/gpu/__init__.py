"""Batched GPU simulation of the CNS (JAX). See docs/GPU.md.

`batched.BatchedNetwork` runs B parameter variants of one connectome at once and
is equivalence-tested against the CPU reference `flyemu.lif.Network`
(tests/test_gpu_batched.py, scripts/gpu_bench.py).
"""
