"""Outcome-blind sequence and parent admission for NucLibC only."""
from .common import ROOT, sha256, write_json, write_new, load_certified
from collections import Counter
import json
import openpyxl
import pandas as pd

DATA = ROOT/'data/external/research_20260921'
OUT = ROOT/'results/research_20260921'


def metadata():
    p = DATA/'sirloin_dataset_ev1.xlsx'
    if sha256(p) != 'ad478cbaff86d527fb74de61235f1225fed67a1598522c1b8cb5f002cff2ccd2':
        raise ValueError('Source changed')
    w = openpyxl.load_workbook(p,read_only=True,data_only=True)
    rows = list(w['NucLibC'].iter_rows(min_row=3,max_col=6,values_only=True))
    w.close()
    frame = pd.DataFrame(rows,columns=['id','gene','tile','wt','sequence','mismatches'])
    if frame.id.duplicated().any():
        raise ValueError('Duplicate source ID')
    return frame


def inventory():
    frame = metadata()
    lines = (DATA/'nuclibc_fasta').read_text().splitlines()
    records = {lines[i][1:]:lines[i+1].upper() for i in range(0,len(lines),2)}
    old = load_certified()
    old_sequences = set(old.parent_sequence.dropna()) | set(old.mutant_sequence.dropna())
    parents = {}
    single_records = []
    for parent,prefix in (('Jpx_9','Jpx_9'),('NICN1_53','NICN_53')):
        wt = frame[frame.id == parent]
        if len(wt) != 1:
            raise ValueError('Expected one WT record: '+parent)
        reference = wt.sequence.iloc[0].upper()
        family = frame[frame.id.str.startswith(prefix+':Mut:')]
        categories = Counter()
        invalid = []
        for row in family.itertuples():
            seq = row.sequence.upper()
            changes = [(i,a,b) for i,(a,b) in enumerate(zip(reference,seq)) if a != b]
            if len(seq) != len(reference) or len(changes) != 1 or set(seq)-set('ACGT'):
                invalid.append(row.id)
                continue
            pos,a,b = changes[0]
            categories[a+'>'+b] += 1
            single_records.append(dict(id=row.id,parent=parent,sequence=seq,reference=reference,
                                       position=pos,mutation=a+'>'+b))
        parents[parent] = {'reference_length':len(reference),'single_substitutions':sum(categories.values()),
                           'mutation_class_sizes':dict(categories),'invalid_ids':invalid}
    result = {'sheet':'NucLibC','rows':len(frame),'sequence_lengths':dict(Counter(len(s) for s in frame.sequence)),
        'fasta_id_matches':sum(i in records for i in frame.id),
        'fasta_sequence_mismatches':[row.id for row in frame.itertuples() if row.id in records and records[row.id] != row.sequence.upper()],
        'exact_sequence_overlap_certified_old':sum(s in old_sequences for s in frame.sequence),
        'parents':parents,'outcome_cells_read':False,'NucLibB_opened':False,
        'note':'GitHub FASTA contains additional library members; published workbook is authoritative for this analysis.'}
    write_new(OUT/'sirloin_single_mutation_sequences.csv',pd.DataFrame(single_records).to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/'sirloin_sequence_inventory.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__':
    inventory()
