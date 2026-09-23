"""Post-hoc Total1 reconciliation; only previously opened target identifiers."""
from .common import ROOT,sha256,write_json,write_new
from .shukla_sequence_recovery import DATA,OUT,rc,HEADER
import csv,gzip,hashlib,json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def run():
    raw=DATA/'SRR5528987.fastq.gz'
    receipt=json.loads((DATA/'SRR5528987.fastq.gz.receipt.json').read_text())
    if not receipt['full_archive_MD5_verified'] or sha256(raw)!=receipt['sha256']:
        raise ValueError('Unverified raw file')
    f=pd.read_csv(OUT/'shukla_transfer_predictions.csv')
    f=f.groupby('accession',group_keys=False).filter(lambda g:len(g)>=10).copy().reset_index(drop=True)
    if len(f)!=277:raise ValueError('Previously opened set changed')
    by_id={r.id:i for i,r in enumerate(f.itertuples())}
    by_barcode={rc(r.barcode):(i,r.sequence[20:]) for i,r in enumerate(f.itertuples())}
    if len(by_barcode)!=len(f):raise ValueError('Ambiguous admitted barcode')
    geo={}
    with gzip.open(DATA/'shukla2018_counts.tsv.gz','rt') as stream:
        if stream.readline().strip().split('\t')!=HEADER:raise ValueError('Unexpected GEO schema')
        for line in stream:
            cells=line.rstrip('\n').split('\t')
            if cells[0] in by_id:geo[cells[0]]=float(cells[7]) # Total1 only.
    author={}
    with (DATA/'shukla2018_author_raw_counts.tsv').open() as stream:
        header=stream.readline().strip().split('\t');column=header.index('Total_BioRep1')
        for line in stream:
            cells=line.rstrip('\n').split('\t')
            if cells[0] in by_id:author[cells[0]]=float(cells[column])
    if set(geo)!=set(by_id) or set(author)!=set(by_id):raise ValueError('Missing audit IDs')
    counts=np.zeros((len(f),3),dtype=np.int64);records=0;examples={}
    with gzip.open(raw,'rt',encoding='ascii',newline='') as stream:
        while True:
            header=stream.readline()
            if not header:break
            s=stream.readline().rstrip('\r\n');plus=stream.readline();q=stream.readline().rstrip('\r\n')
            if not header.startswith('@') or not plus.startswith('+') or len(s)!=len(q):raise ValueError('Malformed full FASTQ')
            records+=1
            match=by_barcode.get(s[:10])
            if match is not None:
                i,expected=match;counts[i,0]+=1
                if len(s)==100 and min(map(ord,q[:10]))>=63 and min(map(ord,q[10:]))>=53:
                    counts[i,1]+=1
                    if rc(s[10:])==expected:
                        counts[i,2]+=1
                        identifier=f.id.iloc[i]
                        if geo[identifier]==0 and identifier not in examples:
                            examples[identifier]={'read_id_sha256':hashlib.sha256(header.strip().encode()).hexdigest(),
                                'read_sequence':s,'read_quality':q,'reference_suffix90':expected}
            if records%2000000==0:print('Validated FASTQ records',records,flush=True)
    f['geo_Total1']=[geo[i] for i in f.id]
    f['author_Total_BioRep1']=[author[i] for i in f.id]
    for i,name in enumerate(['full_raw_barcode_reads','full_raw_Q30barcode_Q20insert_reads','full_raw_exact_suffix90_reads']):f[name]=counts[:,i]
    zeros=f.geo_Total1.eq(0)
    result={'scope':'Post-hoc reconciliation after the external pilot failed; not an independent outcome test.',
        'run':'SRR5528987','geo_sample':'GSM2615964','experiment':'SRX2798197','sample_description':'Total1',
        'full_raw_md5':receipt['archive_md5'],'full_raw_sha256':receipt['sha256'],
        'full_raw_records':records,'previously_open_identifiers':len(f),
        'geo_Total1_zero_rows':int(zeros.sum()),
        'geo_zero_rows_with_5_or_more_exact_raw_reads':int((zeros&(f.full_raw_exact_suffix90_reads>=5)).sum()),
        'minimum_exact_raw_reads_among_geo_zero_rows':int(f.loc[zeros,'full_raw_exact_suffix90_reads'].min()),
        'maximum_exact_raw_reads_among_geo_zero_rows':int(f.loc[zeros,'full_raw_exact_suffix90_reads'].max()),
        'spearman_full_barcode_vs_geo_Total1':float(spearmanr(f.full_raw_barcode_reads,f.geo_Total1).statistic),
        'spearman_exact_suffix90_vs_geo_Total1':float(spearmanr(f.full_raw_exact_suffix90_reads,f.geo_Total1).statistic),
        'spearman_author_vs_geo_Total1':float(spearmanr(f.author_Total_BioRep1,f.geo_Total1).statistic),
        'author_table_scope':'Repository table has four biological-replicate columns per fraction, unlike six in GEO. Its exact relationship to final study samples is unresolved. Only Total_BioRep1 examined.',
        'examples_geo_zero_but_raw_exact_match':examples,
        'conclusion':'Raw/processed Total1 correspondence is not reconciled. Do not interpret the frozen pilot as a clean biological transfer test. This does not establish the cause or an error in the original paper.',
        'closed_replicates_read':False,
        'source_files':{p.relative_to(ROOT).as_posix():sha256(p) for p in [DATA/'shukla2018_counts.tsv.gz',
            DATA/'shukla2018_total1_sample',DATA/'shukla2018_author_raw_counts.tsv',DATA/'shukla2018_normalize.R']},
        'code_sha256':sha256(__file__)}
    columns=['id','accession','qc_quality_reads','qc_exact_suffix90','geo_Total1','author_Total_BioRep1',
             'full_raw_barcode_reads','full_raw_Q30barcode_Q20insert_reads','full_raw_exact_suffix90_reads']
    write_new(OUT/'shukla2018_total1_count_audit.csv',f[columns].to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/'shukla2018_total1_count_audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['examples_geo_zero_but_raw_exact_match','source_files']},indent=2),flush=True)


if __name__=='__main__':run()
