"""Fixed public metadata XML requests. Never follow related-resource links."""
from pathlib import Path
import ctypes,datetime,hashlib,json,subprocess,time,urllib.request,urllib.parse,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_qualitative_xml_20261009';OUT=ROOT/'results'/NS;RAW=ROOT/'data/raw'/NS
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def fresh():
 class M(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 m=M();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
 assert m.available>=1.3*2**30,'Bounded metadata reader1.3GiB floor; original feature/model floors unchanged'
 return m.available
def literal(node,path):
 found=node.find(path);return None if found is None else ''.join(found.itertext()).strip()
def identifiers(node):
 return [] if node is None else [{'tag':x.tag,'attributes':dict(x.attrib),'text':(x.text or '').strip()} for x in node]
def attributes(node,path):
 return [{'TAG':literal(x,'TAG'),'VALUE':literal(x,'VALUE'),'UNITS':literal(x,'UNITS')} for x in node.findall(path)]
def decode(body,kind,requested):
 assert b'<!DOCTYPE' not in body and b'<!ENTITY' not in body
 root=ET.fromstring(body);nodes=[root] if root.tag==kind.upper() else root.findall('.//'+kind.upper())
 assert len(nodes)==1,'Expected exactly one fixed accession metadata object';node=nodes[0]
 ids=identifiers(node.find('IDENTIFIERS'))
 assert requested==node.get('accession') or requested in {x['text'] for x in ids},'Returned object lacks requested accession identity'
 record={'requested_accession':requested,'returned_attributes':dict(node.attrib),'identifiers':ids,'TITLE':literal(node,'TITLE')}
 if kind=='experiment':
  sample=node.find('DESIGN/SAMPLE_DESCRIPTOR');study=node.find('STUDY_REF');library=node.find('DESIGN/LIBRARY_DESCRIPTOR');layout=None if library is None else library.find('LIBRARY_LAYOUT')
  record.update({'DESIGN_DESCRIPTION':literal(node,'DESIGN/DESIGN_DESCRIPTION'),'LIBRARY_NAME':literal(node,'DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_NAME'),
   'LIBRARY_CONSTRUCTION_PROTOCOL':literal(node,'DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_CONSTRUCTION_PROTOCOL'),
   'POOLING_STRATEGY':literal(node,'DESIGN/LIBRARY_DESCRIPTOR/POOLING_STRATEGY'),
   'LIBRARY_LAYOUT':None if layout is None else [{'tag':x.tag,'attributes':dict(x.attrib)} for x in layout],
   'SAMPLE_DESCRIPTOR':None if sample is None else {'attributes':dict(sample.attrib),'identifiers':identifiers(sample.find('IDENTIFIERS'))},
   'STUDY_REF':None if study is None else dict(study.attrib),'EXPERIMENT_ATTRIBUTES':attributes(node,'EXPERIMENT_ATTRIBUTES/EXPERIMENT_ATTRIBUTE')})
 else:record.update({'DESCRIPTION':literal(node,'DESCRIPTION'),'SAMPLE_NAME':None if node.find('SAMPLE_NAME') is None else {x.tag:(x.text or '').strip() for x in node.find('SAMPLE_NAME')},'SAMPLE_ATTRIBUTES':attributes(node,'SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE')})
 return record
def run():
 fresh();path=OUT/'request_manifest.json';m=json.loads(path.read_text())
 assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h
 start=time.monotonic();records=[];failures=[];http_records=[]
 for item in m['requests']:
  accession=item['accession']
  try:
   fresh();remaining=150-(time.monotonic()-start);assert remaining>0,'Fixed150s acquisition budget elapsed'
   req=urllib.request.Request(item['URL'],headers={'User-Agent':'rnaexpress-public-qualitative-metadata/1.0','Accept':'application/xml'})
   with urllib.request.urlopen(req,timeout=min(10,remaining)) as response:
    assert response.status==200 and urllib.parse.urlparse(response.geturl()).hostname=='www.ebi.ac.uk'
    body=response.read(m['per_response_cap_bytes']+1);assert len(body)<=m['per_response_cap_bytes']
    http={'URL':item['URL'],'response_URL':response.geturl(),'status':response.status,'headers':dict(response.headers),'bytes':len(body),'SHA256':hashlib.sha256(body).hexdigest(),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
   raw=RAW/(accession+'.xml')
   with raw.open('xb') as f:f.write(body)
   save(RAW/(accession+'.http.json'),http);http_records.append(http)
   records.append(decode(body,item['kind'],accession));print(accession,'metadata',len(body),'bytes',flush=True)
  except Exception as error:
   failure={'accession':accession,'error_class':type(error).__name__,'message':str(error),'URL':item['URL']}
   failures.append(failure);save(OUT/(accession+'_failure.json'),failure);print(accession,'PRESERVED_METADATA_FAILURE',type(error).__name__,flush=True)
 save(OUT/'qualitative_metadata_records.json',{'records':records,'only_selected_metadata_fields_decoded':True,'whole_metadata_objects_downloaded':True,'links_followed':0,'lysate_pairing_not_inferred_from_suffixes_or_layout':True})
 save(OUT/'acquisition_receipt.json',{'status':'PASS_TWELVE_FIXED_METADATA_OBJECTS' if len(records)==12 and not failures else 'PARTIAL_METADATA_ACQUISITION_FAILURES_PRESERVED',
 'manifest_sha256':sha(path),'objects':len(records),'failures':failures,'http_records':http_records,'elapsed_seconds':time.monotonic()-start,
 'metadata_only_no_FASTQ_or_assay_count_requests':True,'records_sha256':sha(OUT/'qualitative_metadata_records.json'),'cost':0,'models_fit':0,'original_feature_model_floors_unchanged':True})
if __name__=='__main__':run()
