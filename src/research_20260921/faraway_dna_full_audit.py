"""Unchanged DNA identity filters over the remaining verified public DNA reads."""
from .faraway_dna_audit import (ROOT, DATA, OUT, references, aligner, barcode_record,
                                 call_construct, sha256, write_json, write_new)
import Bio.Align._pairwisealigner as align_extension
from collections import Counter
import gzip,json
import pandas as pd


def run():
    pilot=json.loads((OUT/'faraway_dna_audit.json').read_text())
    for p,h in pilot['files'].items():
        if sha256(ROOT/p)!=h:raise ValueError('Pilot dependency changed: '+p)
    prior=pd.read_csv(OUT/'faraway_dna_pilot_calls.csv',dtype={'genotype':str,'barcode':str})
    rows=prior.to_dict('records');counts=Counter({k:v for k,v in pilot['counts'].items() if k.startswith('pilot_')})
    barcode_counts=Counter();pub=set((DATA/'faraway2025_plasmid_barcodes').read_text().splitlines())
    refs,index=references();a=aligner()
    dna=DATA/'ERR12019311.fastq.gz';all_reads=0
    with gzip.open(dna,'rt',encoding='ascii') as f:
        for n in range(1,231532):
            header=f.readline().strip();seq=f.readline().strip();f.readline();q=f.readline().strip()
            if not header.startswith('@') or len(seq)!=len(q):raise ValueError('FASTQ changed')
            all_reads+=1;b=barcode_record(seq,q)
            if b is not None:
                barcode_counts[b['barcode']]+=1
                if n>5000:
                    result,error=call_construct(b['sequence'],refs,index,a)
                    if result is None:counts[error]+=1
                    else:
                        counts['remaining_eight_segment_calls']+=1
                        rows.append({'read_number':n,'read_id':header.split()[0][1:],'barcode':b['barcode'],
                            'genotype':result['genotype'],'barcode_in_published_list':b['barcode'] in pub,
                            'reverse_complemented':b['reverse'],'barcode_min_Q':b['barcode_min_Q']})
            if n%10000==0:print(json.dumps({'DNA_reads_processed':n,'eight_segment_calls':len(rows)}),flush=True)
        if f.readline():raise ValueError('Unexpected extra DNA records')
    inventory=pd.read_csv(OUT/'faraway_dna_barcode_inventory.csv')
    if dict(barcode_counts)!=dict(zip(inventory.barcode,inventory.reads)):raise ValueError('Original barcode inventory did not reproduce')
    frame=pd.DataFrame(rows);consensus=[]
    for barcode,g in frame.groupby('barcode'):
        votes=g.genotype.value_counts();top=int(votes.iloc[0]);fraction=top/len(g)
        consensus.append({'barcode':barcode,'genotype':str(votes.index[0]),'top_genotype_reads':top,
                          'all_passing_reads':len(g),'distinct_called_genotypes':len(votes),
                          'top_fraction':fraction,'repeat_supported':top>=3 and fraction>=.9,
                          'barcode_in_published_list':barcode in pub})
    cons=pd.DataFrame(consensus)
    original=pd.read_csv(OUT/'faraway2025_partition.csv',dtype={'genotype':str})
    target=pd.read_csv(OUT/'faraway_8h_replication_predictions.csv',dtype={'genotype':str})
    supported=cons[cons.repeat_supported]
    result={'scope':'DNA-only full-file audit; unchanged pilot filters; eight-segment calls are not verified intact molecules.',
        'reads':all_reads,'all_barcode_counts_reproduced':True,'qualifying_barcode_reads':sum(barcode_counts.values()),
        'eight_segment_passing_reads':len(frame),'distinct_passing_barcodes':int(frame.barcode.nunique()),
        'distinct_passing_genotypes':int(frame.genotype.nunique()),'rejection_and_pilot_counts':dict(counts),
        'barcodes_with_conflicting_genotype_calls':int((cons.distinct_called_genotypes>1).sum()),
        'repeat_supported_barcodes':len(supported),'repeat_supported_genotypes':int(supported.genotype.nunique()),
        'target_8h_genotypes_with_any_call':len(set(frame.genotype)&set(target.genotype)),
        'target_8h_genotypes_with_repeat_supported_barcode':len(set(supported.genotype)&set(target.genotype)),
        'original_genotypes_with_any_call':len(set(frame.genotype)&set(original.genotype)),
        'numeric_assay_barcode_IDs_resolved':False,'new_RNA_outcomes_read':False,
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in [
            ROOT/'src/research_20260921/faraway_dna_full_audit.py',ROOT/'src/research_20260921/faraway_dna_audit.py',
            ROOT/'src/research_20260921/faraway_design.py',ROOT/'reports/research_20260921/faraway_dna_full_audit_spec.md',
            OUT/'faraway_dna_audit.json',OUT/'faraway_dna_pilot_calls.csv',OUT/'faraway_dna_barcode_inventory.csv',
            dna,ROOT/align_extension.__file__]}}
    write_new(OUT/'faraway_dna_full_calls.csv',frame.to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/'faraway_dna_full_barcode_associations.csv',cons.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/'faraway_dna_full_audit.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':run()
