"""Fail-closed metadata audit for the untouched Moffatt 2026 candidate lock.

The raw GEO archive contains per-oligo neurite/soma counts.  During v3
development it may be hashed as an opaque byte stream, but it must not be
opened, listed, extracted, or parsed.  This module reads only the committed
manifest and GEO's separate outcome-free metadata/file-list artifacts.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "frozen" / "moffatt_2026_candidate_lock_manifest.json"
EXPECTED_FAMILIES = {"mutation", "necessity", "SHAPE", "shuffle", "sufficiency"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit() -> dict[str, object]:
    """Verify frozen bytes and safe metadata without opening the TAR archive."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["outcome_boundary"]["archive_opened"]:
        raise ValueError("Moffatt candidate manifest no longer records an untouched archive")

    paths: dict[str, Path] = {}
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if path.stat().st_size != entry["size_bytes"]:
            raise ValueError(f"Moffatt candidate file size changed: {entry['path']}")
        if _sha256(path) != entry["sha256"]:
            raise ValueError(f"Moffatt candidate file hash changed: {entry['path']}")
        paths[entry["content_class"]] = path

    file_list = paths["outcome-free public file names, sizes, and timestamps"]
    lines = file_list.read_text(encoding="utf-8").splitlines()
    members = [line for line in lines if line.startswith("File\t")]
    if len(members) != 80:
        raise ValueError(f"Expected 80 public processed-file records, found {len(members)}")

    family_counts: Counter[str] = Counter()
    for line in members:
        name = line.split("\t", 2)[1]
        matches = [family for family in EXPECTED_FAMILIES if f"_{family}_" in name]
        if len(matches) != 1 or not name.endswith(".umis.txt.gz"):
            raise ValueError(f"Unexpected GSE334718 metadata filename: {name}")
        family_counts[matches[0]] += 1
    if family_counts != Counter({family: 16 for family in EXPECTED_FAMILIES}):
        raise ValueError(f"Unexpected GSE334718 family file counts: {family_counts}")

    return {
        "dataset": manifest["dataset"],
        "frozen_role": manifest["frozen_role"],
        "archive_sha256": manifest["files"][0]["sha256"],
        "archive_opened": False,
        "processed_files": len(members),
        "files_by_library_family": dict(sorted(family_counts.items())),
        "outcomes_inspected": False,
        "eligibility_unknowns": manifest["eligibility_unknowns"],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
