"""Strict ordered JSON objects, including native multi-track duplicate metadata."""
from __future__ import annotations
from collections import Counter
import datetime,json,math,re
from . import common as c
class Object(list):pass
class SchemaError(ValueError):pass
def check(ok,message):
 if not ok:raise SchemaError(message)
def pairs(payload):
 try:r=json.loads(payload,object_pairs_hook=Object,parse_constant=lambda x:(_ for _ in ()).throw(SchemaError('Nonfinite JSON constant')))
 except (ValueError,UnicodeDecodeError) as e:raise SchemaError('Invalid JSON') from e
 check(isinstance(r,Object),'Expected JSON object');return r
def occurrences(obj,key):return [v for k,v in obj if k==key]
def one(obj,key):
 a=occurrences(obj,key);check(len(a)==1,'Exactly one '+key+' required');return a[0]
def regular(obj):
 check(isinstance(obj,Object),'Nested object required')
 check(len({k for k,v in obj})==len(obj),'Duplicate nested keys');return dict(obj)
def moment(value,stamp):
 check(isinstance(value,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',value) is not None,'Exact source timestamp required')
 try: datetime.datetime.fromisoformat(value)
 except ValueError as error: raise SchemaError('Invalid source calendar time') from error
 check(type(stamp) is int and stamp>0,'Raw positive source timestamp required; no timezone invention')
def schema(payload,track,physical=False,expected_type=None):
 o=pairs(payload);check(not occurrences(o,'error') and not occurrences(o,'maxItemsLimit'),'Schema error/truncation')
 check(one(o,'genome')=='mm10' and one(o,'track')==track,'Exact metadata source mismatch')
 table=occurrences(o,'table');check(not table or all(isinstance(v,str) and v==track for v in table),'Unexpected schema source table replacement')
 tm=one(o,'dataTime');stamp=one(o,'dataTimeStamp');moment(tm,stamp)
 cols=one(o,'columnTypes');check(isinstance(cols,list) and not isinstance(cols,Object),'Schema columns must be an array')
 columns=[regular(v) for v in cols]
 check(all(isinstance(v.get('name'),str) and bool(v['name']) for v in columns),'Missing/nonstring schema column name')
 names=[v['name'] for v in columns]
 check(len(names)==len(set(names)),'Duplicate schema columns')
 if physical:
  check(not any(v is True for v in occurrences(o,'splitTable')),'Physical schema did not identify exact requested table')
  check({'chrom','chromStart','chromEnd','span','file','offset'}.issubset(names),'Physical wig schema missing required storage fields')
  typ=None
 else:
  check(names==['chrom','start','end','value'],'Logical native wig columns differ')
  check(all(isinstance(v.get('jsonType'),str) for v in columns),'Missing/nonstring logical schema JSON type')
  coltypes=[v['jsonType'] for v in columns]
  check(coltypes==['string','number','number','number'],'Logical output types differ')
  types=occurrences(o,'type');check(bool(types) and all(t==types[0] for t in types),'Conflicting logical track types')
  typ=types[0];check(isinstance(typ,str) and typ==expected_type and typ.startswith('wig ') and not typ.startswith('wigMaf'),'Exact admitted wig type differs')
  check(one(o,'splitTable') is True,'Require source-certified split SQL storage')
 return {'source_table':track,'dataTime':tm,'dataTimeStamp':stamp,'trackType':typ,'column_names':names}
def values(payload,query,expected):
 o=pairs(payload)
 check(not occurrences(o,'error') and not occurrences(o,'maxItemsLimit'),'Value error/truncation')
 check(one(o,'genome')=='mm10','Wrong value assembly')
 allowed={'downloadTime','downloadTimeStamp','genome','dataTime','dataTimeStamp','trackType','track','chrom','start','end','itemsReturned','totalTime','totalTimeMs'}|set(c.TRACKS)
 check(all(k in allowed for k,v in o),'Unknown value root schema')
 singleton={'downloadTime','downloadTimeStamp','genome','itemsReturned','totalTime','totalTimeMs'}
 for key in singleton:check(len(occurrences(o,key))<=1,'Duplicate singleton '+key)
 duplicate={'dataTime','dataTimeStamp','trackType','track','chrom','start','end'}
 for key in duplicate:check(len(occurrences(o,key))==2,'Require two exact per-track '+key+' groups')
 groups=[];pending={};current=None;arrays={};count=0
 for key,value in o:
  if key in ('dataTime','dataTimeStamp','trackType'):
   check(current is None and key not in pending,'Misordered/repeated source metadata');pending[key]=value
  elif key=='track':
   index=len(groups);check(index<2 and value==c.TRACKS[index],'Declared source track order differs')
   check(set(pending)=={'dataTime','dataTimeStamp','trackType'},'Incomplete source group')
   current={'track':value,**pending};pending={}
  elif key in ('chrom','start','end'):
   check(current is not None and key not in current,'Coordinate metadata outside track group');current[key]=value
  elif key in c.TRACKS:
   check(current is not None and current['track']==key and key not in arrays,'Misbound named value array')
   check(set(current)=={'track','dataTime','dataTimeStamp','trackType','chrom','start','end'},'Incomplete ordered group')
   check(type(current['start']) is int and type(current['end']) is int and current['chrom']==query['chrom'] and current['start']==query['start0'] and current['end']==query['end0'],'Source interval differs')
   ex=expected[key];moment(current['dataTime'],current['dataTimeStamp'])
   check(all(current[k]==ex[k] for k in ('dataTime','dataTimeStamp','trackType')),'Pinned chromosome source metadata changed')
   check(isinstance(value,list) and not isinstance(value,Object),'Track values must be an array')
   got={}
   for raw in value:
    row=regular(raw);check(set(row)=={'chrom','start','end','value'},'Unexpected score row fields')
    s,e,v=row['start'],row['end'],row['value']
    check(row['chrom']==query['chrom'] and type(s) is int and type(e) is int and query['start0']<=s<e<=query['end0'],'Overhanging/invalid score interval')
    check(type(v) in (int,float) and math.isfinite(v),'Invalid numeric score')
    if key=='phastCons60way':check(0<=v<=1,'phastCons outside0..1')
    for pos in range(s,e):check(pos not in got,'Overlapping ambiguous score rows');got[pos]=float(v)
   count+=len(value);arrays[key]=got;groups.append(current);current=None
 check(not pending and current is None and len(groups)==2 and set(arrays)==set(c.TRACKS),'Incomplete dual-track response')
 count_fields=occurrences(o,'itemsReturned')
 check((not count_fields and count==0) or (len(count_fields)==1 and type(count_fields[0]) is int and count_fields[0]==count),'Exact total row count differs')
 check(count<10000,'Uncertified output cap reached')
 return arrays,groups
