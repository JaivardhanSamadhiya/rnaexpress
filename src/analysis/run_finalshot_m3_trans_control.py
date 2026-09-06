"""Run the frozen M3 trans-interaction knockout on crossed cell transfers.

This deliberately reuses the already-frozen M3 transfer optimizer and selection
code while replacing only its feature store.  Cache and result roots are
separate, and the implementation token prevents an ordinary M3 cache from
being accepted as a control fit.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis import run_finalshot_m3_transfers as frozen
from src.modeling.finalshot_controls import FinalShotControlledFeatureStore


CONTROL = "trans_interaction_knockout"
TASKS = ("CAD_to_N2A", "N2A_to_CAD")
CACHE = ROOT / "data" / "interim" / "finalshot_m3_trans_control_cache"
OUT = ROOT / "results" / "finalshot" / "transfers_m3_trans_control"
IMPLEMENTATION = "2026-09-06-trans-knockout-v1"


class TransKnockoutStore(FinalShotControlledFeatureStore):
    """M2 requests resolve to the corresponding frozen M1 feature space."""

    def __init__(self, rows, rbp_matrix_path, dictionary_path, expression_path):
        super().__init__(
            rows, rbp_matrix_path, dictionary_path, expression_path, CONTROL
        )


def configure() -> None:
    frozen.CACHE = CACHE
    frozen.OUT = OUT
    frozen.IMPLEMENTATION = IMPLEMENTATION
    frozen.FinalShotFeatureStore = TransKnockoutStore


def annotate(task: str) -> None:
    path = OUT / f"{task}_M3.npz"
    with np.load(path, allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    metadata = json.loads(str(arrays["metadata_json"].item()))
    metadata.update({
        "phase": "FinalShot M3 crossed-cell trans-interaction knockout",
        "control": CONTROL,
        "implementation": IMPLEMENTATION,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    })
    arrays["metadata_json"] = np.asarray(json.dumps(metadata, sort_keys=True))
    temporary = path.with_suffix(".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("inner-grid", "finalize"), required=True)
    parser.add_argument("--task", choices=TASKS, required=True)
    args = parser.parse_args()
    configure()
    if args.stage == "inner-grid":
        frozen.fit_inner_grid(args.task)
    else:
        frozen.finalize(args.task)
        annotate(args.task)


if __name__ == "__main__":
    main()
