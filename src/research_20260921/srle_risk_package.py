"""Package existing anonymous risk summaries; never reads parent-level outcomes."""

from pathlib import Path
import io
import json
import subprocess
import sys
import zipfile

from .common import ROOT, sha256, write_json, write_new
from .srle_risk_replay import MEMBERS, replay, require
import numpy as np


OUT = ROOT / "results/research_20260921"
REPORTS = ROOT / "reports/research_20260921"
RELEASE = OUT / "srle_risk_replay_20260924"
ZIP_PATH = OUT / "srle_risk_replay_20260924.zip"
RECEIPT = OUT / "srle_risk_replay_receipt_20260924.json"
FRESH = ROOT / "data/interim/research_20260921/srle_risk_replay_fresh_20260924"
PINNED_RESULTS = {
    "fixed_result.json": ("srle_fixed_choice_risk_result_20260924.json", "e32881e75074551e76b1f7b32d925dd2364dd6f65ab056b81e0195d8829f71d2"),
    "uniform_result.json": ("srle_uniform_risk_result_20260924.json", "0ab692ced989bdf36477e651bcdeb5a82c88319251c2fb96070549054da536fb"),
}
README = """# SRLE fixed-choice and exact-uniform risk arithmetic replay

Run `python -I -S -B replay.py` in this extracted directory. Python standard
library only: no installation, network, source repository, raw outcomes or
sequence identifiers are needed. The replay reads only explicit package members.

This validates aggregation arithmetic, not training, candidate enumeration,
biological replication, model selection, source measurements or an experimental
success gate. These are conditional, posthoc summaries from a shared constituent
experiment. PASS means that anonymous class aggregates reproduce archived
numbers; it does not mean that an independent biological hypothesis passed.

All four models and both requested directions are retained. The 60 composition
classes contain 592 retained parents; each class has equal weight. Percentages
are class-balanced means, not unweighted percentages of 592 parents. Positive
directed change is movement in the requested NRS direction. Negative change
means the opposite direction, not toxicity. NRS is a log2 compartment ratio,
not a percentage of molecules. The 0.1 scale is descriptive, not a validated
biological cutoff.

The fixed summaries contain 152 statistics, and the exact-uniform reference and
literal model-minus-uniform comparisons contain 190 statistics. Each has one
estimate and two descriptive CI endpoints: 1,026 numeric comparisons total.
Means use equally weighted sorted class IDs 0..59. The supplied 2,000 x 60
bootstrap indices were generated once with NumPy 1.26.4 default_rng(20260921),
integers(0,60,size=(2000,60)), and shared across every summary and contrast.
Replay uses math.fsum means and linear quantiles at 0.025 and 0.975; maximum
allowed absolute discrepancy is 1e-12. These CIs omit training uncertainty.

The uniform source summaries average all measured candidates per parent and
hold one candidate identity fixed across paired replicates. Nonlinear metrics
were computed per candidate before averaging. This package starts from saved
class aggregates and DOES NOT independently rederive candidate choices,
within-parent averages, sequence matching or the exact-uniform enumeration.
The comparison is model minus uniform for every metric, without sign reversal.
Higher benefit/mean and lower harm/loss are favorable; a positive difference
is not uniformly favorable across metrics. No new performance criterion is set.

Checks cover exact file/schema membership, SHA256 hashes, all expected class /
model / direction / replicate cells, consistent parent counts, finite values,
valid sign fractions, and all 342 estimates plus 684 CI endpoints. Original
result JSONs and specs are included for provenance. Metadata about original
rows, frozen sources and candidate rosters is carried from those results and
is not revalidated by anonymous aggregates. No raw source outcomes or sequences
are included. SHA256 verifies consistency with the supplied manifest; it is
not an authenticity guarantee if an adversary replaces both files and manifest.

The package builder and archive receipt remain in the source project. The
archive uses a fixed member allowlist and explicit safe extraction for its
isolated standard-library validation.
"""


