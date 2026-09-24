"""Compare two official formats only at previously opened outcome keys."""
from .common import ROOT, sha256, write_new, write_json
from .faraway_configuration import load_frame, read_values, verify
from .faraway_8h_replication import target_metadata, read_target
from .faraway_metadata import decode_genotype
from datetime import datetime,timezone
from urllib.request import Request,urlopen
import csv,json,math
import numpy as np
import pandas as pd

DATA=ROOT/'data/external/research_20260921';OUT=ROOT/'results/research_20260921'
FILES={'development':('transfection_firstexperiment_ratios.tsv',5967368),
       '8h':('transfection_timepoints_ratios.tsv',3048954)}


def fetch(filename,size):
    if (filename,size) not in FILES.values():raise PermissionError('Not an admitted official processed file')
    p=DATA/('faraway2025_'+filename);rp=p.with_name(p.name+'.receipt.json')
    if rp.exists():
        if sha256(p)!=json.loads(rp.read_text())['sha256']:raise ValueError('Saved asset changed')
        return p
    url='https://www.ebi.ac.uk/biostudies/files/E-MTAB-13329/'+filename
    with urlopen(Request(url,headers={'User-Agent':'RNAddress-provenance/1.0'}),timeout=45) as r:
        body=r.read(size+1);resolved=r.geturl()
    if len(body)!=size:raise ValueError('Official file size differs')
    write_new(p,body);write_json(rp,{'url':url,'resolved_url':resolved,'bytes':len(body),'sha256':sha256(p),
        'retrieved_utc':datetime.now(timezone.utc).isoformat(),'scope':'Official processed file; numeric parsing restricted separately to previously opened keys.'})
    return p


def read_scoped_tsv(path, allowed, timed):
    """Return only whitelisted outcomes; all other values remain unconverted."""
    result={};metadata=[]
    with path.open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream,delimiter='\t'):
            condition=row.get('time','16 hr')
            key=(str(row['bc_number']),int(row['replicate']),condition)
            genotype=decode_genotype(row['structure'],row['int_pattern'])
            if genotype[:8].count('1')!=int(row['n_opt']) or genotype[8:].count('1')!=int(row['n_introns']):
                raise ValueError('Metadata genotype/count mismatch')
            metadata.append((key,genotype))
            if key not in allowed:continue
            if timed and condition!='8 hr':raise PermissionError('Later condition not admitted')
            if genotype!=allowed[key]:raise ValueError('Allowed key has changed genotype')
            if key in result:raise ValueError('Duplicate admitted key')
            cyto,nucleus,ratio=[float(row[c]) for c in ['cytoplasm','nucleus','nc_ratio']]
            if not all(math.isfinite(v) and v>0 for v in [cyto,nucleus,ratio]):raise ValueError('Invalid admitted values')
            if not np.isclose(ratio,nucleus/cyto,rtol=1e-8,atol=1e-10):raise ValueError('Ratio inconsistency')
            result[key]=float(np.log2(nucleus/cyto))
    if set(result)!=set(allowed):raise ValueError('Missing previously opened keys')
    return result,metadata


def run():
    verify()
    original=load_frame();dev=original[(original.partition=='development')&original.decision_candidate]
    target=target_metadata()
    all_metadata=pd.read_csv(OUT/'faraway2025_construct_metadata.csv',dtype={'genotype':str,'bc_number':str})
    reports={}
    for stage,f in [('development',dev),('8h',target)]:
        filename,size=FILES[stage];path=fetch(filename,size)
        allowed={(str(r.bc_number),int(r.replicate),'8 hr' if stage=='8h' else '16 hr'):r.genotype for r in f.itertuples()}
        if len(allowed)!=len(f):raise ValueError('Workbook admitted-key duplicates')
        vals,metadata=read_scoped_tsv(path,allowed,stage=='8h')
        book,_=read_values(DATA/'faraway2025_supptable_3.xlsx',f.excel_row) if stage=='development' else (read_target(DATA/'faraway2025_supptable_3.xlsx',f.excel_row),None)
        differences=[]
        for r in f.itertuples():
            key=(str(r.bc_number),int(r.replicate),'8 hr' if stage=='8h' else '16 hr')
            differences.append(abs(vals[key]-book[r.excel_row]))
        whole=all_metadata[all_metadata.sheet.eq('transfection_1' if stage=='development' else 'transfection_2')]
        workbook_keys={(str(r.bc_number),int(r.replicate),'16 hr' if stage=='development' else r.time):r.genotype for r in whole.itertuples()}
        native_keys=dict(metadata)
        if len(native_keys)!=len(metadata):raise ValueError('Native metadata has duplicate keys')
        shared=set(native_keys)&set(workbook_keys)
        reports[stage]={'numeric_rows_compared':len(vals),'numeric_cells_parsed_from_native':3*len(vals),
            'max_abs_log2_ratio_difference':float(max(differences)),'rows_equal_within_1e_10':int(sum(d<=1e-10 for d in differences)),
            'native_metadata_rows':len(metadata),'workbook_metadata_rows':len(whole),
            'native_time_labels':sorted({k[2] for k in native_keys}),
            'metadata_keys_only_native':len(set(native_keys)-set(workbook_keys)),
            'metadata_keys_only_workbook':len(set(workbook_keys)-set(native_keys)),
            'shared_keys_with_different_genotype':sum(native_keys[k]!=workbook_keys[k] for k in shared)}
    write_json(OUT/'faraway_processed_correspondence.json',{'scope':'Already-open development and 8-hour outcome rows only; remaining file inspection metadata-only.',
        'results':reports,'new_outcome_rows_opened':False,'DNA_barcode_to_numeric_ID_mapping_resolved':False,
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in [ROOT/'src/research_20260921/faraway_processed_correspondence.py',
              ROOT/'reports/research_20260921/faraway_processed_correspondence_spec.md',*[DATA/('faraway2025_'+name) for name,_ in FILES.values()]]}})
    print(json.dumps(reports,indent=2),flush=True)


if __name__=='__main__':run()
