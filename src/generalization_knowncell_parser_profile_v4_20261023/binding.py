"""Capture a Git-verified raw identity once; never redefine its expectation."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


def valid_sha(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def digest(raw):
    assert isinstance(raw,bytes)
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class BoundAdmission:
    manifest:dict
    initial_sha256:str


def bind_initial(raw,git_verified_raw,expected_sha=None):
    assert isinstance(raw,bytes) and isinstance(git_verified_raw,bytes)
    assert raw==git_verified_raw,'Manifest raw bytes differ from HEAD'
    initial=digest(raw)
    if expected_sha is not None:
        assert valid_sha(expected_sha),'Invalid expected manifest SHA argument'
        assert initial==expected_sha,'Child manifest differs from parent initially verified raw SHA'
    def unique(pairs):
        value={}
        for key,item in pairs:
            assert key not in value,'Duplicate manifest JSON key'
            value[key]=item
        return value
    data=json.loads(raw,object_pairs_hook=unique)
    assert isinstance(data,dict)
    return BoundAdmission(data,initial)


def observed_sha(path):
    return digest(Path(path).read_bytes())


def require_unchanged(path,admission):
    assert isinstance(admission,BoundAdmission) and valid_sha(admission.initial_sha256)
    actual=observed_sha(path)
    assert actual==admission.initial_sha256,('Manifest changed after initial Git verification: '
        +str(path)+' initial='+admission.initial_sha256+' observed='+actual)
    return actual


def guarded_call(path,admission,callback,*args,**kwargs):
    require_unchanged(path,admission)
    return callback(*args,**kwargs)


def child_expected(argv):
    assert len(argv)==2 and argv[0]=='--expected-manifest-sha','A parent-bound manifest SHA is mandatory'
    assert valid_sha(argv[1]),'Invalid parent-bound manifest SHA'
    return argv[1]
