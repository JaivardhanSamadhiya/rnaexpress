"""Resume-safe orchestration for both frozen crossed-cell M3 controls."""

from __future__ import annotations

import subprocess
import sys

from src.analysis.run_finalshot_m3_trans_control import TASKS


def main() -> None:
    for task in TASKS:
        for stage in ("inner-grid", "finalize"):
            subprocess.run(
                [
                    sys.executable,
                    "-u",
                    "-m",
                    "src.analysis.run_finalshot_m3_trans_control",
                    "--stage",
                    stage,
                    "--task",
                    task,
                ],
                check=True,
            )


if __name__ == "__main__":
    main()
