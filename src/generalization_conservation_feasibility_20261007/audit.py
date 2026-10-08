"""Explicit metadata only; fixed small reference pilot, never outcomes or fits."""
from src.research_20260921 import common as _runtime_bootstrap
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import argparse, csv, gzip, hashlib, json, re, subprocess, time
import urllib.request, urllib.error
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_conservation_feasibility_20261007'
SRC, REP, OUT, ART = [ROOT / folder / NS for folder in ('src','reports','results','artifacts')]
INVENTORY = ROOT / 'artifacts/generalization_next_20261007/sequence_inventory.csv.gz'
CORE = ROOT / 'results/probabilistic_ranking_20260928/candidate_index.csv'
FASTA = ROOT / 'data/external/RNAloc_MPRA/Datasets/mouse_3utrs.txt'
NOTEBOOK = ROOT / 'data/external/RNAloc_MPRA/LibraryDesign.ipynb'
MIKL = ROOT / 'data/raw/mikl_gse173098/supplementary/files/SupplementaryData_NAR_Final/SupplementaryTables/TableS2.csv'
LINEAGE = ROOT / 'results/v4_phaseA/mikl_interventions.csv.gz'
ASTRO = ROOT / 'data/frozen/astrocyte_external_features.csv.gz'
COLS = ['intervention_id','dataset','biological_component','parent_context_id','parent_sequence','mutant_sequence']
GENES = ['intervention_id','gene_transcript','parent_id','mutant_id']
API = 'https://api.genome.ucsc.edu/'
MAX_REGION = 500_000
MAX_TOTAL = 2_000_000
MAX_RESPONSE = 4_000_000

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def save(path, data):
    path=Path(path).resolve(); assert any(path.is_relative_to(p.resolve()) for p in (SRC,REP,OUT,ART))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): assert path.read_bytes()==data, 'Preserve earlier feasibility bytes: '+str(path)
    else:
        with path.open('xb') as stream: stream.write(data)

