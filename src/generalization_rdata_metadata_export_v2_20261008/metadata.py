"""Literal design columns; bound the annotation subtree, not unrelated count objects."""
import math
from src.generalization_rdata_metadata_feasibility_20261008 import decode as d
ALLOW=("tileID","group","mutType","mutLoc","type","mutation","idx","coord","region","bpLoc5prime","bpLoc3prime")
INTEGER_FIELDS=frozenset(("mutLoc","idx","bpLoc5prime","bpLoc3prime"))
SAFE=frozenset(("NIL","NILVALUE","SYM","LIST","CHAR","STR","INT","REAL","LGL","VEC","REF"))
def count_metadata_nodes(obj,cap=500000,edge_cap=1000000):
    stack=[(obj,False)];seen=set();active=set();edges=0
    while stack:
        current,leaving=stack.pop()
        if current is None or not hasattr(current,"info"):continue
        identity=id(current)
        if leaving:active.remove(identity);continue
        assert identity not in active,"Cycle in annotation subtree"
        if identity in seen:continue
        assert current.info.type.name in SAFE,"Unsupported RObject in annotation subtree"
        seen.add(identity);active.add(identity)
        assert len(seen)<=cap,"Annotation RObject node cap exceeded"
        stack.append((current,True))
        children=[current.attributes,current.tag,current.referenced_object]
        if hasattr(current.value,"info"):children.append(current.value)
        elif isinstance(current.value,(tuple,list)):
            assert len(current.value)<=10000,"Metadata vector length cap exceeded"
            children.extend(v for v in current.value if hasattr(v,"info"))
        elif current.info.type.name in ("INT","REAL","LGL"):
            assert len(current.value)<=10000,"Metadata numeric vector length cap exceeded"
        if current.info.type.name=="CHAR":
            assert current.value is None or isinstance(current.value,bytes) and len(current.value)<=10000
        edges+=sum(child is not None for child in children)
        assert edges<=edge_cap,"Metadata graph edge cap exceeded"
        stack.extend((child,False) for child in reversed(children) if child is not None)
    return len(seen)
def column(obj,allow_number=False):
    obj=d.deref(obj)
    if d.kind(obj)!="REAL":return d.column(obj,allow_number)
    assert allow_number,"REAL design metadata not explicitly allowed"
    attributes=d.attrs(obj)
    assert "class" not in attributes,"Classed REAL design metadata unsupported"
    values=obj.value.tolist();assert len(values)<=10000
    result=[]
    for value in values:
        if value is None:result.append(None);continue
        assert type(value) is float
        if math.isnan(value):result.append(None);continue
        assert math.isfinite(value) and value.is_integer() and abs(value)<=2**53,"Nonintegral or unsafe REAL design metadata"
        result.append(int(value))
    return result,{"type":"integer_valued_REAL_design_metadata","missing_NA_or_NaN_preserved_as_null":True}
def select_annotation(root):
    globals_=d.pairs(root)
    assert "tile.annot" in globals_,"STOP_METADATA_MISSING"
    return globals_,globals_["tile.annot"]
def export(annotation):
    nodes=count_metadata_nodes(annotation);columns=d.columns(annotation)
    assert "tileID" in columns
    rows={};meta={}
    for name in ALLOW:
        if name in columns:
            rows[name],meta[name]=column(columns[name],name in INTEGER_FIELDS)
    length=len(rows["tileID"])
    assert 0<length<=5000 and all(isinstance(x,str) and x for x in rows["tileID"])
    assert len(set(rows["tileID"]))==length,"Duplicate tile IDs"
    assert all(len(values)==length for values in rows.values()),"Unequal annotation columns"
    for obj in columns.values():
        obj=d.deref(obj)
        assert d.kind(obj) in ("STR","INT","REAL","LGL"),"Nested or nonscalar annotation column"
        assert len(obj.value)==length,"Unequal unexported annotation column"
    return {"all_annotation_column_names":list(columns),"exported_allowlist_columns":list(rows),"column_metadata":meta,
            "rows":[{name:col[i] for name,col in rows.items()} for i in range(length)],
            "annotation_RObject_nodes":nodes,"parent_mutant_ancestry_admitted":False}
