"""Immutable official metadata requests; failures remain missing and never retry."""
from __future__ import annotations
from datetime import datetime, timezone
import json, time
from pathlib import Path
import urllib.error, urllib.parse, urllib.request
from . import common as c


def official(url):
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme == "https" and parsed.netloc == "api.genome.ucsc.edu" and parsed.path in ("/getData/track", "/getData/sequence")


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not official(newurl):
            raise urllib.error.URLError("Refuse nonofficial coordinate redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def cached(path, url, hasher=c.sha):
    """HTTP0/no-body failures do not hash missing files or trigger a retry."""
    path = Path(path)
    receipt = path.with_name(path.name + ".receipt.json")
    if not receipt.exists():
        assert not path.exists(), "Reject orphaned unbound response"
        return None, None
    item = c.read(receipt)
    assert item["url"] == url
    if item.get("sha256") is None:
        assert not path.exists(), "Missing-body failure unexpectedly acquired response bytes"
        prefix = item.get("oversize_prefix_path")
        if prefix:
            partial = (path.parent / prefix).resolve()
            assert partial.parent == path.parent.resolve() and not partial.is_symlink()
            assert hasher(partial) == item["oversize_prefix_sha256"]
        return None, item
    assert path.is_file() and hasher(path) == item["sha256"] and path.stat().st_size == item["bytes"]
    if item["http_status"] != 200 or item.get("failure"):
        return None, item
    return c.read(path), item


class Client:
    def __init__(self, allowed_urls, opener=None, sleep=time.sleep):
        self.allowed = set(allowed_urls)
        assert self.allowed and all(official(url) for url in self.allowed)
        self.opener = urllib.request.build_opener(OfficialRedirect()) if opener is None else opener
        self.sleep = sleep
        self.new_requests = 0

    def get(self, url, path):
        assert url in self.allowed and official(url), "Only fixed design URLs allowed"
        data, old = cached(path, url)
        if old is not None:
            return data, old
        path = Path(path)
        assert path.resolve().is_relative_to(c.ART.resolve()), "New caches stay inside this additive namespace"
        self.sleep(1.05)
        self.new_requests += 1
        request = urllib.request.Request(url, headers={"User-Agent": "RNA-localization-academic-reference-coordinate-audit/1.0"})
        item = {"url": url, "accessed_utc": datetime.now(timezone.utc).isoformat(), "bytes": 0, "sha256": None,
            "http_status": 0, "public_free": True, "account_or_payment": False,
            "terms_url": "https://genome.ucsc.edu/license/", "scope": "Official sequence/annotation coordinate metadata only; no scores or outcomes"}
        try:
            try:
                response = self.opener.open(request, timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                status = response.status if hasattr(response, "status") else response.code
                item.update(http_status=status, final_url=response.geturl(), content_type=response.headers.get("Content-Type", ""))
                assert official(item["final_url"])
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > c.MAX_RESPONSE:
                    item["failure"] = "response_declared_byte_cap_exceeded_no_body_read"
                    payload = None
                else:
                    payload = response.read(c.MAX_RESPONSE + 1) # one bounded sentinel byte detects an undeclared overflow
                    if len(payload) > c.MAX_RESPONSE:
                        prefix = path.with_name(path.name + ".oversize_prefix.bin")
                        c.save(prefix, payload[:c.MAX_RESPONSE])
                        item.update(failure="response_byte_cap_exceeded", oversize_prefix_path=prefix.name,
                            oversize_prefix_sha256=c.sha(prefix), observed_bytes_at_least=c.MAX_RESPONSE + 1)
                        payload = None
                if payload is not None:
                    c.save(path, payload)
                    item.update(bytes=len(payload), sha256=c.sha(path))
                    if status == 200:
                        try:
                            data = json.loads(payload)
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            item["failure"] = "invalid_reference_JSON"
                            data = None
                    else:
                        data = None
                else:
                    data = None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            item["failure"] = "transport_failure:" + str(error)
            data = None
        c.jsave(path.with_name(path.name + ".receipt.json"), item)
        return data, item
