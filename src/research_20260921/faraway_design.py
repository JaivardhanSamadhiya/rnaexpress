"""Outcome-free synonymous/intron design checks and fixed GA-pattern partition."""
from .common import ROOT,sha256,write_json,write_new
import hashlib,itertools,json
import numpy as np
import pandas as pd
import openpyxl

OUT=ROOT/'results/research_20260921';DATA=ROOT/'data/external/research_20260921'
STARTS=[0,296,458,689,887,1037,1206,1457,1703]


def panel(g):
    # DeO fragments 1 and 7 contain a linked exonic substitution when intron-bearing.
    # Keep these statuses fixed, so candidate placement choices preserve mature RNA.
    return g[:8]+'_'+(g[8] if g[0]=='0' else '*')+'_'+(g[14] if g[6]=='0' else '*')


def excise(noin,with_intron):
    delta=len(with_intron)-len(noin)
    if delta<=0:raise ValueError('Nonpositive intron length')
    options=[]
    for j in range(len(noin)+1):
        s=with_intron[:j]+with_intron[j+delta:]
        options.append((sum(a!=b for a,b in zip(s,noin)),j,s))
    best=min(x[0] for x in options);seqs={x[2] for x in options if x[0]==best}
    if len(seqs)!=1:raise ValueError('Ambiguous exon sequence after minimum-edit excision')
    return next(iter(seqs)),best,delta


def run():
    w=openpyxl.load_workbook(DATA/'faraway2025_supptable_2.xlsx',read_only=True,data_only=True)
    fragments={n:s.upper() for n,s in list(w['Ordered_fragments'].values)[1:] if isinstance(s,str)}
    examples={n:s.upper() for n,d,s in list(w['Example_reporter_plasmids'].values)[1:] if isinstance(s,str)};w.close()
    pieces={};audit=[]
    for tag in ['Opt','DeO']:
        for i in range(1,9):
            no=fragments[f'PPIG_{tag}_NoIn_{i}'];yes=fragments[f'PPIG_{tag}_In_{i}']
            mature,mismatches,length=excise(no,yes)
            off=49 if i==1 else 0;size=STARTS[i]-STARTS[i-1]
            pieces[(tag,i,0)]=no[off:off+size];pieces[(tag,i,1)]=mature[off:off+size]
            audit.append({'tag':tag,'position':i,'linked_exonic_substitutions':mismatches,'intron_length':length})
    if ''.join(pieces[('Opt',i,0)] for i in range(1,9))!=examples['PPIG: GA-rich without introns']:
        raise ValueError('Ordered fragment assembly differs from GA-rich reference')
    bases='TCAG';code='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
    table={a+b+c:code[i*16+j*4+k] for i,a in enumerate(bases) for j,b in enumerate(bases) for k,c in enumerate(bases)}
    def assemble(g):return ''.join(pieces[('Opt' if g[i-1]=='1' else 'DeO',i,int(g[8+i-1]))] for i in range(1,9))
    f=pd.read_csv(OUT/'faraway2025_construct_metadata.csv',dtype={'genotype':str,'bc_number':str})
    f=f[f.sheet=='transfection_1'].copy();f['ga']=f.genotype.str[:8];f['panel']=f.genotype.map(panel)
    genotypes=f.drop_duplicates('genotype');seqs={g:assemble(g) for g in genotypes.genotype}
    proteins=set()
    for s in seqs.values():
        if len(s)!=1703 or s[20:23]!='ATG':raise ValueError('Unexpected assembled reporter')
        proteins.add(''.join(table[s[i:i+3]] for i in range(20,1658,3)))
    if len(proteins)!=1 or not next(iter(proteins)).endswith('*'):raise ValueError('Reporter protein identity not preserved')
    eligible=genotypes[genotypes.n_introns==4].groupby('panel').filter(lambda g:len(g)>=5)
    for _,g in eligible.groupby('panel'):
        if len({seqs[x] for x in g.genotype})!=1:raise ValueError('Candidate panel changes mature RNA')
    parents=sorted(eligible.ga.unique(),key=lambda x:hashlib.sha256(('faraway-placement-20260923|'+x).encode()).hexdigest())
    if len(parents)!=125:raise ValueError('Metadata eligibility changed')
    reserved={g:('confirmation' if j<25 else 'development' if j<50 else 'train') for j,g in enumerate(parents)}
    f['partition']=[reserved.get(g,'train') for g in f.ga]
    valid_panels=set(eligible.panel);f['decision_candidate']=f.panel.isin(valid_panels)&f.n_introns.eq(4)
    write_new(OUT/'faraway2025_partition.csv',f.to_csv(index=False,lineterminator='\n').encode())
    sframe=genotypes[['genotype','ga','panel','n_introns']].copy();sframe['mature_sequence']=[seqs[x] for x in sframe.genotype]
    write_new(OUT/'faraway2025_design_sequences.csv',sframe.to_csv(index=False,lineterminator='\n').encode())
    result={'scope':'Outcome-free construction and partition audit; predicted exon removal is design-based, not raw-read confirmation.',
        'unique_genotypes':len(genotypes),'protein_identity_count':len(proteins),'protein_amino_acids_excluding_stop':len(next(iter(proteins)))-1,
        'eligible_panels':len(valid_panels),'eligible_GA_patterns':len(parents),'candidate_genotypes':len(eligible),
        'exon_removal_audit':audit,'example_GA_poor_mismatches':sum(a!=b for a,b in zip(assemble('0'*16),examples['PPIG: GA-poor without introns'])),
        'partition_GA_patterns':f.groupby('partition').ga.nunique().to_dict(),
        'decision_panels_by_partition':f[f.decision_candidate].groupby('partition').panel.nunique().to_dict(),
        'restrictions':['Only transfection_1 admitted for prospective numeric-access protocol.','Other assay outcomes and halflife sheet remain unopened.','Example GA-poor sequence does not match ordered-fragment assembly; use ordered-fragment design and declare reconstruction limit.'],
        'files':{str(p.relative_to(ROOT)):sha256(p) for p in [DATA/'faraway2025_supptable_2.xlsx',DATA/'faraway2025_supptable_3.xlsx',ROOT/'src/research_20260921/faraway_design.py']}}
    write_json(OUT/'faraway2025_design_audit.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':run()
