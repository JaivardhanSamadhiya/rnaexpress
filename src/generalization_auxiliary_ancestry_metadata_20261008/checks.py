import re
COMPLEMENT=str.maketrans("ACGT","TGCA")
def single(rows,key,value):
    hits=[r for r in rows if r[key]==value]
    assert len(hits)==1,"Author WT lookup is not unique"
    return hits[0]
def coord(value):
    match=re.fullmatch(r"hTR:(\d+)-(\d+)",value)
    assert match
    start,end=map(int,match.groups());assert 0<start<=end
    return start,end
def index_set(value):
    assert isinstance(value,str) and value
    result=set()
    for part in value.split(","):
        match=re.fullmatch(r"(\d+)(?::(\d+))?",part)
        assert match,"Unsupported literal idx"
        start=int(match[1]);end=int(match[2] or match[1])
        assert 0<start<=end
        new=set(range(start,end+1));assert not new&result,"Overlapping idx segments"
        result|=new
    return result
def diff(parent,mutant):
    assert set(parent)<=set("ACGT") and set(mutant)<=set("ACGT")
    if len(parent)!=len(mutant):return None
    return {i+1:(a,b) for i,(a,b) in enumerate(zip(parent,mutant)) if a!=b}
def expected_check(parent,mutant,positions,ref_alt=None,complement=False):
    edits=diff(parent,mutant);assert edits is not None,"Unequal inferred insert lengths"
    assert set(edits)==set(positions),"Physical sequence changes disagree with author design coordinates"
    if ref_alt is not None:assert all(pair==ref_alt for pair in edits.values()),"Reference/alternate symbols disagree"
    if complement:assert all(a.translate(COMPLEMENT)==b for a,b in edits.values()),"Design complement is not basewise complement"
    return edits
def quartet_union(parent,arm5,arm3,comp):
    d5=diff(parent,arm5);d3=diff(parent,arm3);dc=diff(parent,comp)
    assert d5 is not None and d3 is not None and dc is not None
    assert not set(d5)&set(d3),"Mutation arms overlap"
    assert dc=={**d5,**d3},"Compensatory allele is not the exact union of side alleles"
    return True
def alias(pool,identifier):
    if pool=="wrap53mt":return identifier
    if pool=="ms2_4x":
        match=re.fullmatch(r"ms2-4x:(\d+)",identifier);assert match
        return "design:"+match[1]
    if pool=="hTR":
        match=re.fullmatch(r"hTR_(\d+)",identifier);assert match
        return "hTR:"+match[1]
    raise AssertionError("No generic identifier normalization")
