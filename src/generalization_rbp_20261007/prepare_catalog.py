"""Acquire only official human PFM/evidence metadata; no project outcomes.

This file resolves the public download form instead of guessing an archive URL.
No downloaded executable or pickle is imported or evaluated.
"""

from pathlib import Path
import datetime
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NS = "generalization_rbp_20261007"
ART = ROOT / "artifacts" / NS
OUT = ROOT / "results" / NS
REP = ROOT / "reports" / NS
OFFICIAL = "https://cisbp-rna.ccbr.utoronto.ca/"
MAX_BYTES = 20 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path = Path(path).resolve()
    assert any(path.is_relative_to(base) for base in (ART, OUT, REP))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, "Preserve existing artifact " + str(path)
    else:
        path.write_bytes(data)


def jsave(path, value):
    save(path, (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def retrieve(url, payload=None):
    assert url.startswith(OFFICIAL), "Only the official academic catalog is admitted"
    request = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(request, timeout=45) as response:
        assert response.url.startswith(OFFICIAL)
        declared = response.headers.get("Content-Length")
        if declared:
            assert int(declared) <= MAX_BYTES
        data = response.read(MAX_BYTES + 1)
        assert len(data) <= MAX_BYTES
        return data, {
            "requested_url": url,
            "final_url": response.url,
            "http_status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "bytes": len(data),
            "sha256": digest(data),
            "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


def acquire():
    receipt_path = ART / "resource_receipt.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        for name, checksum in receipt["saved_files"].items():
            assert digest((ROOT / name).read_bytes()) == checksum, name
        print("Existing official resource replay verified", flush=True)
        return receipt
    bulk, bulk_meta = retrieve(OFFICIAL + "bulk.php")
    html = bulk.decode("utf-8")
    assert 'value="Homo_sapiens"' in html
    assert 'name="Spec[]" value="RBP_Information"' in html
    assert 'name="Spec[]" value="PFMs"' in html
    form = re.search(r'<form\b[^>]*action="([^"]+)"[^>]*>', html, re.I)
    assert form and form.group(1) == "bulk_archive.php"
    endpoint = urllib.parse.urljoin(bulk_meta["final_url"], form.group(1))
    fields = [("selSpec", "Homo_sapiens"), ("Spec[]", "RBP_Information"),
              ("Spec[]", "PFMs"), ("submit", "Download Species Archive!")]
    answer, answer_meta = retrieve(endpoint, urllib.parse.urlencode(fields).encode())
    links = re.findall(r'href=[\"\']([^\"\']+)', answer.decode("utf-8"), re.I)
    archives = [link for link in links if link.startswith("tmp/Homo_sapiens_") and link.endswith(".zip")]
    assert len(archives) == 1, "Resolve exactly one actual official archive link"
    archive_url = urllib.parse.urljoin(answer_meta["final_url"], archives[0])
    archive, archive_meta = retrieve(archive_url)
    assert zipfile.is_zipfile(io.BytesIO(archive))
    main, main_meta = retrieve(OFFICIAL)
    help_bytes, help_meta = retrieve(OFFICIAL + "help.html")
    assert "2.00" in main.decode("utf-8") and "2_00" in answer.decode("utf-8")
    snapshots = {
        ART / "official_bulk_form.html": bulk,
        ART / "official_archive_response.html": answer,
        ART / "official_home.html": main,
        ART / "official_help.html": help_bytes,
        ART / "official_human_pfms_evidence.zip": archive,
    }
    for path, data in snapshots.items():
        save(path, data)
    members = []
    with zipfile.ZipFile(io.BytesIO(archive)) as opened:
        for info in opened.infolist():
            name = info.filename.replace("\\", "/")
            assert not name.startswith("/") and ".." not in name.split("/")
            assert not info.flag_bits & 1, "No encrypted/private entries admitted"
            members.append({"name": name, "bytes": info.file_size})
    receipt = {
        "scope": "Official public human RBP PFMs and motif evidence only; no localization outcome",
        "official_host": OFFICIAL,
        "database_build": "2.00",
        "reported_last_update": "7-5-2025 (official displayed string; no locale date assumption)",
        "actual_resolved_download_url": archive_url,
        "request_form_fields": fields,
        "resources": [bulk_meta, answer_meta, archive_meta, main_meta, help_meta],
        "archive_members": members,
        "saved_files": {path.relative_to(ROOT).as_posix(): digest(data) for path, data in snapshots.items()},
        "public_access": "Anonymous HTTPS official university site, no login or payment required",
        "free_access": True,
        "trusted_publisher": "CisBP-RNA, Hughes/Weirauch resource at University of Toronto",
        "resource_article": "https://doi.org/10.1093/nar/gkaf1081",
        "resource_article_license": "CC BY 4.0 (paper only)",
        "standalone_catalog_license": "Not located on inspected home/help/bulk pages; archive inspection pending",
        "redistribution_policy": "Internal computational research use only until catalog redistribution terms certified; cite source",
        "paid_resources": False,
        "protected_outcomes_opened": False,
        "project_features_computed": False,
        "supervised_models_fit": 0,
        "executable_downloads": False,
    }
    jsave(receipt_path, receipt)
    print(json.dumps({"status": "OFFICIAL_RESOURCE_DOWNLOADED", "bytes": len(archive),
                      "members": len(members), "url": archive_url,
                      "sha256": digest(archive)}, indent=2), flush=True)
    return receipt


if __name__ == "__main__":
    acquire()