def build():
    require(np.__version__ == "1.26.4", "Unexpected NumPy version for pinned bootstrap")
    sources = {}
    for target, (name, expected_hash) in PINNED_RESULTS.items():
        source = OUT / name
        require(sha256(source) == expected_hash, "Pinned result changed: " + name)
        sources[target] = source
    fixed = json.loads(sources["fixed_result.json"].read_text(encoding="utf-8"))
    uniform = json.loads(sources["uniform_result.json"].read_text(encoding="utf-8"))
    mappings = {
        "fixed_groups.csv": "srle_fixed_choice_risk_groups_20260924.csv",
        "fixed_pairs.csv": "srle_fixed_choice_risk_pairs_20260924.csv",
        "uniform_groups.csv": "srle_uniform_risk_groups_20260924.csv",
        "uniform_pairs.csv": "srle_uniform_risk_pairs_20260924.csv",
    }
    for target, name in mappings.items():
        source = OUT / name
        expected = fixed["output_hashes"] if target.startswith("fixed") else uniform["outputs"]
        require(sha256(source) == expected["results/research_20260921/" + name], "Archived CSV changed: " + name)
        sources[target] = source
    sources["fixed_spec.md"] = REPORTS / "srle_fixed_choice_risk_spec_20260924.md"
    sources["uniform_spec.md"] = REPORTS / "srle_uniform_risk_spec_20260924.md"
    require(sha256(sources["fixed_spec.md"]) == fixed["files"]["reports/research_20260921/srle_fixed_choice_risk_spec_20260924.md"],
            "Fixed specification changed")
    sources["replay.py"] = Path(__file__).with_name("srle_risk_replay.py")
    for target, source in sources.items():
        write_new(RELEASE / target, source.read_bytes())
    write_new(RELEASE / "README.md", README.encode("utf-8"))
    draws = np.random.default_rng(20260921).integers(0, 60, size=(2000, 60))
    buffer = io.StringIO(newline="")
    np.savetxt(buffer, draws, fmt="%d", delimiter=",")
    write_new(RELEASE / "bootstrap_indices.csv", buffer.getvalue().encode("ascii"))
    write_json(RELEASE / "provenance.json", {
        "scope": "Existing anonymous class aggregate replay only; no source outcomes, fitting or new metrics.",
        "inputs": {target: {"path": str(source.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(source)}
                   for target, source in sources.items()},
        "builder_sha256": sha256(Path(__file__)),
        "numpy_version": np.__version__, "bootstrap_generator": "numpy.random.default_rng(20260921).integers(0,60,size=(2000,60))",
        "bootstrap_indices_sha256": sha256(RELEASE / "bootstrap_indices.csv"),
        "expected_statistics": {"fixed": 152, "uniform_and_model_minus_uniform": 190},
        "expected_numeric_comparisons": 1026,
    })
    write_json(RELEASE / "integrity.json", {name: sha256(RELEASE / name) for name in MEMBERS})
    result = replay(RELEASE)
    write_json(OUT / "srle_risk_replay_validation_20260924.json", result)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name in MEMBERS + ("integrity.json",):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, (RELEASE / name).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    write_new(ZIP_PATH, archive.getvalue())
    expected_members = set(MEMBERS) | {"integrity.json"}
    interim_root = (ROOT / "data/interim/research_20260921").resolve()
    fresh = FRESH.resolve()
    require(fresh.parent == interim_root and not fresh.exists(), "Fresh extraction destination is not new or is outside the namespace")
    with zipfile.ZipFile(ZIP_PATH) as zipped:
        require(set(zipped.namelist()) == expected_members and len(zipped.namelist()) == len(expected_members),
                "Archive has unexpected or duplicate members")
        require(zipped.testzip() is None, "ZIP CRC failure")
        fresh.mkdir(parents=True, exist_ok=False)
        for info in zipped.infolist():
            target = (fresh / info.filename).resolve()
            require(target.parent == fresh and info.filename in expected_members and not info.is_dir(), "Unsafe archive member")
            require((info.external_attr >> 16) & 0o170000 == 0o100000, "Archive member is not a regular file")
            with target.open("xb") as handle:
                handle.write(zipped.read(info))
    command = [sys.executable, "-I", "-S", "-B", str(fresh / "replay.py")]
    completed = subprocess.run(command, cwd=fresh, check=True, capture_output=True, text=True, encoding="utf-8", timeout=120)
    require(completed.stderr == "", "Unexpected standalone stderr")
    standalone = json.loads(completed.stdout)
    require(standalone == result, "Standalone validation differs from in-project replay")
    standalone_path = OUT / "srle_risk_standalone_validation_20260924.json"
    write_json(standalone_path, standalone)
    receipt = {
        "status": "PASS", "scope": "Aggregation arithmetic only; not independent biological validation.",
        "zip_path": str(ZIP_PATH.relative_to(ROOT)).replace("\\", "/"), "zip_sha256": sha256(ZIP_PATH),
        "zip_bytes": ZIP_PATH.stat().st_size, "zip_members": len(expected_members),
        "member_sha256": {name: sha256(RELEASE / name) for name in sorted(expected_members)},
        "standalone_command": command, "fresh_extraction_directory": str(fresh),
        "standalone_validation_sha256": sha256(standalone_path), "validation": standalone,
        "builder_sha256": sha256(Path(__file__)), "replay_source_sha256": sha256(sources["replay.py"]),
    }
    write_json(RECEIPT, receipt)
    return receipt


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True, indent=2, allow_nan=False))
