
"""Bounded metadata-only RObject traversal, never stock class conversion."""
def deref(obj):
    seen=set()
    while obj is not None and obj.info.type.name=="REF":
        assert id(obj) not in seen and len(seen)<1000,"Reference cycle"
        seen.add(id(obj));obj=obj.referenced_object
    return obj
def kind(obj):
    obj=deref(obj);return "NONE" if obj is None else obj.info.type.name
def string(obj):
    obj=deref(obj)
    if kind(obj)=="SYM":return string(obj.value)
    assert kind(obj)=="CHAR","Not a literal R string"
    if obj.value is None:return None
    assert isinstance(obj.value,bytes) and len(obj.value)<=10000
    gp=obj.info.gp
    encoding="utf8" if gp & 8 else "latin1" if gp & 4 else "ascii"
    return obj.value.decode(encoding,errors="strict")
def pairs(obj,cap=10000):
    obj=deref(obj);result={};seen=set()
    while kind(obj) not in ("NILVALUE","NONE"):
        assert kind(obj)=="LIST" and id(obj) not in seen and len(seen)<cap
        seen.add(id(obj));name=string(obj.tag)
        assert name is not None and name not in result
        assert len(obj.value)==2
        result[name]=deref(obj.value[0]);obj=deref(obj.value[1])
    return result
def strings(obj):
    obj=deref(obj);assert kind(obj)=="STR"
    assert len(obj.value)<=10000
    return [string(value) for value in obj.value]
def attrs(obj):
    obj=deref(obj);return pairs(obj.attributes)
def column(obj,allow_number=False):
    obj=deref(obj);attributes=attrs(obj)
    classes=strings(attributes["class"]) if "class" in attributes else []
    assert set(classes)<=set(("factor","ordered")),"Unsupported selected R class"
    if kind(obj)=="STR":
        assert not classes;return strings(obj),{"type":"string","character_gp":[deref(v).info.gp for v in obj.value]}
    assert kind(obj)=="INT","Unsupported selected annotation vector"
    values=obj.value.tolist();assert len(values)<=10000
    if "factor" in classes:
        levels=strings(attributes["levels"])
        assert all(value is not None for value in levels)
        result=[]
        for value in values:
            if value is None or value==-2147483648:result.append(None)
            else:
                assert type(value) is int and 1<=value<=len(levels)
                result.append(levels[value-1])
        return result,{"type":"factor","levels":levels,"ordered":"ordered" in classes}
    assert not classes and allow_number,"Numeric column not allowed"
    assert all(value is None or type(value) is int for value in values)
    return [None if value==-2147483648 else value for value in values],{"type":"integer_design_metadata"}
def columns(obj):
    obj=deref(obj);assert kind(obj)=="VEC"
    attributes=attrs(obj);classes=strings(attributes["class"]) if "class" in attributes else []
    assert classes==["data.frame"],"Annotation is not a literal data.frame"
    names=strings(attributes["names"])
    assert all(name is not None for name in names) and len(names)==len(set(names))==len(obj.value)<=50
    return dict(zip(names,obj.value))
