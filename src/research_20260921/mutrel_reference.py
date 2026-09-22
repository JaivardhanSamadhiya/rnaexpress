"""Reconstruct the documented 162-nt WT from mutation metadata and PCR primers."""
from .common import ROOT,sha256,write_json,write_new
import json,openpyxl

def run():
    out=ROOT/'results/research_20260921'
    p=ROOT/'data/external/research_20260921/mutrel_primers.xlsx'
    if sha256(p)!='ecffa140e24402ea37ad7f2e4a6df3d3fbce850176de13bbdfbcf45620331a18':
        raise ValueError('Primer workbook changed')
    w=openpyxl.load_workbook(p,read_only=True,data_only=True)
    primers={row[1]:row[2] for row in w.active.iter_rows(values_only=True) if isinstance(row[1],str) and isinstance(row[2],str)}
    w.close()
    forward=primers['Nxf1-enChr-1F']; reverse=primers['Nxf1-enChr-1R']
    if not forward.startswith('ATCCGGCGCGCC') or not reverse.startswith('ATCCGCGGCCGC'):
        raise ValueError('Unexpected restriction-site overhangs')
    forward=forward[12:]
    reverse=reverse[12:].translate(str.maketrans('ACGT','TGCA'))[::-1]
    support=[set() for _ in range(162)];evidence=[[] for _ in range(162)]
    rows=(out/'mutrel_sequence_metadata.tsv').read_text().splitlines()[1:]
    for row in rows:
        name,site,mutation=row.split('\t')
        if mutation:
            support[int(site)-1].add(mutation[0]);evidence[int(site)-1].append('mutation_metadata')
    for start,sequence,label in [(0,forward,'forward_PCR_primer'),(162-len(reverse),reverse,'reverse_PCR_primer_RC')]:
        for i,base in enumerate(sequence):
            support[start+i].add(base);evidence[start+i].append(label)
    missing=[i+1 for i,s in enumerate(support) if len(s)==0]
    conflicting=[i+1 for i,s in enumerate(support) if len(s)>1]
    report={'length_assumption':162,'length_source':'Yin et al. Nature 2020 describes a 162-nucleotide NXF1-enChr fragment.',
            'missing_positions':missing,'conflicting_positions':conflicting,
            'primer_supported_positions':sum(any('primer' in e for e in es) for es in evidence),
            'outcomes_read':False,'isolated_mutant_semantics_established':False}
    if not missing and not conflicting:
        sequence=''.join(next(iter(s)) for s in support)
        report['sequence']=sequence
        report['known_U1_motif_start_1based']=sequence.find('CAGGTGAGT')+1
        if primers['Nxf1-mutU1-2F'] not in sequence:
            raise ValueError('Independent internal primer fails WT cross-check')
        report['independent_internal_primer_match']=True
        write_new(out/'mutrel_reconstructed_WT.fasta',('>NXF1_enChr_metadata_and_PCR_reconstruction\n'+sequence+'\n').encode())
    write_json(out/'mutrel_reference_inventory.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':run()
