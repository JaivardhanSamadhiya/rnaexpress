"""Resume-safe orchestration for the remaining frozen direct/M3 controls."""

from __future__ import annotations

import subprocess
import sys


CONTROLS = ("parent_binding_knockout", "cell_context_permutation")


def invoke(module: str, *arguments: str) -> None:
    subprocess.run([sys.executable, "-u", "-m", module, *arguments], check=True)


def main() -> None:
    for control in CONTROLS:
        for family in ("M1", "M2"):
            for outer_fold in range(5):
                invoke(
                    "src.analysis.run_finalshot_direct_controls",
                    "--control", control,
                    "--family", family,
                    "--outer-fold", str(outer_fold),
                )
        for outer_fold in range(5):
            invoke(
                "src.analysis.run_finalshot_m3_controls",
                "--control", control,
                "--stage", "inner-grid",
                "--outer-fold", str(outer_fold),
            )
            invoke(
                "src.analysis.run_finalshot_m3_controls",
                "--control", control,
                "--stage", "finalize",
                "--outer-fold", str(outer_fold),
            )


if __name__ == "__main__":
    main()