def jsave(path, value):
    save(path,(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())

def csvsave(path, frame):
    raw=frame.to_csv(index=False,lineterminator='\n').encode()
    save(path,gzip.compress(raw,mtime=0) if str(path).endswith('.gz') else raw)

def occurrences(sequence, piece):
    starts=[]; first=sequence.find(piece)
    while first>=0:
        starts.append(first); first=sequence.find(piece,first+1)
    return starts

def reverse_complement(sequence):
    return sequence.translate(str.maketrans('ACGTN','TGCAN'))[::-1]

def references(genes):
    """Stream author FASTA; retain only requested sequence/gene metadata."""
    result=defaultdict(list); header=None; chunks=[]
    def emit():
        if header is None: return
        parts=header.split('|')
        assert len(parts)==6, 'Unexpected source FASTA metadata schema'
        if parts[2].casefold() not in genes: return
        seq=''.join(chunks).upper()
        if not re.fullmatch('[ACGT]+',seq): return
        result[parts[2].casefold()].append({'header':header,'gene_id':parts[0],'transcript_id':parts[1],
            'gene':parts[2],'chromosome':parts[3],'gene_start1':int(parts[4]),'gene_end1':int(parts[5]),
            'sequence':seq,'sequence_sha256':hashlib.sha256(seq.encode()).hexdigest()})
    with FASTA.open(encoding='utf8') as stream:
        for line in stream:
            if line.startswith('>'):
                emit(); header=line[1:].strip(); chunks=[]
            else: chunks.append(line.strip())
        emit()
    return result

def source_frame():
    prefit=ROOT/'results/generalization_next_20261007/prefit_manifest.json'
    manifest=json.loads(prefit.read_text())
    assert manifest['files'][INVENTORY.relative_to(ROOT).as_posix()]==sha(INVENTORY)
    f=pd.read_csv(INVENTORY,usecols=COLS,low_memory=False)
    assert f.columns.tolist()==COLS and len(f)==26258 and f.intervention_id.is_unique
    metadata=pd.read_csv(CORE,usecols=GENES,low_memory=False)
    assert metadata.intervention_id.is_unique and list(metadata.intervention_id)==list(f.intervention_id)
    return f.merge(metadata,on='intervention_id',validate='one_to_one',sort=False)

def local():
    assert not (OUT/'metadata_receipt.json').exists()
    f=source_frame(); refs=references(set(f.gene_transcript.str.casefold()))
    parents=f[['dataset','gene_transcript','parent_id','parent_sequence']].drop_duplicates().sort_values(['dataset','gene_transcript','parent_id'])
    assert not parents.duplicated(['dataset','parent_id']).any()
    records, coverage=[],{}
    for row in parents.itertuples(index=False):
        matches=[]
        if row.dataset!='srle':
            for ref in refs[row.gene_transcript.casefold()]:
                for start in occurrences(ref['sequence'],row.parent_sequence):
                    matches.append({k:v for k,v in ref.items() if k!='sequence'}|{'utr_insert_start0':start,'utr_insert_end0':start+len(row.parent_sequence)})
        status='synthetic_no_native_coordinates' if row.dataset=='srle' else ('no_exact_source_utr' if not matches else ('one_source_transcript_occurrence' if len(matches)==1 else 'multiple_source_transcript_occurrences'))
        records.append({'dataset':row.dataset,'gene':row.gene_transcript,'parent_id':row.parent_id,'parent_sequence':row.parent_sequence,
                        'parent_sequence_sha256':hashlib.sha256(row.parent_sequence.encode()).hexdigest(),'status':status,'reference_candidates':matches})
    for dataset in sorted(f.dataset.unique()):
        selected=[row for row in records if row['dataset']==dataset]
        coverage[dataset]={'interventions':int(f.dataset.eq(dataset).sum()),'genes':int(f.loc[f.dataset.eq(dataset),'gene_transcript'].nunique()),
            'parents':len(selected),'parent_status_counts':dict(Counter(row['status'] for row in selected)),
            'coordinate_certified_parents':0,'scope':'Exact source-UTR transcript candidate coverage only; no genomic-vector proof yet'}
    # Verify Mikl admitted parent metadata against actual sequence-only author rows.
    lineage=pd.read_csv(LINEAGE,usecols=['source_row','mutant_id','parent_sequence','mutant_sequence','gene_name','organism'])
    chosen=lineage[lineage.mutant_id.isin(f.loc[f.dataset.eq('mikl_gse173098'),'mutant_id'])].copy()
    assert chosen.mutant_id.is_unique and len(chosen)==6901
    author=pd.read_csv(MIKL,usecols=['gene name','position in 3UTR','subset','full library sequence (primers-barcode-test sequence)'])
    wt=author[author.subset.eq('wt scanning 50')]
    wt_groups={(str(g).casefold(),float(p)):set(values['full library sequence (primers-barcode-test sequence)'].str.upper().str[30:180]) for (g,p),values in wt.groupby(['gene name','position in 3UTR'])}
    for row in chosen.itertuples(index=False):
        a=author.iloc[int(row.source_row)]
        assert a['subset']=='mut scanning 50' and a['full library sequence (primers-barcode-test sequence)'][30:180].upper()==row.mutant_sequence
        assert row.parent_sequence in wt_groups[(str(a['gene name']).casefold(),float(a['position in 3UTR']))]
    # Astrocyte frozen table is accessed only for named sequence/offset fields.
    astro=pd.read_csv(ASTRO,usecols=['element','parent_id','gene','parent_sequence','mutant_sequence','genomic_or_utr_position'])
    astro=astro[astro.element.isin(f.loc[f.dataset.eq('astrocyte_gse330741'),'mutant_id'])]
    assert len(astro)==3984 and astro.element.is_unique
    assert astro.genomic_or_utr_position.notna().all()
    # Predeclare first/middle/last lexical genes; first/last parents per gene.
    pilot=[]
    for dataset in ('mikl_gse173098','moffatt_gse334718','astrocyte_gse330741'):
        genes=sorted({row['gene'] for row in records if row['dataset']==dataset})
        for gene in [genes[i] for i in sorted({0,(len(genes)-1)//2,len(genes)-1})]:
            eligible=sorted((r for r in records if r['dataset']==dataset and r['gene']==gene),key=lambda r:r['parent_id'])
            for i in sorted({0,len(eligible)-1}): pilot.append(eligible[i])
    pilot_ids={(r['dataset'],r['parent_id']) for r in pilot}
    candidate=f[[ (r.dataset,r.parent_id) in pilot_ids for r in f.itertuples() ]].copy()
    assert set(candidate.parent_id)=={r['parent_id'] for r in pilot}
    csvsave(OUT/'pilot_candidate_metadata.csv.gz',candidate)
    jsave(OUT/'parent_reference_candidates.json',records)
    jsave(OUT/'pilot_parent_metadata.json',pilot)
    csvsave(OUT/'parent_metadata.csv',parents)
    inputs=[INVENTORY,CORE,FASTA,NOTEBOOK,MIKL,LINEAGE,ASTRO]
    sources={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
    jsave(OUT/'metadata_receipt.json',{'status':'PASS_METADATA_ONLY','coverage':coverage,'pilot_parents':len(pilot),'pilot_interventions':len(candidate),
        'pilot_genes_by_dataset':{d:sorted({r['gene'] for r in pilot if r['dataset']==d}) for d in sorted({r['dataset'] for r in pilot})},
        'author_reference_assembly':'GRCm38.p6 from LibraryDesign code cell; header omits assembly/strand/UTR exon blocks',
        'mikl_author_parent_semantics_verified':True,'mikl_organism_metadata':sorted(chosen.organism.unique()),
        'astro_offsets_scope':'author transcript-or-UTR offset, not genomic coordinate','files':sources,
        'outcomes_read':False,'features_loaded':False,'models_fit':0,'remote_coordinate_mapping_run':False})
    print(json.dumps({'coverage':coverage,'pilot_parents':len(pilot),'pilot_interventions':len(candidate)},indent=2),flush=True)

def freeze():
    assert not (OUT/'pilot_design_manifest.json').exists() and not (OUT/'pilot_mapping_receipt.json').exists()
    metadata=json.loads((OUT/'metadata_receipt.json').read_text()); assert metadata['status']=='PASS_METADATA_ONLY'
    tests=json.loads((OUT/'synthetic_tests_receipt.json').read_text()); assert tests['status']=='PASS'
    for name,expected in tests['source_hashes'].items(): assert sha(SRC/name)==expected
    files=[p for root in (SRC,REP,OUT,ART) for p in root.rglob('*') if p.is_file()]
    files += [ROOT/name for name in metadata['files']]
    jsave(OUT/'pilot_design_manifest.json',{'status':'FROZEN_OUTCOME_BLIND_COORDINATE_PILOT','files':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files))},
        'selection':'Lexical first/middle/last genes per non-SRLE study; first/last exact parents per gene; ALL their admitted allele IDs retained',
        'assembly':'mm10/GRCm38','annotation_track':'knownGene GENCODE VM23','matching_rule':'Exact original parent in source author UTR then exact same stable transcript ID (version-stripped) and parent in reconstructed 3UTR; collapse only identical genomic base vectors; zero or multiple vectors remain unmapped/ambiguous',
        'region_cap_bases':MAX_REGION,'total_region_cap_bases':MAX_TOTAL,'response_byte_cap':MAX_RESPONSE,'interval_units':'Source gene start1/end1 inclusive to UCSC [start1-1,end1); exons and certified sites0based',
        'genome_wide_uniqueness_claimed':False,'no_alias_liftover_approximate_match_fallback':True,'conservation_scores_downloaded':False,
        'no_positive_direction_assigned':True,'root_commit_required_before_remote_mapping':True})
    print('Fixed pilot design written; root commits before remote mapping',flush=True)

def certify():
    path=OUT/'pilot_design_manifest.json'; manifest=json.loads(path.read_text())
    assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
    for name,expected in manifest['files'].items(): assert sha(ROOT/name)==expected,name
    return manifest

def download(url, stem):
    assert url.startswith(API) and not any(token in url for token in ('phyloP','phastCons','password','token'))
    path=ART/'public_metadata'/stem; receipt=path.with_name(path.name+'.receipt.json')
    if receipt.exists():
        r=json.loads(receipt.read_text()); assert r['url']==url and sha(path)==r['sha256']; return json.loads(path.read_text()) if r['http_status']==200 else None
    assert not path.exists(),'Reject unbound download cache'
    time.sleep(1.05)
    request=urllib.request.Request(url,headers={'User-Agent':'RNA-localization-academic-coordinate-feasibility/1.0'})
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            data=response.read(MAX_RESPONSE+1); status=response.status; content_type=response.headers.get('Content-Type',''); final=response.url
    except urllib.error.HTTPError as error:
        data=error.read(MAX_RESPONSE+1); status=error.code; content_type=error.headers.get('Content-Type',''); final=url
    except (urllib.error.URLError,TimeoutError) as error:
        jsave(receipt,{'url':url,'http_status':0,'failure':str(error),'accessed_utc':datetime.now(timezone.utc).isoformat(),'bytes':0,'sha256':None}); return None
    assert len(data)<=MAX_RESPONSE and final.startswith(API)
    save(path,data); jsave(receipt,{'url':url,'final_url':final,'http_status':status,'content_type':content_type,'bytes':len(data),'sha256':sha(path),
        'accessed_utc':datetime.now(timezone.utc).isoformat(),'scope':'Free official coordinate/reference metadata only; no scores, outcomes or models','terms_url':'https://genome.ucsc.edu/license/'})
    return json.loads(data) if status==200 else None

def transcript_utr(record, genomic, region_start):
    starts=[int(n) for n in record['exonStarts'].split(',') if n]; ends=[int(n) for n in record['exonEnds'].split(',') if n]
    assert len(starts)==len(ends)==record['exonCount'] and record['strand'] in ('+','-')
    assert all(a<b for a,b in zip(starts,ends)) and starts==sorted(starts)
    if record['cdsStart']==record['cdsEnd']: return None,None # no certified coding 3UTR
    positions=[]
    for a,b in zip(starts,ends):
        left,right=(max(a,record['cdsEnd']),b) if record['strand']=='+' else (a,min(b,record['cdsStart']))
        if right>left: positions.extend(range(left,right))
    if record['strand']=='-': positions=positions[::-1]
    assert all(0<=position-region_start<len(genomic) for position in positions)
    sequence=''.join(genomic[position-region_start] for position in positions)
    if record['strand']=='-': sequence=sequence.translate(str.maketrans('ACGTN','TGCAN'))
    return sequence,positions

def unique_vector(matches):
    vectors={ (r['chrom'],r['strand'],tuple(r['positions0'])) for r in matches }
    return 'reference_site_vector_unique' if len(vectors)==1 else ('ambiguous_reference_site_vectors' if vectors else 'no_exact_reference_vector')

def pilot():
    manifest=certify(); assert not (OUT/'pilot_mapping_receipt.json').exists()
    parents=json.loads((OUT/'pilot_parent_metadata.json').read_text()); results=[]; downloaded=0; regions={}
    for parent in parents:
        refs=parent['reference_candidates']; allowed={ref['transcript_id'] for ref in refs}; matches=[]; failures=[]
        keys=sorted({(ref['chromosome'],ref['gene_start1']-1,ref['gene_end1']) for ref in refs})
        for chrom,start,end in keys:
            ucsc_chrom='chrM' if chrom=='MT' else 'chr'+chrom
            if chrom not in [str(i) for i in range(1,20)]+['X','Y','MT'] or end-start>MAX_REGION:
                failures.append({'region':[chrom,start,end],'reason':'fixed_region_or_chromosome_cap'}); continue
            key=(ucsc_chrom,start,end)
            if key not in regions:
                if downloaded+end-start>MAX_TOTAL:
                    failures.append({'region':[chrom,start,end],'reason':'fixed_total_region_cap'}); continue
                tag=f'mm10_{ucsc_chrom}_{start}_{end}'
                ann=download(API+f'getData/track?genome=mm10;track=knownGene;chrom={ucsc_chrom};start={start};end={end};maxItemsOutput=10000',tag+'_knownGene.json')
                genome=download(API+f'getData/sequence?genome=mm10;chrom={ucsc_chrom};start={start};end={end}',tag+'_sequence.json')
                downloaded+=end-start; regions[key]=(ann,genome)
            ann,genome=regions[key]
            if ann is None or genome is None:
                failures.append({'region':list(key),'reason':'public_reference_request_failed'}); continue
            assert genome['genome']=='mm10' and genome['chrom']==ucsc_chrom and genome['start']==start and genome['end']==end
            genomic=genome['dna'].upper(); assert len(genomic)==end-start and re.fullmatch('[ACGTN]+',genomic)
            assert ann['genome']=='mm10' and ann['track']=='knownGene' and not ann.get('maxItemsLimit',False)
            for record in ann['knownGene']:
                if record['name'].split('.')[0] not in allowed: continue
                # Gene ranges can differ across releases. Never extend on demand.
                if record['txStart']<start or record['txEnd']>end:
                    failures.append({'transcript':record['name'],'reason':'annotation_outside_fixed_author_gene_range'}); continue
                utr,positions=transcript_utr(record,genomic,start)
                if utr is None: continue
                for offset in occurrences(utr,parent['parent_sequence']):
                    vector=positions[offset:offset+len(parent['parent_sequence'])]
                    assert len(vector)==len(parent['parent_sequence'])
                    matches.append({'transcript':record['name'],'chrom':ucsc_chrom,'strand':record['strand'],'utr_start0':offset,'positions0':vector,
                        'sequence_exact':True,'annotation_data_time':ann.get('dataTime'),'assembly':'mm10'})
        status=unique_vector(matches) if refs else parent['status']
        results.append({k:v for k,v in parent.items() if k!='reference_candidates'}|{'mapping_status':status,'matches':matches,'failures':failures})
    candidates=pd.read_csv(OUT/'pilot_candidate_metadata.csv.gz',usecols=COLS+GENES[1:],low_memory=False)
    lookup={(r['dataset'],r['parent_id']):r for r in results}; sites=[]
    for row in candidates.itertuples(index=False):
        parent=lookup[(row.dataset,row.parent_id)]; assert row.parent_sequence==parent['parent_sequence'] and len(row.parent_sequence)==len(row.mutant_sequence)
        changed=[i for i,(a,b) in enumerate(zip(row.parent_sequence,row.mutant_sequence)) if a!=b]; assert changed and len(changed)<=6
        vectors={ (m['chrom'],m['strand'],tuple(m['positions0'])) for m in parent['matches'] }
        coord=[]
        if len(vectors)==1:
            chrom,strand,vector=next(iter(vectors))
            coord=[{'insert_position0':i,'chrom':chrom,'genomic_position0':vector[i],'strand':strand,'expressed_reference':row.parent_sequence[i],
                'expressed_alternate':row.mutant_sequence[i],'genomic_reference':row.parent_sequence[i] if strand=='+' else reverse_complement(row.parent_sequence[i]),
                'genomic_alternate':row.mutant_sequence[i] if strand=='+' else reverse_complement(row.mutant_sequence[i])} for i in changed]
        sites.append({'intervention_id':row.intervention_id,'dataset':row.dataset,'gene':row.gene_transcript,'parent_id':row.parent_id,
            'mapping_status':parent['mapping_status'],'edited_site_coordinates':coord,'edit_positions0':changed})
    jsave(OUT/'pilot_parent_mappings.json',results); jsave(OUT/'pilot_edited_site_metadata.json',sites)
    certify()
    counts=dict(Counter(r['mapping_status'] for r in results))
    jsave(OUT/'pilot_mapping_receipt.json',{'status':'COMPLETED_COORDINATE_FEASIBILITY_ONLY','pilot_parents':len(results),'pilot_interventions':len(sites),
        'parent_status_counts':counts,'coordinate_unique_interventions':sum(bool(r['edited_site_coordinates']) for r in sites),'region_bases_downloaded':downloaded,
        'files':{p.relative_to(ROOT).as_posix():sha(p) for p in (OUT/'pilot_parent_mappings.json',OUT/'pilot_edited_site_metadata.json')},
        'remote_reference_receipts':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ART/'public_metadata').glob('*.receipt.json'))},
        'pilot_design_manifest_sha256':sha(OUT/'pilot_design_manifest.json'),'preservation_before_and_after':True,
        'interpretation':'Unique among admitted gene/transcript candidates on pinned mm10/reference bytes; not genome-wide uniqueness, final reporter/transcript-version certification, conservation direction or independent biology',
        'conservation_values_read':False,'outcomes_read':False,'models_fit':0})
    print(json.dumps({'parent_status_counts':counts,'parents':len(results),'unique_interventions':sum(bool(r['edited_site_coordinates']) for r in sites),'region_bases':downloaded},indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['local','freeze','pilot']);args=parser.parse_args()
    {'local':local,'freeze':freeze,'pilot':pilot}[args.mode]()
