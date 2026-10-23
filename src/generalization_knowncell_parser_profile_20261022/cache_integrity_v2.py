"""Bind possible existing bytecode payloads; do not assert they were executed."""
from pathlib import Path
from .common import sha


def possible_cache_proof(modules, prefix, expected, hasher=sha):
    prefix=Path(prefix).resolve(); observed={}; no_existing=[]
    for name,module in tuple(modules.items()):
        source=getattr(module,'__file__',None)
        if not source: continue
        source=Path(source).resolve()
        if not source.is_relative_to(prefix): continue
        assert source.relative_to(prefix).as_posix() in expected
        cached=getattr(module,'__cached__',None)
        if cached is None:
            no_existing.append(name);continue
        assert isinstance(cached,str), 'Invalid module cache path'
        path=Path(cached)
        assert not path.is_symlink(), 'Symlink cache path is not admitted'
        if not path.exists():
            no_existing.append(name);continue
        assert path.is_file() and path.suffix.lower()=='.pyc'
        resolved=path.resolve()
        assert resolved.is_relative_to(prefix), 'Existing cache outside pinned prefix'
        relative=resolved.relative_to(prefix).as_posix()
        assert relative in expected, 'Existing bytecode cache is not pinned'
        assert hasher(resolved)==expected[relative], 'Existing bytecode cache changed'
        observed[name]={'attribute_path':cached,'resolved_path':str(resolved),
                        'relative_path':relative,'sha256':expected[relative]}
    return {'status':'PASS_EXISTING_POSSIBLE_BYTECODE_PAYLOADS_BOUND',
            'possible_existing_bytecode_payloads':observed,
            'modules_without_existing_cache':sorted(no_existing),
            'execution_from_cache_established':False,
            'missing_cache_allowed_with_no_bytecode_writes':True}
