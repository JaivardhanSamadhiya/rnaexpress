"""Exact blocked global edit-distance graph over original 150-nt inserts."""
from .common import *
import importlib,importlib.metadata,itertools,time
from collections import defaultdict
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein

def runtime_binding():
    assert importlib.metadata.version('rapidfuzz')=='3.14.1'
    base=ROOT/'data/interim/mechanism_v2/runtime'
    native_cdist=importlib.import_module(process.cdist.__module__)._cdist
    names={'rapidfuzz','rapidfuzz.process','rapidfuzz.distance.Levenshtein',Levenshtein.distance.__module__,process.cdist.__module__,native_cdist.__module__}
    files={}
    for name in sorted(names):
        path=Path(importlib.import_module(name).__file__).resolve()
        assert path.is_relative_to(base.resolve()),str(path)
        files[path.relative_to(ROOT).as_posix()]=sha256(path)
    distribution=importlib.metadata.distribution('rapidfuzz')
    for entry in distribution.files or []:
        if entry.name in {'METADATA','LICENSE','LICENSE.txt','LICENSE.md'}:
            path=Path(distribution.locate_file(entry)).resolve()
            assert path.is_relative_to(base.resolve())
            files[path.relative_to(ROOT).as_posix()]=sha256(path)
    assert 'cpp' in Levenshtein.distance.__module__
    return {'version':'3.14.1','distance_scorer':Levenshtein.distance.__module__,
            'cdist':process.cdist.__module__,'native_cdist':native_cdist.__module__,'files':files,'workers':WORKERS,
            'weights':[1,1,1],'processor':None,'score_cutoff':CUTOFF,
            'dtype':'int16','block':BLOCK}

def reference_distance(left,right):
    """Independent full Wagner-Fischer unit edit distance for synthetic checks."""
    prior=list(range(len(right)+1))
    for i,a in enumerate(left,1):
        current=[i]
        for j,b in enumerate(right,1):
            current.append(min(current[-1]+1,prior[j]+1,prior[j-1]+(a!=b)))
        prior=current
    return prior[-1]

def distance_matrix(queries,choices,cutoff=CUTOFF):
    return process.cdist(queries,choices,scorer=Levenshtein.distance,processor=None,
                         score_cutoff=cutoff,scorer_kwargs={'weights':(1,1,1)},
                         dtype=np.int16,workers=WORKERS)

class Union:
    def __init__(self,names):self.parent={name:name for name in names}
    def root(self,name):
        trail=[]
        while name!=self.parent[name]:trail.append(name);name=self.parent[name]
        for item in trail:self.parent[item]=name
        return name
    def join(self,left,right):
        a,b=self.root(left),self.root(right)
        if a!=b:self.parent[max(a,b)]=min(a,b)

def inventory(frame):
    assert 'measured_delta' not in frame
    assert frame.groupby('gene_transcript').biological_component.nunique().eq(1).all()
    assert frame.groupby('biological_component').gene_transcript.nunique().eq(1).all()
    owners=defaultdict(set)
    roles=defaultdict(set)
    for role in ('parent_sequence','mutant_sequence'):
        for sequence,component in frame[[role,'biological_component']].itertuples(index=False,name=None):
            assert len(sequence)==LENGTH and set(sequence)<=set('ACGT')
            owners[sequence].add(component);roles[sequence].add(role)
    rows=[]
    for sequence in sorted(owners):
        rows.append({'allele_sha256':hashlib.sha256(sequence.encode()).hexdigest(),
                     'sequence':sequence,'components':'|'.join(sorted(owners[sequence])),
                     'roles':'|'.join(sorted(roles[sequence]))})
    return pd.DataFrame(rows),owners

