"""Separate reconstruction from preserved public-reference bodies; metadata only."""
from .acquire import ROOT,OUT,RAW,fresh,sha,save
import json,subprocess
def run():
 fresh();path=OUT/'reference_replay_manifest.json';m=json.loads(path.read_text())
 assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h,rel
 request=json.loads((OUT/'request_manifest.json').read_text());receipt=json.loads((OUT/'reference_receipt.json').read_text())
 assert receipt['status']=='COMPLETE_FIXED_REFERENCE_QUERIES_REVIEW_MATCHES' and not receipt['failures']
 byurl={x['URL']:x for x in receipt['http_records']};bodies={}
 for item in request['requests']:
  raw=RAW/(item['name']+item['suffix']);record=byurl[item['URL']];assert sha(raw)==record['SHA256']
  body=raw.read_bytes()
  if item['kind']=='RefSeq':
   lines=body.decode('ascii').splitlines();version=[x.split()[1] for x in lines if x.startswith('VERSION')]
   assert version==[item['accession']]
   begin=next(i for i,line in enumerate(lines) if line.startswith('ORIGIN'))
   end=next(i for i in range(begin+1,len(lines)) if lines[i].startswith('//'))
   sequence=''.join(letter.upper() for line in lines[begin+1:end] for letter in line if letter.isalpha())
   assert set(sequence)<=set('ACGT')
   declared=int(next(line.split()[2] for line in lines if line.startswith('LOCUS')));assert len(sequence)==declared
   bodies[item['name']]=sequence
  else:bodies[item['name']]=json.loads(body)
 source=json.loads((ROOT/request['design']).read_text());rows={x['source_excel_row']:x for x in source['rows']}
 matches=json.loads((OUT/'literal_native_reference_matches.json').read_text());comparisons=0;native=set();versions={}
 for item in matches['matches']:
  dna=rows[item['source_excel_row']]['Sequence'];assert len(dna)==140;native.add(item['source_excel_row'])
  if item['lineage']=='NORAD':
   reference=bodies[item['reference_accession']];versions[item['reference_accession']]=len(reference)
   allhits=[[i,i+140] for i in range(len(reference)-139) if reference[i:i+140]==dna]
   assert allhits==item['exact_forward140nt_intervals0based'] and len(allhits)==item['matches']==1
   comparisons+=140
  else:
   definition=next(x for x in request['requests'] if x['name']==item['lineage']+'_sequence')
   reference=bodies[definition['name']];a,b=item['exact140nt_interval0based'];segment=reference['dna'][a-definition['start']:b-definition['start']].upper()
   if item['strand']=='-':
    complement={'A':'T','C':'G','G':'C','T':'A'}
    segment=''.join(complement[letter] for letter in reversed(segment))
   assert segment==dna and b-a==140;comparisons+=140
   annotations=bodies[item['lineage']+'_refGene']['refGene'];recorded=item['covering_refGene_exon_annotations']
   expected=[]
   for gene in annotations:
    if gene['strand']!=item['strand']:continue
    starts=gene['exonStarts'].rstrip(',').split(',');ends=gene['exonEnds'].rstrip(',').split(',')
    assert len(starts)==len(ends)
    if any(int(u)<=a and b<=int(v) for u,v in zip(starts,ends)):expected.append({k:gene[k] for k in ('name','name2','chrom','strand','txStart','txEnd')})
   assert expected==recorded and recorded
 for record in matches['SMARCA2_hg38_fixed_comparison']:
  ref=bodies['SMARCA2_hg38_sequence'];dna=next(rows[x['source_excel_row']]['Sequence'] for x in matches['matches'] if x['lineage']=='SMARCA2')
  expected=[[ref['start']+i,ref['start']+i+140] for i in range(len(ref['dna'])-139) if ref['dna'][i:i+140].upper()==dna]
  assert expected==record['whole140nt_hits0based'];comparisons+=140
 assert len(native)==7 and not matches['genomic_no_exact_match_or_unavailable']
 save(OUT/'independent_reference_replay_receipt.json',{'status':'PASS_ALL_FIXED_BODY_HASHES_WHOLE_NATIVE_STRINGS_AND_EXON_COVERAGE_REPLAY',
  'manifest_sha256':sha(path),'source_receipt_sha256':sha(OUT/'reference_receipt.json'),'public_response_bodies':13,'new_native_WT_fragments':7,
  'DNA_base_comparisons':comparisons,'NORAD_versioned_lengths':versions,'SMARCA2_hg19_hg38_both_match':True,
  'native_source_gene_context_full_reporter_RNA_not_certified':True,'producer_GenBank_parser_match_finder_and_RC_helper_not_used':True,
  'same_root_runtime_not_independent_agent_execution':True,'models_fit':0,'assay_outcomes_read':False})
 print('WHOLE_NATIVE_REFERENCE_REPLAY_PASS',comparisons,flush=True)
if __name__=='__main__':run()
