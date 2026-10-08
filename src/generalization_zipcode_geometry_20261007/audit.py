"""Standard-library-only, phenotype-free exact zipcode geometry feasibility."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = "generalization_zipcode_geometry_20261007"
SRC, OUT, REP, ART = [ROOT / stem / NS for stem in ("src", "results", "reports", "artifacts")]
DESIGN = ART / "design.json"
MANIFEST = OUT / "design_freeze.json"
NEXT_MANIFEST = ROOT / "results/generalization_next_20261007/prefit_manifest.json"
INVENTORIES = {
    "original": ROOT / "artifacts/generalization_next_20261007/sequence_inventory.csv.gz",
    "encoded": ROOT / "artifacts/generalization_next_20261007/encoded_sequence_inventory.csv.gz",
}
FIELDS = ["intervention_id", "dataset", "biological_component", "parent_context_id",
          "parent_sequence", "mutant_sequence"]
PROHIBITED = {"measured_delta", "localization_effect", "localization_change", "score", "outcome"}
PAPER = "https://pmc.ncbi.nlm.nih.gov/articles/PMC3258965/"
A = "CGGAC"
B = re.compile(r"(?=([AC]CA[CT]))")
LOW, HIGH = 10, 25


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path: Path, payload: bytes) -> None:
    path = path.resolve()
    assert any(path.is_relative_to(home) for home in (SRC, OUT, REP, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == payload, "Immutable artifact differs: " + str(path)
    else:
        path.write_bytes(payload)


def jsave(path: Path, data: dict) -> None:
    save(path, (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def normalize(sequence: str) -> str:
    if not isinstance(sequence, str):
        raise ValueError("Sequence must be a string")
    value = sequence.upper().replace("U", "T")
    if not value or set(value) - set("ACGT"):
        raise ValueError("Expected nonempty ACGT/U expressed-strand sequence")
    return value


def starts(sequence: str, motif: str) -> tuple[int, ...]:
    return tuple(match.start() for match in re.finditer("(?=" + re.escape(motif) + ")", sequence))


def pieces(sequence: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    sequence = normalize(sequence)
    return starts(sequence, A), tuple(match.start() for match in B.finditer(sequence))


def pairs(sequence: str) -> frozenset[tuple[str, int, int]]:
    """A/B starts, not RNA reverse complements; all strictly intervening gaps."""
    sites_a, sites_b = pieces(sequence)
    output = set()
    for a in sites_a:
        for b in sites_b:
            gap_ab = b - (a + 5)
            gap_ba = a - (b + 4)
            if LOW <= gap_ab <= HIGH:
                output.add(("A_then_B", a, b))
            if LOW <= gap_ba <= HIGH:
                output.add(("B_then_A", a, b))
    return frozenset(output)


def contrast(parent: str, mutant: str) -> dict:
    parent, mutant = normalize(parent), normalize(mutant)
    if len(parent) != len(mutant):
        raise ValueError("Only equal-length substitution contrasts are admitted")
    changed = frozenset(i for i, (left, right) in enumerate(zip(parent, mutant)) if left != right)
    before, after = pairs(parent), pairs(mutant)
    gained, lost = after - before, before - after
    for _, a, b in gained | lost:
        assert changed.intersection(range(a, a + 5)) or changed.intersection(range(b, b + 4)), \
            "Equal-length spacer-only edits cannot change recognition-piece geometry"
    pa, pb = pieces(parent)
    ma, mb = pieces(mutant)
    return {
        "sequence_length": len(parent), "edit_count": len(changed),
        "parent_pair_count": len(before), "mutant_pair_count": len(after),
        "parent_pair_present": int(bool(before)), "mutant_pair_present": int(bool(after)),
        "pair_count_delta": len(after) - len(before),
        "gained_pair_count": len(gained), "lost_pair_count": len(lost),
        "geometry_changed": int(bool(gained or lost)),
        "net_pair_count_changed": int(len(after) != len(before)),
        "gained_A_then_B": sum(order == "A_then_B" for order, _, _ in gained),
        "gained_B_then_A": sum(order == "B_then_A" for order, _, _ in gained),
        "lost_A_then_B": sum(order == "A_then_B" for order, _, _ in lost),
        "lost_B_then_A": sum(order == "B_then_A" for order, _, _ in lost),
        "isolated_piece_A_delta": len(ma) - len(pa),
        "isolated_piece_B_delta": len(mb) - len(pb),
        "old_ACACCC_proxy_delta": len(starts(mutant, "ACACCC")) - len(starts(parent, "ACACCC")),
        "zero_net_turnover": int(bool(gained or lost) and len(after) == len(before)),
    }


def assert_design() -> dict:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    assert design["primary_paper"] == PAPER
    assert design["recognition_piece_a_rna"] == A
    assert design["recognition_piece_b_dna_regex"] == "[AC]CA[CT]"
    assert design["recognition_piece_b_rna_regex"] == "[AC]CA[CU]"
    assert (design["spacer_min_nt"], design["spacer_max_nt"]) == (LOW, HIGH)
    assert design["orders"] == ["A_then_B", "B_then_A"]
    return design


def admit_next() -> dict:
    committed = subprocess.check_output(["git", "show", "HEAD:" + NEXT_MANIFEST.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert committed == NEXT_MANIFEST.read_bytes(), "NEXT prefit manifest must be committed exactly"
    previous = json.loads(committed)
    for path in INVENTORIES.values():
        name = path.relative_to(ROOT).as_posix()
        assert previous["files"][name] == sha256(path), name
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in INVENTORIES.values()}


def freeze() -> None:
    assert not (OUT / "coverage_receipt.json").exists(), "Coverage already exists; no new design"
    assert_design()
    inventory_hashes = admit_next()
    test_receipt = json.loads((OUT / "synthetic_tests_receipt_v2.json").read_text(encoding="utf-8"))
    assert test_receipt["status"] == "PASS" and test_receipt["tests"] >= 8
    own = list(SRC.glob("*.py")) + [DESIGN, REP / "protocol.md"]
    own += [home / ".gitattributes" for home in (SRC, OUT, REP, ART)]
    assert all(path.read_bytes() == b"* -text\n" for path in own if path.name == ".gitattributes")
    sources = {path.relative_to(ROOT).as_posix(): sha256(path) for path in SRC.glob("*.py")}
    assert test_receipt["sources"] == sources, "Tests must bind current source"
    files = {path.relative_to(ROOT).as_posix(): sha256(path) for path in own}
    files.update(inventory_hashes)
    files[NEXT_MANIFEST.relative_to(ROOT).as_posix()] = sha256(NEXT_MANIFEST)
    files[(OUT / "synthetic_tests_receipt_v2.json").relative_to(ROOT).as_posix()] = sha256(OUT / "synthetic_tests_receipt_v2.json")
    jsave(MANIFEST, {"status": "FROZEN_OUTCOME_BLIND_DESIGN", "version": 1,
        "primary_paper": PAPER, "supervised_fits": 0, "source_outcomes_read": False,
        "coverage_precedes_fit": True, "coverage_after_design_commit": True,
        "files": files, "file_count": len(files),
        "initial_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()})
    print("Design freeze", len(files), sha256(MANIFEST), flush=True)


def check_freeze() -> dict:
    committed = subprocess.check_output(["git", "show", "HEAD:" + MANIFEST.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert committed == MANIFEST.read_bytes(), "Commit exact outcome-blind design before coverage"
    manifest = json.loads(committed)
    for name, expected in manifest["files"].items():
        assert sha256(ROOT / name) == expected, "Pinned input changed: " + name
    assert_design()
    return manifest


def read_inventory(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        validate_schema(reader.fieldnames)
        rows = list(reader)
    assert len(rows) == 26258
    assert len({row["intervention_id"] for row in rows}) == len(rows)
    return rows


def validate_schema(fields: list[str]) -> None:
    if fields != FIELDS or PROHIBITED.intersection(fields):
        raise ValueError("Inventory must have the exact outcome-free six-field schema")


def identity_check(original: list[dict], encoded: list[dict]) -> None:
    assert len(original) == len(encoded)
    for left, right in zip(original, encoded):
        assert all(left[key] == right[key] for key in FIELDS[:4]), "Row identity/metadata changed"
        if left["dataset"] != "srle":
            assert all(left[key] == right[key] for key in FIELDS[4:]), "Only SRLE can acquire encoded arms"
        else:
            assert all(len(left[key]) == 6 and len(right[key]) == 46 for key in FIELDS[4:])
            assert all(right[key][20:26] == left[key] for key in FIELDS[4:])


def csv_bytes(rows: list[dict]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def summarize(rows: list[dict], summaries: list[dict]) -> list[dict]:
    by_dataset = defaultdict(list)
    for index, row in enumerate(rows):
        by_dataset[row["dataset"]].append(index)
    output = []
    conditions = {
        "all": lambda value: True,
        "parent_pair_present": lambda value: value["parent_pair_present"] == 1,
        "mutant_pair_present": lambda value: value["mutant_pair_present"] == 1,
        "either_pair_present": lambda value: value["parent_pair_present"] or value["mutant_pair_present"],
        "geometry_changed": lambda value: value["geometry_changed"] == 1,
        "net_pair_count_changed": lambda value: value["net_pair_count_changed"] == 1,
        "zero_net_turnover": lambda value: value["zero_net_turnover"] == 1,
        "isolated_piece_A_changed": lambda value: value["isolated_piece_A_delta"] != 0,
        "isolated_piece_B_changed": lambda value: value["isolated_piece_B_delta"] != 0,
        "old_proxy_changed": lambda value: value["old_ACACCC_proxy_delta"] != 0,
    }
    for dataset, indices in sorted(by_dataset.items()):
        for condition, predicate in conditions.items():
            selected = [i for i in indices if predicate(summaries[i])]
            output.append({"dataset": dataset, "condition": condition, "rows": len(selected),
                "parent_contexts": len({rows[i]["parent_context_id"] for i in selected}),
                "biological_components": len({rows[i]["biological_component"] for i in selected}),
                "unique_parent_sequences": len({rows[i]["parent_sequence"] for i in selected}),
                "unique_mutant_sequences": len({rows[i]["mutant_sequence"] for i in selected}),
                "unique_allele_pairs": len({(rows[i]["parent_sequence"], rows[i]["mutant_sequence"]) for i in selected})})
    return output


def run_coverage() -> None:
    manifest = check_freeze()
    inventories = {scope: read_inventory(path) for scope, path in INVENTORIES.items()}
    identity_check(inventories["original"], inventories["encoded"])
    aggregate = []
    row_output = []
    lengths = {}
    for scope, rows in inventories.items():
        contrasts = [contrast(row["parent_sequence"], row["mutant_sequence"]) for row in rows]
        assert all(1 <= value["edit_count"] <= 6 for value in contrasts)
        for row, summary in zip(rows, contrasts):
            row_output.append({"scope": scope, **{key: row[key] for key in FIELDS[:4]}, **summary})
        aggregate += [{"scope": scope, **summary} for summary in summarize(rows, contrasts)]
        lengths[scope] = dict(sorted(Counter(len(row["parent_sequence"]) for row in rows).items()))
    save(OUT / "coverage_rows.csv.gz", gzip.compress(csv_bytes(row_output), mtime=0))
    save(OUT / "coverage_by_assay.csv", csv_bytes(aggregate))
    support = [row for row in aggregate if row["condition"] == "geometry_changed"]
    receipt = {"status": "COMPLETE_DESCRIPTIVE_FEASIBILITY", "supervised_fits": 0,
        "outcomes_read": False, "protected_outcomes_opened": False,
        "design_freeze_sha256": sha256(MANIFEST), "design_files": manifest["file_count"],
        "rows_per_inventory": 26258, "parent_lengths": lengths,
        "paired_geometry_edit_support": support,
        "Mikl_unit_scope": "whole-gene biological components per committed crosscell metadata contract",
        "other_unit_scope": "supplied conservative biological components; no invented gene-symbol mapping",
        "input_files": {str(path.relative_to(ROOT).as_posix()): sha256(path) for path in INVENTORIES.values()},
        "result_files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in
                         (OUT / "coverage_rows.csv.gz", OUT / "coverage_by_assay.csv")}}
    check_freeze()
    jsave(OUT / "coverage_receipt.json", receipt)
    lines = ["# Exact zipcode geometry: outcome-blind coverage", "",
             "The published10–25 intervening-base rule was frozen and committed before this scan. No effect, rank or model outcome was read. Original and encoded contexts are descriptive comparisons; neither selects a model or subgroup.", "",
             "| Input | Assay | Edited rows changing valid pairs | Parent contexts | Biological components | Unique allele pairs |",
             "|---|---|---:|---:|---:|---:|"]
    lines += ["| {scope} | {dataset} | {rows} | {parent_contexts} | {biological_components} | {unique_allele_pairs} |".format(**row) for row in support]
    lines += ["", "Mikl units are certified whole genes. Other units are inherited conservative biological components, not automatically independent named genes. Cell/reporter parent contexts are counted without inventing additional metadata. Repeated cells of the same allele are not additional independent sequences.", "",
              "Counts alone cannot justify broad modeling or mechanism attribution. The paired-site prior is a refinement of the old isolated ACACCC proxy; future modeling would require isolated-piece/proxy controls and full-menu, source-only evaluation. SRLE encoded46 includes certified local construction arms, not a reconstructed full mature transcript. No spacing, motif, assay or threshold was changed after coverage.", "",
              "See coverage_by_assay.csv for WT/mutant presence, net-count change versus pair turnover, isolated-piece/proxy controls and independent-unit counts. coverage_rows.csv.gz contains sequence-only row summaries. No positive-result gate was applied."]
    save(REP / "feasibility.md", ("\n".join(lines) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "support": support}, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("freeze", "coverage"))
    arguments = parser.parse_args()
    {"freeze": freeze, "coverage": run_coverage}[arguments.command]()


if __name__ == "__main__":
    main()
