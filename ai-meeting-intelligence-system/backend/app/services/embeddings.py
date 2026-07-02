from __future__ import annotations

import hashlib

import numpy as np


def cheap_hash_embedding(text: str, dim: int = 384) -> list[float]:
    """
    Deterministic, dependency-light embedding fallback.
    Replace with a real embedding model in production.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "big", signed=False)
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(dim,)).astype(np.float32)
    v /= max(float(np.linalg.norm(v)), 1e-8)
    return v.tolist()