def build_graph(frame,progress=None):
    roster,owners=inventory(frame)
    sequences=roster.sequence.tolist();components=sorted(frame.biological_component.unique())
    union=Union(components);edges={};exact_alleles=0
    def witness(left,right,distance):
        left_hash=hashlib.sha256(left.encode()).hexdigest();right_hash=hashlib.sha256(right.encode()).hexdigest()
        used=set()
        for owner_a in sorted(owners[left]):
            for owner_b in sorted(owners[right]):
                if owner_a==owner_b:continue
                a,b=sorted((owner_a,owner_b));key=(a,b)
                if key in used:continue
                used.add(key)
                a_sequence,b_sequence=(left,right) if owner_a==a else (right,left)
                a_hash,b_hash=(left_hash,right_hash) if owner_a==a else (right_hash,left_hash)
                item={'component_a':a,'component_b':b,'distance':int(distance),
                      'allele_a_sha256':a_hash,'allele_b_sha256':b_hash,
                      'hamming_distance':sum(x!=y for x,y in zip(left,right)),
                      'left_distinct_4mers':len({a_sequence[i:i+4] for i in range(LENGTH-3)}),
                      'right_distinct_4mers':len({b_sequence[i:i+4] for i in range(LENGTH-3)}),
                      'cross_gene_allele_pairs':1}
                if key not in edges:edges[key]=item
                else:
                    count=edges[key]['cross_gene_allele_pairs']+1
                    old=edges[key]
                    if (item['distance'],a_hash,b_hash)<(old['distance'],old['allele_a_sha256'],old['allele_b_sha256']):edges[key]=item
                    edges[key]['cross_gene_allele_pairs']=count
                union.join(a,b)
    # An exact allele owned by distinct genes joins them before nonidentical comparisons.
    for sequence in sequences:
        if len(owners[sequence])>1:exact_alleles+=1;witness(sequence,sequence,0)
    compared=0;native_pairs=0;cross_pairs=0;started=time.perf_counter()
    for start in range(0,len(sequences),BLOCK):
        stop=min(start+BLOCK,len(sequences));queries=sequences[start:stop];choices=sequences[start:]
        matrix=distance_matrix(queries,choices)
        assert matrix.shape==(stop-start,len(choices)) and matrix.min()>=0 and matrix.max()<=CUTOFF+1
        native_pairs+=matrix.size
        for local,i in enumerate(range(start,stop)):
            eligible=np.flatnonzero(matrix[local,(i-start+1):]<=CUTOFF)+(i+1)
            compared+=len(sequences)-i-1
            for j in eligible:
                left,right=sequences[i],sequences[int(j)]
                if len(owners[left]|owners[right])>1:
                    cross_pairs+=1;witness(left,right,int(matrix[local,int(j)-start]))
        if progress is not None:progress(stop,len(sequences),time.perf_counter()-started)
    assert compared==len(sequences)*(len(sequences)-1)//2
    groups=defaultdict(list)
    for component in components:groups[union.root(component)].append(component)
    group_rows=[]
    for members in sorted(groups.values()):
        identity='similarity_'+hashlib.sha256('|'.join(members).encode()).hexdigest()[:16]
        for component in members:group_rows.append({'biological_component':component,'similarity_component':identity,'family_size':len(members)})
    edge_columns=['component_a','component_b','distance','allele_a_sha256','allele_b_sha256','hamming_distance','left_distinct_4mers','right_distinct_4mers','cross_gene_allele_pairs']
    edge_frame=pd.DataFrame([edges[key] for key in sorted(edges)],columns=edge_columns)
    return roster,pd.DataFrame(group_rows),edge_frame,{
        'metadata_sha256':metadata_hash(frame),'unique_alleles':len(sequences),
        'original_gene_components':len(components),'similarity_components':len(groups),
        'largest_family':max(map(len,groups.values())),'unordered_nonidentical_allele_pairs_exhaustively_checked':compared,
        'native_distance_elements':native_pairs,'cross_gene_exact_shared_alleles':exact_alleles,
        'cross_gene_nonidentical_close_allele_pairs':cross_pairs,'direct_gene_edges':len(edges),
        'elapsed_seconds':time.perf_counter()-started,'runtime':runtime_binding()}
