"""Fixed public PyPI wheel data preparation; no imports or installation."""
from __future__ import annotations
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import zipfile

from .resources import ROOT, ART, OUT, digest, jsave, save
from .backend_preparation import safe_member

RUNTIME = ART / "dependency_runtime"
PACKAGES = (("sympy", "1.13.1", "sympy-1.13.1-py3-none-any.whl"),
            ("mpmath", "1.3.0", "mpmath-1.3.0-py3-none-any.whl"),
            ("networkx", "3.4.2", "networkx-3.4.2-py3-none-any.whl"),
            ("jinja2", "3.1.6", "jinja2-3.1.6-py3-none-any.whl"),
            ("markupsafe", "3.0.3", "markupsafe-3.0.3-cp312-cp312-win_amd64.whl"))


def run():
    records, files = [], {}
    for name, version, filename in PACKAGES:
        metadata_url = "https://pypi.org/pypi/" + name + "/" + version + "/json"
        with urllib.request.urlopen(metadata_url, timeout=30) as response:
            metadata_bytes = response.read()
        metadata = json.loads(metadata_bytes)
        matches = [entry for entry in metadata["urls"] if entry["filename"] == filename]
        assert len(matches) == 1
        entry = matches[0]
        assert entry["url"].startswith("https://files.pythonhosted.org/packages/")
        save(ART / "dependency_metadata" / (name + "_" + version + ".json"), metadata_bytes)
        wheel = ART / "wheels" / filename
        if not wheel.exists():
            with urllib.request.urlopen(entry["url"], timeout=60) as response:
                payload = response.read()
            assert len(payload) == entry["size"] and hashlib.sha256(payload).hexdigest() == entry["digests"]["sha256"]
            save(wheel, payload)
        assert wheel.stat().st_size == entry["size"] and digest(wheel) == entry["digests"]["sha256"]
        with zipfile.ZipFile(wheel) as archive:
            metadata_names = [value for value in archive.namelist() if value.endswith(".dist-info/METADATA")]
            assert len(metadata_names) == 1
            information = BytesParser().parsebytes(archive.read(metadata_names[0]))
            assert information["Name"].lower() == name and information["Version"] == version
            licenses = []
            for member in archive.infolist():
                target = safe_member(member.filename, RUNTIME)
                assert ((member.external_attr >> 16) & 0o170000) != 0o120000
                if member.is_dir():
                    continue
                payload = archive.read(member)
                save(target, payload)
                files[target.relative_to(RUNTIME).as_posix()] = hashlib.sha256(payload).hexdigest()
                if ".dist-info/" in member.filename and any(token in member.filename.rsplit("/", 1)[-1].upper()
                                                          for token in ("LICENSE", "COPYING")):
                    licenses.append({"member": member.filename, "sha256": hashlib.sha256(payload).hexdigest()})
        assert licenses or information.get("License") or information.get("License-Expression")
        records.append({"package": name, "version": version, "wheel_filename": filename,
                        "wheel_sha256": digest(wheel), "wheel_bytes": wheel.stat().st_size,
                        "wheel_url": entry["url"], "metadata_url": metadata_url,
                        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
                        "license": information.get("License-Expression") or information.get("License") or metadata["info"].get("license"),
                        "license_members": licenses, "required_distributions": information.get_all("Requires-Dist", [])})
        print("Verified isolated dependency", name, version, flush=True)
    assert {path.relative_to(RUNTIME).as_posix() for path in RUNTIME.rglob("*") if path.is_file()} == set(files)
    jsave(OUT / "dependency_runtime_receipt.json", {
        "status": "PASS", "runtime_path": RUNTIME.relative_to(ROOT).as_posix(), "files": files,
        "packages": records, "public_free": True, "system_install_modified": False,
        "packages_imported": False, "model_loaded": False, "conversion_started": False,
        "existing_reused_dependencies": "Bundled setuptools84.0.0; workspace filelock3.32.4, fsspec2026.7.0, typing_extensions4.16.0; source/runtime identities pinned before model work"})


if __name__ == "__main__":
    assert not sys.argv[1:]
    run()
