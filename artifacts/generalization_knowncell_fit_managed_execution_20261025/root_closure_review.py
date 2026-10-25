"""Source-only import diagnostic, with explicitly reviewed dormant entrypoints."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path.cwd()
NS='generalization_knowncell_fit_managed_execution_20261025'
GENERATION='6d2c7bfdc0d8d03290882f3a409ec92f3895b56a2778b344b9d5d77e7cbaddcb'
DORMANT={
    ('src.generalization_splicebert_runtime_compatibility_20261007.launcher','run'),
    ('src.generalization_prelib_numpy_profile_20261022.invented','run'),
    ('src.generalization_prelib_numpy_profile_v2_20261022.invented','run'),
}


def existing(module):
    path=ROOT.joinpath(*module.split('.'))
    if path.with_suffix('.py').is_file():return path.with_suffix('.py')
    if (path/'__init__.py').is_file():return path/'__init__.py'


def nodes(node,module,prune):
    yield node
    if prune and isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and (module,node.name) in DORMANT:
        return
    for child in ast.iter_child_nodes(node):yield from nodes(child,module,prune)


def walk(pins,prune):
    seen=set();missing={};dynamic=[]
    queue=['src.'+NS+'.'+suffix for suffix in
        ('common','inputs','build','calibration','monitor','projection_io','worker','terminal','journal','supervise')]
    while queue:
        module=queue.pop()
        if module in seen:continue
        path=existing(module)
        if path is None:continue
        seen.add(module);name=path.relative_to(ROOT).as_posix();raw=path.read_bytes()
        actual=hashlib.sha256(raw).hexdigest()
        if pins.get(name)!=actual:missing[name]={'actual':actual,'pin':pins.get(name)}
        package=module if path.name=='__init__.py' else module.rpartition('.')[0]
        for node in nodes(ast.parse(raw),module,prune):
            if isinstance(node,ast.Import):queue.extend(a.name for a in node.names if a.name.startswith('src.'))
            elif isinstance(node,ast.ImportFrom):
                absolute=importlib.util.resolve_name('.'*node.level+(node.module or ''),package) if node.level else node.module
                if absolute and absolute.startswith('src'):
                    queue.append(absolute)
                    queue.extend(absolute+'.'+a.name for a in node.names if a.name!='*' and existing(absolute+'.'+a.name))
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='import_module' and node.args:
                first=node.args[0]
                if isinstance(first,ast.Constant) and isinstance(first.value,str) and first.value.startswith('src.'):
                    queue.append(first.value)
                else:dynamic.append({'module':module,'line':node.lineno,'expression':ast.unparse(first)})
    for module in seen:
        path=existing(module).parent
        while path.is_relative_to(ROOT/'src'):
            init=path/'__init__.py'
            if init.is_file():
                name=init.relative_to(ROOT).as_posix();actual=hashlib.sha256(init.read_bytes()).hexdigest()
                if pins.get(name)!=actual:missing[name]={'actual':actual,'pin':pins.get(name)}
            path=path.parent
    return {'workspace_modules':sorted(seen),'module_count':len(seen),'missing':missing,
        'dynamic_imports_separately_reviewed_as_fixed_targets':dynamic}


def main():
    raw=(ROOT/'results'/NS/'preparation_manifest.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==GENERATION
    pins=json.loads(raw)['files']
    broad=walk(pins,False);scoped=walk(pins,True)
    assert broad['module_count']==98 and len(broad['missing'])==4
    assert not scoped['missing']
    value={'status':'PASS_REVIEWED_FIT_FUNCTION_SCOPED_CLOSURE_NOT_UNIVERSAL_IMPORT_CLOSURE',
        'generation_manifest_sha256':GENERATION,'unscoped_diagnostic':broad,'scoped_diagnostic':scoped,
        'excluded_dormant_function_bodies':[list(item) for item in sorted(DORMANT)],
        'scope_requires_reviewed_fixed_production_entrypoints':True,
        'scientific_modules_executed_native_calls_payload_reads_or_jobs':0}
    out=ROOT/'results'/NS/'root_source_closure.json'
    with out.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(value['status'],scoped['module_count'])


if __name__=='__main__':main()
