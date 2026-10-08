"""Public official wheel comparison and installed-byte snapshot; no imports/models."""
from __future__ import annotations

from email.parser import BytesParser
import json
from pathlib import PurePosixPath
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile

from .common import *


def package_member(name):
    assert isinstance(name, str) and name and "\\" not in name
    value = PurePosixPath(name)
    assert not value.is_absolute() and ".." not in value.parts and not any(":" in part for part in value.parts)
    return value.parts[0] in {"numpy", "numpy.libs"} and not name.endswith("/")


def acquire_numpy():
    metadata_path = ART / "pypi_numpy_1_26_4.json"
    if metadata_path.exists():
        metadata_bytes = metadata_path.read_bytes()
        metadata_status = 200
    else:
        with urllib.request.urlopen(PYPI, timeout=30) as response:
            assert response.status == 200 and urllib.parse.urlsplit(response.url).hostname == "pypi.org"
            metadata_bytes, metadata_status = response.read(), response.status
        save(metadata_path, metadata_bytes)
    metadata = json.loads(metadata_bytes)
    assert metadata["info"]["name"].lower() == "numpy" and metadata["info"]["version"] == NUMPY_VERSION
    # Versioned official metadata includes the permissive project/bundled licenses.
    license_text = metadata["info"]["license"]
    assert "Redistribution and use in source and binary forms" in license_text
    matches = [row for row in metadata["urls"] if row["filename"] == NUMPY_WHEEL]
    assert len(matches) == 1
    record = matches[0]
    assert record["packagetype"] == "bdist_wheel" and not record["yanked"]
    assert urllib.parse.urlsplit(record["url"]).hostname == "files.pythonhosted.org"
    wheel = ART / "wheels" / NUMPY_WHEEL
    actual_url, status = record["url"], 200
    if not wheel.exists():
        with urllib.request.urlopen(record["url"], timeout=30) as response:
            assert response.status == 200 and urllib.parse.urlsplit(response.url).hostname == "files.pythonhosted.org"
            payload, actual_url, status = response.read(), response.url, response.status
        assert len(payload) == record["size"]
        from hashlib import sha256 as hash_bytes
        assert hash_bytes(payload).hexdigest() == record["digests"]["sha256"]
        save(wheel, payload)
    assert wheel.stat().st_size == record["size"] and sha256(wheel) == record["digests"]["sha256"]
    files, mismatches, ignored = {}, [], []
    with zipfile.ZipFile(wheel) as archive:
        metadata_members = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        assert len(metadata_members) == 1
        information = BytesParser().parsebytes(archive.read(metadata_members[0]))
        assert information["Name"].lower() == "numpy" and information["Version"] == NUMPY_VERSION
        licenses = [name for name in archive.namelist() if name.endswith(".dist-info/LICENSE.txt")]
        assert len(licenses) == 1
        save(ART / "NumPy_LICENSE.txt", archive.read(licenses[0]))
        for member in archive.infolist():
            if member.is_dir():
                continue
            if not package_member(member.filename):
                ignored.append(member.filename)
                continue
            assert ((member.external_attr >> 16) & 0o170000) != 0o120000
            from hashlib import sha256 as hash_bytes
            expected = hash_bytes(archive.read(member)).hexdigest()
            installed = PREFIX / member.filename
            observed = sha256(installed) if installed.is_file() else None
            files[member.filename] = expected
            if observed != expected or installed.stat().st_size != member.file_size:
                mismatches.append({"path": member.filename, "published_member_sha256": expected, "installed_sha256": observed})
    actual_package_files = {path.relative_to(PREFIX).as_posix() for root in (PREFIX / "numpy", PREFIX / "numpy.libs")
                            for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"}
    extras = sorted(actual_package_files - set(files))
    receipt = {"status": "PASS" if not mismatches and not extras else "FAIL_PRESERVE_INSTALLED_BYTES",
        "official_API": PYPI, "API_HTTP_status": metadata_status,
        "API_metadata_sha256": sha256(metadata_path), "download_url": record["url"], "actual_url": actual_url,
        "wheel_HTTP_status": status, "wheel_path": wheel.relative_to(ROOT).as_posix(), "wheel_bytes": wheel.stat().st_size,
        "published_wheel_sha256": record["digests"]["sha256"], "actual_wheel_sha256": sha256(wheel),
        "public_free": True, "account_or_payment": False, "package": "numpy", "version": NUMPY_VERSION,
        "ABI": "cp312-cp312-win_amd64", "package_and_libs_member_count": len(files), "files": files,
        "mismatches": mismatches, "unexpected_nonbytecode_package_files": extras,
        "explicit_nonpackage_wheel_members_ignored": ignored,
        "parity_scope": "All numpy/ and numpy.libs/ code, data, native PYD and DLL members; installed bytecode excluded; dist-info/script installation differences not claimed equal",
        "license_path": (ART / "NumPy_LICENSE.txt").relative_to(ROOT).as_posix(),
        "license_sha256": sha256(ART / "NumPy_LICENSE.txt"),
        "installed_library_modified": False, "packages_imported": False, "model_work": False,
        "old_zero_byte_wheel_preserved_unused": str(PREFIX / NUMPY_WHEEL)}
    jsave(ART / "numpy_official_member_parity.json", receipt)
    assert receipt["status"] == "PASS", "Preserve mismatch; do not replace any installed library"
    print("Official NumPy member parity PASS", len(files), "members", flush=True)


def snapshot():
    parity = json.loads((ART / "numpy_official_member_parity.json").read_text(encoding="utf-8"))
    assert parity["status"] == "PASS"
    wheel_text = (PREFIX / "numpy-1.26.4.dist-info/WHEEL").read_text(encoding="utf-8")
    assert "Tag: cp312-cp312-win_amd64" in wheel_text
    metadata = BytesParser().parsebytes((PREFIX / "numpy-1.26.4.dist-info/METADATA").read_bytes())
    assert metadata["Name"].lower() == "numpy" and metadata["Version"] == NUMPY_VERSION
    files = {}
    for path in sorted(PREFIX.rglob("*")):
        assert not path.is_symlink(), "No scientific prefix symlinks"
        if path.is_file():
            assert path.resolve().is_relative_to(PREFIX.resolve())
            files[path.relative_to(PREFIX).as_posix()] = sha256(path)
    assert all(files[name] == checksum for name, checksum in parity["files"].items())
    native = {name: checksum for name, checksum in files.items()
              if name.split("/")[0] in {"numpy", "numpy.libs"} and name.endswith((".pyd", ".dll"))}
    assert native and all("cp312-win_amd64" in name for name in native if name.endswith(".pyd"))
    python_files = [Path(sys.executable), Path(sys.executable).parent / "python312.dll", Path(sys.executable).parent / "python3.dll"]
    assert all(path.is_file() for path in python_files)
    old = PREFIX / NUMPY_WHEEL
    jsave(RUNTIME_RECEIPT, {"status": "PASS", "numpy_version": NUMPY_VERSION,
        "runtime_path": str(PREFIX), "files": files, "file_count": len(files),
        "total_bytes": sum((PREFIX / name).stat().st_size for name in files),
        "numpy_native_files": native, "official_numpy_member_parity_sha256": sha256(ART / "numpy_official_member_parity.json"),
        "other_scientific_prefix_provenance": "Observed installed bytes, not freshly proven official-wheel parity",
        "python_executable": str(Path(sys.executable).resolve()), "python_cache_tag": sys.implementation.cache_tag,
        "python_native_files": {str(path.resolve()): sha256(path) for path in python_files},
        "old_unused_wheel_bytes": old.stat().st_size, "old_unused_wheel_sha256": sha256(old),
        "packages_imported": False, "model_loaded": False, "system_install_modified": False})
    print("Scientific prefix snapshot", len(files), "files; imports0", flush=True)


def freeze():
    no_completed_outputs()
    assert PLAN.is_file(), "Written reviewable repair plan required"
    committed(ORIGINAL_MANIFEST)
    tests = json.loads((OUT / "synthetic_tests_receipt.json").read_text(encoding="utf-8"))
    sources = {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(SRC.glob("*.py"))}
    assert tests["status"] == "PASS" and tests["source_hashes"] == sources
    runtime = json.loads(RUNTIME_RECEIPT.read_text(encoding="utf-8"))
    check_runtime(runtime)
    originals = json.loads(ORIGINAL_MANIFEST.read_text(encoding="utf-8"))["files"]
    # Preserve original design/input byte identity without invoking its guard/model code.
    for name, expected in originals.items():
        assert sha256(ROOT / name) == expected, name
    paths = [path for home in (SRC, ART, OUT, REP) for path in home.rglob("*") if path.is_file()]
    assert MANIFEST not in paths
    paths += [ORIGINAL_SOURCE, ORIGINAL_MANIFEST, ROOT / "src/research_20260921/common.py",
              ROOT / "logs/generalization_campaign_20261007/splicebert_backend_probe_retry_02.log"]
    jsave(MANIFEST, {"status": "FROZEN_ADDITIVE_NUMPY_COMPATIBILITY_PREPARATION",
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(paths))},
        "scientific_prefix_files": runtime["file_count"], "NumPy_ABI": "cp312-cp312-win_amd64",
        "original_guard_calls": 1, "original_guard_resource_checks": 2, "original_threads": 2,
        "NumPy_origin_check_before_Torch": True, "conversion_algorithm_unchanged": True,
        "monkeypatch": "temporary process-local original module guard binding only, restored in finally",
        "root_commit_and_explicit_start_required": True, "packages_imported": False,
        "project_alleles_authorized": 0, "synthetic_examples_unchanged": 16,
        "outcomes_read": False, "fits": 0, "old_freezes_modified": False})
    print("Repair preparation freeze", len(json.loads(MANIFEST.read_text())["files"]), sha256(MANIFEST), flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] in (["acquire_numpy"], ["snapshot"], ["freeze"])
    {"acquire_numpy": acquire_numpy, "snapshot": snapshot, "freeze": freeze}[sys.argv[1]]()
