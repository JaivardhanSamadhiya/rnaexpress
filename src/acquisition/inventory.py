"""Build a checksum inventory for physically acquired public files."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "manifests" / "file_inventory.csv"


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in RAW.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__MACOSX" in path.parts:
            continue
        files.append(path)
    return sorted(files)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["relative_path", "size_bytes", "sha256"],
        )
        writer.writeheader()
        for path in iter_source_files():
            writer.writerow(
                {
                    "relative_path": path.relative_to(ROOT).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

