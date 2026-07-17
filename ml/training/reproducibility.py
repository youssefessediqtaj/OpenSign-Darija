from __future__ import annotations

import os
import platform
import random
import subprocess
from datetime import UTC, datetime

import numpy as np


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNCONFIRMED"


def set_global_seeds(seed: int) -> dict[str, object]:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch_seeded = True
    except Exception:
        torch_seeded = False
    return {
        "seed": seed,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "torch_seeded": torch_seeded,
        "platform": platform.platform(),
        "git_commit": git_commit(),
        "created_at": datetime.now(UTC).isoformat(),
        "device": os.environ.get("TRAINING_DEVICE", "cpu"),
    }
