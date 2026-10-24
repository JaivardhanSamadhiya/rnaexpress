"""Additive source/initial-identity checks; no project payload reader."""
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from src.generalization_knowncell_metadata_execution_v2_20261023 import common as v2
from src.generalization_knowncell_metadata_execution_v2_20261023 import supervise as original

ROOT=v2.ROOT
NS='generalization_knowncell_metadata_startup_retry_20261023'
OUT=ROOT/'results'/NS
MANIFEST=OUT/'execution_manifest.json'
V2_MANIFEST=v2.MANIFEST.relative_to(ROOT).as_posix()
V2_SHA='dccab5219dcc6a82e015a31e248748cef160ee2e0408105ddfd8e2a0c86e35f7'
OLD_BLOCKED=(v2.OUT/'supervisor_receipt.json').relative_to(ROOT).as_posix()
OLD_BLOCKED_SHA='071e5c006c5af60b752e249964b766596f271fa9aa6e296dc101ad003d3ac89a'
STATUS='FROZEN_ONE_EXPLICIT_PREWORKER_METADATA_STARTUP_RETRY_ADDON'
sha=v2.sha
read_json=v2.read_json
save_new=v2.save_new
source_mode=v2.source_mode
resource_failure=v2.resource_failure


@dataclass(frozen=True)
class Admission:
    addon_raw:bytes
    addon_sha256:str
    v2_raw:bytes
    v2_sha256:str

    def addon(self):return read_json(self.addon_raw)
    def original(self):return read_json(self.v2_raw)


def blocked_document(raw):
    record=read_json(raw)
    assert record['status']=='BLOCKED_ORIGINAL_METADATA_V2_STARTUP_FLOOR_NO_WORKER'
    assert record['worker_started'] is False and record['project_payloads_opened']==record['model_fits']==0
    assert record['automatic_retry'] is False and record['original_resource_guards_unchanged'] is True
    assert record['initial_committed_execution_manifest_sha256']==V2_SHA
    assert record['source_mode']['pycache_prefix']==str(v2.CACHE_PREFIX)
    assert record['source_mode']['cache_prefix_absent'] is True
    return record


def verify_sources(addon_sha,v2_sha):
    v2.valid_sha(addon_sha);assert v2_sha==V2_SHA
    raw=MANIFEST.read_bytes()
    assert sha(raw)==addon_sha,'Addon differs from initially Git-verified manifest bytes'
    document=read_json(raw)
    assert document['status']==STATUS
    assert document['files'][V2_MANIFEST]==V2_SHA and document['files'][OLD_BLOCKED]==OLD_BLOCKED_SHA
    assert document['original_worker_manifest_sha256']==v2_sha
    old=v2.verify_sources(v2_sha)
    assert len(old['files'])==75
    for name,want in document['files'].items():
        assert name==name.replace('\\','/') and not name.startswith('/') and ':' not in name and '..' not in name.split('/')
        assert sha((ROOT/name).read_bytes())==want,name
    blocked_document((ROOT/OLD_BLOCKED).read_bytes())
    source_mode()
    return document


def admitted():
    # Both exact manifests must be in HEAD; capture identities once, before birth.
    source_mode()
    raw=MANIFEST.read_bytes()
    committed=original.headless.GitFacade(subprocess).check_output(
        ['git','show','HEAD:'+MANIFEST.relative_to(ROOT).as_posix()],cwd=ROOT)
    assert raw==committed,'Addon manifest is not exact committed bytes'
    initial=sha(raw)
    old,old_sha=original.admitted()
    assert old_sha==V2_SHA
    old_raw=v2.MANIFEST.read_bytes()
    assert sha(old_raw)==old_sha and read_json(old_raw)==old
    blocked_raw=(ROOT/OLD_BLOCKED).read_bytes()
    assert original.headless.GitFacade(subprocess).check_output(
        ['git','show','HEAD:'+OLD_BLOCKED],cwd=ROOT)==blocked_raw,'First blocked receipt is not exact committed bytes'
    assert sha(blocked_raw)==OLD_BLOCKED_SHA
    verify_sources(initial,old_sha)
    return Admission(raw,initial,old_raw,old_sha)


def worker_paths():
    return (ROOT/v2.BUNDLE,v2.OUT/'worker.log',v2.OUT/'worker_completion.json')


def require_absent(paths):
    for path in paths:
        assert not os.path.lexists(path),'Preserve existing/partial attempt; no resume: '+str(path)


def wait_for_floor(wait_seconds,probe,monotonic,sleep):
    """Resource sampling only, never a worker retry; at most60 explicit seconds."""
    assert type(wait_seconds) is int and 0<=wait_seconds<=60
    started=monotonic();samples=0
    while True:
        state=probe();samples+=1
        failure=resource_failure(state,0)
        elapsed=monotonic()-started
        if failure is None or elapsed>=wait_seconds:
            return state,failure,elapsed,samples
        sleep(min(.25,wait_seconds-elapsed))
