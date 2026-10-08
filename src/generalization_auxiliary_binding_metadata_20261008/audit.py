"""Outcome-blind public auxiliary FASTA audit; inferred interiors are not RNA truth."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_auxiliary_binding_metadata_20261008'
RAW = ROOT / 'data/raw/generalization_auxiliary_binding_20261008'
OUT = ROOT / 'results' / NS
PREFIX = 'ACTGGCCGCTTCACTG'
SUFFIX = 'AGATCGGAAGAGCGTCG'
POOLS = {'ctcf':(985,24), 'hTR':(614,25), 'ms2_4x':(105,50), 'pum2':(1599,22), 'wrap53mt':(55,35)}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def save(path, value):
    path=Path(path).resolve(); assert path.is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f: f.write((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())


def fasta(path):
    records=[]; name=None; parts=[]
    with gzip.open(path,'rt',encoding='ascii') as f:
        for line in f:
            line=line.strip()
            if line.startswith('>'):
                if name is not None: records.append((name,''.join(parts)))
                name=line[1:]; parts=[]
                assert name
            else:
                assert name is not None and line and set(line)<=set('ACGT')
                parts.append(line)
        if name is not None: records.append((name,''.join(parts)))
    assert records and len({n for n,_ in records})==len(records)
    return records


def split_id(name, pool):
    if pool=='ms2_4x':
        match=re.fullmatch(r'(design:[0-9]+)\.([0-9]+)',name)
        assert match,name
        return match[1],int(match[2]),None
    match=re.fullmatch(r'(.+)_([0-9]+)(?:\.([ACGT]{10}))?',name)
    assert match,name
    return match[1],int(match[2]),match[3]


def inferred_interior(sequence):
    assert sequence.startswith(PREFIX) and sequence.endswith(SUFFIX)
    assert len(sequence)>len(PREFIX)+len(SUFFIX)+10
    # This is a DNA-layout inference tested against every supplied record.
    # No claim of source-certified primer boundaries or mature reporter RNA.
    middle=sequence[len(PREFIX):-len(SUFFIX)]
    return middle[:-10],middle[-10:]


def substitution_count(parent, mutant):
    return sum(a!=b for a,b in zip(parent,mutant)) if len(parent)==len(mutant) else None


def run():
    receipt_path=ROOT/'results/generalization_auxiliary_binding_20261008/acquisition_receipt.json'
    receipt=json.loads(receipt_path.read_text(encoding='utf8'))
    assert receipt['status']=='PASS_AUXILIARY_PUBLIC_ACQUISITION_ONLY'
    pins={receipt_path.relative_to(ROOT).as_posix():sha(receipt_path)}
    for row in receipt['records']:
        p=RAW/row['filename']; assert sha(p)==row['sha256']
        assert p.stat().st_size==row['bytes'] and row['http_status']==200
        pins[p.relative_to(ROOT).as_posix()]=sha(p)
    summaries=[]; tiles=[]
    for pool,(expected_tiles,copies) in POOLS.items():
        p=RAW/('GSE221537_'+pool+'_oligoPool.fasta.gz')
        records=fasta(p); assert len(records)==expected_tiles*copies
        groups=collections.defaultdict(list)
        for name,sequence in records:
            tile,barcode_id,named_barcode=split_id(name,pool)
            interior,barcode=inferred_interior(sequence)
            assert named_barcode is None or named_barcode==barcode
            groups[tile].append((barcode_id,interior,barcode))
        assert len(groups)==expected_tiles
        for tile,members in groups.items():
            assert len(members)==copies and {r[0] for r in members}==set(range(1,copies+1))
            assert len({r[1] for r in members})==1 and len({r[2] for r in members})==copies
            interior=members[0][1]
            tiles.append({'pool':pool,'source_named_tile':tile,'inferred_DNA_interior':interior,
                'inferred_interior_sha256':hashlib.sha256(interior.encode()).hexdigest(),
                'inferred_interior_length':len(interior),'technical_barcode_copies':copies,
                'explicit_author_mutation_ancestry_certified':False,'certified_mature_RNA':False})
        interiors=[m[0][1] for m in groups.values()]
        summaries.append({'pool':pool,'oligos':len(records),'source_named_tiles':len(groups),
            'technical_barcode_copies_per_tile':copies,'raw_oligo_lengths':dict(collections.Counter(len(s) for _,s in records)),
            'inferred_interior_lengths':dict(collections.Counter(map(len,interiors))),
            'distinct_inferred_interiors':len(set(interiors)),
            'all_records_observed_layout':True,'within_tile_interiors_identical':True,
            'source_named_barcodes_match_actual_sequence':pool in ('ctcf','pum2','wrap53mt')})
    headers={}
    for p in sorted(RAW.glob('*_count.txt.gz')):
        with gzip.open(p,'rt',encoding='ascii') as f: headers[p.name]=f.readline().rstrip('\n').rstrip('\r').split('\t')
    assert len(headers)==5
    with zipfile.ZipFile(RAW/'MPRNA-IP-v1.0.0.zip') as z:
        members=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()]
        functions=next(n for n in z.namelist() if n.endswith('/nar_functions.R'))
        script=next(n for n in z.namelist() if n.endswith('/nar_manuscript.Rmd'))
        rtext=z.read(script).decode('utf8')
        assert 'tileID.wt' in rtext and 'tile.annot' in rtext
        scripts={n:hashlib.sha256(z.read(n)).hexdigest() for n in (functions,script)}
    wrap=[r for r in tiles if r['pool']=='wrap53mt']
    parents=[r for r in wrap if r['source_named_tile']=='wt_1']; assert len(parents)==1
    parent=parents[0]['inferred_DNA_interior']
    provisional=[]
    for row in wrap:
        if row['source_named_tile']=='wt_1': continue
        edits=substitution_count(parent,row['inferred_DNA_interior'])
        provisional.append({'source_named_parent':'wt_1','source_named_candidate':row['source_named_tile'],
            'inferred_equal_length_substitution_count':edits,'within_1_to_6_if_ancestry_later_certified':edits is not None and 1<=edits<=6,
            'training_pair_admitted':False,'ancestry_not_inferred_from_sequence_distance':True})
    save(OUT/'inferred_tile_interiors.json',tiles)
    save(OUT/'wrap53_provisional_distance_metadata.json',provisional)
    files=dict(pins)
    for p in (OUT/'inferred_tile_interiors.json',OUT/'wrap53_provisional_distance_metadata.json'):
        files[p.relative_to(ROOT).as_posix()]=sha(p)
    save(OUT/'metadata_audit_receipt.json',{'status':'PASS_AUXILIARY_SEQUENCE_METADATA_ONLY',
        'files':files,'pools':summaries,'total_oligos':sum(s['oligos'] for s in summaries),
        'total_source_named_tiles':len(tiles),'count_headers_only':headers,
        'archive_members':members,'author_analysis_text_sha256':scripts,
        'inferred_DNA_layout':{'observed_prefix':PREFIX,'observed_suffix':SUFFIX,'inferred_barcode_length':10},
        'layout_matches_paper_157nt_for_standard_200nt_oligos':True,
        'source_certified_primer_boundaries':False,'full_mature_RNA_context_certified':False,
        'author_ancestry_metadata_missing_from_plain_FASTA':True,'Rdata_objects_decoded':False,
        'scientific_binding_count_values_analyzed':False,'localization_outcomes_read':False,
        'models_fit':0,'training_pairs_admitted':0,
        'MS2_four_tandem_hairpins_requires_actual_physical_edit_count':True,
        'WRAP53_pool_one_named_WT_parent_is_not_many_independent_genes':True})
    print('PASS auxiliary sequence metadata only; no training pairs, count analysis or models',flush=True)


if __name__=='__main__': run()
