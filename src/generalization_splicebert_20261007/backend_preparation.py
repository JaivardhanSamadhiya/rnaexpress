"""Official CPU wheel retrieval/inspection; no runtime or model imports.

Downloading and extracting data does not authorize model loading, conversion,
or inference. Existing metadata-only receipts remain immutable.
"""
from __future__ import annotations
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from .resources import ROOT, ART, OUT, MODEL, digest, jsave, save

WHEEL_METADATA = OUT / "cpu_wheel_metadata.json"
WHEELS = ART / "wheels"
RUNTIME = ART / "cpu_runtime"
ALLOWED_DOWNLOAD_HOSTS = {"download.pytorch.org", "download-r2.pytorch.org"}


def safe_member(name, destination=RUNTIME):
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    assert normalized == name and not path.is_absolute() and ".." not in path.parts
    assert not any(":" in part for part in path.parts)
    assert not name.endswith(".pth"), "Do not activate wheel startup hooks"
    target = (destination / name).resolve()
    assert target.is_relative_to(destination.resolve())
    return target


def download(mirror=False):
    metadata = json.loads(WHEEL_METADATA.read_text())
    assert metadata["official_index"] == "https://download.pytorch.org/whl/cpu/torch/"
    assert digest(ART / "official_cpu_index.html") == metadata["official_index_sha256"]
    published_url, expected = metadata["download_url"], metadata["published_sha256"]
    url = (urllib.parse.urlunsplit(urllib.parse.urlsplit(published_url)._replace(netloc="download.pytorch.org"))
           if mirror else published_url)
    assert urllib.parse.urlsplit(url).hostname in ALLOWED_DOWNLOAD_HOSTS
    path = WHEELS / metadata["wheel_filename"]
    WHEELS.mkdir(parents=True, exist_ok=True)
    final_url = url
    if not path.exists():
        partial = path.with_suffix(path.suffix + ".partial")
        assert not partial.exists(), "Preserve incomplete download; review before retrying"
        # Opening the official GET happens before any output file is created.
        try:
            response = urllib.request.urlopen(url, timeout=60)
        except urllib.error.HTTPError as error:
            jsave(OUT / ("cpu_wheel_mirror_GET_incident.json" if mirror else "cpu_wheel_GET_incident.json"), {
                "stage": "Official published CPU wheel GET before runtime/model use",
                "url": url, "http_status": error.code, "reason": str(error.reason),
                "downloaded": False, "metadata_only_receipt_preserved": True,
                "unsafe_load_attempted": False, "conversion_started": False,
                "inference_started": False, "authorization_bypass_attempted": False})
            print("Official GET unavailable:", error.code, error.reason, flush=True)
            return False
        with response:
            final_url = response.url
            assert urllib.parse.urlsplit(final_url).hostname in ALLOWED_DOWNLOAD_HOSTS
            assert response.status == 200
            expected_bytes = response.headers.get("Content-Length")
            checksum = hashlib.sha256(); count = 0
            with partial.open("xb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block); checksum.update(block); count += len(block)
                    if count % (32 * 1024 * 1024) == 0:
                        print("Official CPU wheel downloaded", count, "bytes", flush=True)
                output.flush(); os.fsync(output.fileno())
            assert expected_bytes is None or count == int(expected_bytes)
            assert checksum.hexdigest() == expected, "Published CPU wheel SHA256 mismatch; preserve partial"
            partial.rename(path)
    assert digest(path) == expected
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        assert len(metadata_names) == 1
        information = BytesParser().parsebytes(archive.read(metadata_names[0]))
        assert information["Name"].lower() == "torch" and information["Version"] == "2.6.0+cpu"
        for member in archive.infolist():
            safe_member(member.filename)
            assert ((member.external_attr >> 16) & 0o170000) != 0o120000, "Reject symbolic link member"
        licenses = [name for name in names if ".dist-info/" in name and name.rsplit("/", 1)[-1] == "LICENSE"]
        assert licenses
        save(ART / "torch_cpu_LICENSE", archive.read(licenses[0]))
        metadata_bytes = archive.read(metadata_names[0])
        save(ART / "torch_cpu_wheel_METADATA", metadata_bytes)
    jsave(OUT / "cpu_wheel_download_receipt.json", {
        "status": "PASS", "package": "torch", "version": "2.6.0+cpu",
        "wheel_path": path.relative_to(ROOT).as_posix(), "wheel_bytes": path.stat().st_size,
        "published_sha256": expected, "actual_sha256": digest(path),
        "official_index": metadata["official_index"], "published_GET_url": published_url,
        "GET_url": url, "final_url": final_url,
        "public_mirror_attempt": mirror, "same_published_wheel_sha_required": True,
        "METADATA_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "required_distributions": information.get_all("Requires-Dist", []),
        "license_path": (ART / "torch_cpu_LICENSE").relative_to(ROOT).as_posix(),
        "license_sha256": digest(ART / "torch_cpu_LICENSE"),
        "safe_member_count": len(names), "public_free": True,
        "runtime_extracted": False, "runtime_imported": False, "system_install_modified": False,
        "model_loaded": False, "conversion_started": False, "inference_started": False})
    print("Official CPU wheel verified; no model/runtime import", flush=True)
    return True


def extract():
    """Optional isolated preparation; performs no package import or installer."""
    receipt = json.loads((OUT / "cpu_wheel_download_receipt.json").read_text())
    wheel = ROOT / receipt["wheel_path"]
    assert digest(wheel) == receipt["actual_sha256"] == receipt["published_sha256"]
    files = {}
    with zipfile.ZipFile(wheel) as archive:
        for member in archive.infolist():
            target = safe_member(member.filename)
            if member.is_dir():
                continue
            # Chunked extraction keeps large native DLLs off the Python heap.
            target.parent.mkdir(parents=True, exist_ok=True)
            checksum = hashlib.sha256()
            with archive.open(member) as stream:
                if target.exists():
                    with target.open("rb") as existing:
                        while block := stream.read(1024 * 1024):
                            assert existing.read(len(block)) == block; checksum.update(block)
                        assert not existing.read(1)
                else:
                    with target.open("xb") as output:
                        while block := stream.read(1024 * 1024):
                            output.write(block); checksum.update(block)
            files[target.relative_to(RUNTIME).as_posix()] = checksum.hexdigest()
    actual = {path.relative_to(RUNTIME).as_posix() for path in RUNTIME.rglob("*") if path.is_file()}
    assert actual == set(files), "Isolated extracted runtime has unexpected files"
    jsave(OUT / "cpu_runtime_extraction_receipt.json", {
        "status": "PASS", "runtime_path": RUNTIME.relative_to(ROOT).as_posix(),
        "wheel_sha256": digest(wheel), "files": files, "package_imported": False,
        "system_install_modified": False, "model_loaded": False})
    print("Isolated CPU wheel extraction/hash parity PASS; package not imported", flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] in (["download"], ["download_mirror"], ["extract"])
    extract() if sys.argv[1] == "extract" else download(mirror=sys.argv[1] == "download_mirror")
