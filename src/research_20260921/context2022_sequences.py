"""Outcome-blind context-study inventory, restricted to six metadata columns."""
from .common import ROOT,sha256,write_json,write_new,load_certified
from .sirloin_sequences import metadata as sirloin_metadata
from collections import Counter
import json,openpyxl,pandas as pd


def run():
    path=ROOT/'data/external/research_20260921/context2022_data3.xlsx'
    if sha256(path)!='c440eb07ed641cc172e23d9051b2ecf659e320b2de3caed9978a073f8c30aafd':
        raise ValueError('Context source changed')
    w=openpyxl.load_workbook(path,read_only=True,data_only=True)
    rows=list(w['finalTab_230221'].iter_rows(min_row=2,max_col=6,values_only=True));w.close()
    f=pd.DataFrame(rows,columns=['id','library','index','segment','gene','sequence'])
    valid=f.sequence.map(lambda s:isinstance(s,str) and len(s)>=6 and not set(s.upper())-set('ACGT'))
    old=load_certified(); oldseq=set(old.parent_sequence)|set(old.mutant_sequence)
    sirloin=sirloin_metadata(); sirseq=set(sirloin.sequence)
    f=f.assign(valid_sequence=valid,overlap_old=f.sequence.isin(oldseq),overlap_sirloin=f.sequence.isin(sirseq))
    summary={'metadata_rows':len(f),'valid_sequence_rows':int(valid.sum()),
             'unique_sequences':int(f.loc[valid,'sequence'].nunique()),
             'duplicate_ids':int(f.id.duplicated().sum()),'libraries':f.library.value_counts().to_dict(),
             'valid_sequence_lengths':dict(Counter(len(s) for s in f.loc[valid,'sequence'])),
             'gene_labels':int(f.gene.nunique()),'exact_overlap_old':int(f.overlap_old.sum()),
             'exact_overlap_sirloin':int(f.overlap_sirloin.sum()),
             'genes_with_at_least_20_valid_rows':int((f[valid].groupby('gene').size()>=20).sum()),
             'outcome_columns_read':False,
             'caution':'Gene labels still require biological grouping validation; these are tiled fragments, not minimal edits.'}
    out=ROOT/'results/research_20260921'
    write_new(out/'context2022_sequence_metadata.csv',f.to_csv(index=False,lineterminator='\n').encode())
    write_json(out/'context2022_sequence_inventory.json',summary)
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':run()
