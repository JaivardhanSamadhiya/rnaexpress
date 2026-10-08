"""Fixed public-reference sequence pilot; exact native-locus match only."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,urllib.request,urllib.parse
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_irf_locus_metadata_20261008';OUT=ROOT/'results'/NS;RAW=ROOT/'data/raw'/NS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2)+'\n').encode())
def reverse_complement(seq):return seq.translate(str.maketrans('ACGT','TGCA'))[::-1]
def exact_hits(reference,query):return [i for i in range(len(reference)-len(query)+1) if reference[i:i+len(query)]==query]
def run():
 mpath=OUT/'request_manifest.json';m=read(mpath)
 assert subprocess.check_output(['git','show','HEAD:'+mpath.relative_to(ROOT).as_posix()],cwd=ROOT)==mpath.read_bytes()
 for rel,digest in m['files'].items():assert sha(ROOT/rel)==digest,rel
 design=read(ROOT/m['source_design'])['rows'];parent=next(row for row in design if row['source_excel_row']==1777)
 assert parent['ID']==m['source_parent_ID'] and hashlib.sha256(parent['Sequence'].encode()).hexdigest()==m['source_sequence_sha256']
 requests=m['requests'];records=[];matches=[]
 for item in requests:
  request=urllib.request.Request(item['url'],headers={'User-Agent':'rnaexpress-public-reference-metadata/1.0','Accept':'application/json,text/plain'})
  try:
   with urllib.request.urlopen(request,timeout=45) as response:
    final=response.geturl();assert urllib.parse.urlparse(final).scheme=='https' and urllib.parse.urlparse(final).hostname in ('api.genome.ucsc.edu','eutils.ncbi.nlm.nih.gov')
    assert response.status==200;body=response.read(item['response_cap_bytes']+1);assert len(body)<=item['response_cap_bytes']
    receipt={'URL':item['url'],'response_URL':final,'HTTP_status':response.status,'headers':dict(response.headers),'bytes':len(body),'SHA256':hashlib.sha256(body).hexdigest(),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
   path=RAW/item['name']
   with path.open('xb') as f:f.write(body)
   save(RAW/(item['name']+'.http.json'),receipt);records.append({'name':item['name'],'receipt':receipt})
   if item['kind']=='genomic_JSON':
    data=json.loads(body);assert data['genome']==item['genome'] and data['chrom']=='chr19' and data['start']==46386925 and data['end']==46387389
    reference=data['dna'].upper();assert len(reference)==464 and set(reference)<=set('ACGT')
    positions=exact_hits(reference,parent['Sequence']);minus_positions=exact_hits(reverse_complement(reference),parent['Sequence'])
    matches.append({'kind':item['kind'],'reference':item['genome'],'query_start_0based':data['start'],'query_end_exclusive':data['end'],
     'forward_exact_hits_0based':positions,'minus_oriented_reference_exact_hits_0based':minus_positions,
     'minus_genomic_intervals_0based_halfopen':[[data['end']-i-140,data['end']-i] for i in minus_positions],
     'native_fragment_only_not_reporter_mature_context':True})
   else:
    text=body.decode('ascii');assert re.search(r'^VERSION\s+NM_015649\.3',text,re.M)
    assert '/gene="IRF2BP1"' in text and 'ORIGIN' in text and text.rstrip().endswith('//')
    sequence=re.sub(r'[^acgtACGT]','',text.split('ORIGIN',1)[1].split('//',1)[0]).upper()
    assert 140<=len(sequence)<=50000 and set(sequence)<=set('ACGT')
    matches.append({'kind':item['kind'],'reference':'NM_015649.3','reference_gene_literal':'IRF2BP1','mRNA_length':len(sequence),
      'forward_exact_hits_0based':exact_hits(sequence,parent['Sequence']),'reverse_complement_exact_hits_0based':exact_hits(reverse_complement(sequence),parent['Sequence']),
      'native_reference_transcript_match_not_reporter_junction_or_full_mature_RNA':True})
  except Exception as error:
   save(OUT/(item['name']+'.failure.json'),{'status':'SOURCE_METADATA_REQUEST_OR_PARSE_FAILURE','request':item,'exception_type':type(error).__name__,'error':str(error),'no_retry_or_substitution':True})
   raise
 save(OUT/'exact_reference_sequence_matches.json',matches)
 hg19=next(x for x in matches if x['reference']=='hg19');rna=next(x for x in matches if x['reference']=='NM_015649.3')
 certified=len(hg19['minus_genomic_intervals_0based_halfopen'])==1 and len(rna['forward_exact_hits_0based'])==1
 save(OUT/'reference_pilot_receipt.json',{'status':'PASS_EXACT_IRF2BP1_NATIVE_FRAGMENT_REFERENCE_MATCH' if certified else 'COMPLETE_REFERENCE_PILOT_NO_UNIQUE_NATIVE_CERTIFICATE',
   'manifest_sha256':sha(mpath),'source_parent_ID':parent['ID'],'source_sequence_sha256':m['source_sequence_sha256'],
   'records':records,'matches_sha256':sha(OUT/'exact_reference_sequence_matches.json'),'gene_identity_certificate_applies_only_to_one_native_fragment':certified,
   'other_six_lineages_not_certified':True,'engineered_mPRE_genomic_identity_not_assumed':True,'source_gene_conflict_preserved_not_silently_aliased':True,
   'binding_count_assignment_or_replicate_pairing_not_certified':True,'reporter_mature_boundaries_uncertified':True,'numerical_binding_or_localization_endpoints_opened':False,
   'models_fit':0,'training_pairs_admitted':0,'cost':0,'public_unauthenticated_primary_reference_sources':True})
 print('REFERENCE_METADATA',certified,json.dumps(matches,sort_keys=True),flush=True)
if __name__=='__main__':run()
