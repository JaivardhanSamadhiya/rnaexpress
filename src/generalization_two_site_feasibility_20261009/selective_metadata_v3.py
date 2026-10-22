"""Bounded strict JSON syntax traversal; only fixed WT row values are decoded."""
import json,re
from .common import strict_pairs
D=json.JSONDecoder(object_pairs_hook=strict_pairs)
NUMBER=re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
WS=" \r\n\t"
def whitespace(text,i,end=None):
 end=len(text) if end is None else end
 assert 0<=i<=end<=len(text)
 while i<end and text[i] in WS:i+=1
 return i
def string_end(text,i,end):
 assert i<end and text[i]=='"';i+=1
 while i<end:
  c=text[i]
  if c=='"':return i+1
  if c=="\\":
   i+=1;assert i<end
   if text[i]=="u":
    assert i+4<end and all(x in "0123456789abcdefABCDEF" for x in text[i+1:i+5]);i+=5;continue
   assert text[i] in '"\\/bfnrt';i+=1;continue
  assert ord(c)>=32;i+=1
 raise ValueError("Unterminated bounded JSON string")
def object_items(text,i,end,depth):
 assert depth<=64 and i<end and text[i]=="{";i=whitespace(text,i+1,end);seen=set();items=[]
 if i<end and text[i]=="}":return items,i+1
 while True:
  assert i<end and text[i]=='"';j=string_end(text,i,end)
  key=D.decode(text[i:j]);assert isinstance(key,str) and key not in seen,"Duplicate JSON key";seen.add(key)
  i=whitespace(text,j,end);assert i<end and text[i]==":"
  a=whitespace(text,i+1,end);b=value_end(text,a,end,depth+1);items.append((key,a,b))
  i=whitespace(text,b,end);assert i<end
  if text[i]=="}":return items,i+1
  assert text[i]==",";i=whitespace(text,i+1,end);assert i<end and text[i]!="}"
def value_end(text,i,end=None,depth=0):
 end=len(text) if end is None else end;i=whitespace(text,i,end)
 assert depth<=64 and i<end
 c=text[i]
 if c=='"':return string_end(text,i,end)
 if c=="{":return object_items(text,i,end,depth)[1]
 if c=="[":
  i=whitespace(text,i+1,end)
  if i<end and text[i]=="]":return i+1
  while True:
   i=whitespace(text,value_end(text,i,end,depth+1),end);assert i<end
   if text[i]=="]":return i+1
   assert text[i]==",";i=whitespace(text,i+1,end);assert i<end and text[i]!="]"
 if c in "-0123456789":
  match=NUMBER.match(text,i,end);assert match;return match.end()
 for literal in ("true","false","null"):
  if text.startswith(literal,i) and i+len(literal)<=end:return i+len(literal)
 raise ValueError("Invalid JSON value")
def fields(text,start=0,end=None):
 end=len(text) if end is None else end
 i=whitespace(text,start,end);items,j=object_items(text,i,end,0)
 assert whitespace(text,j,end)==end,"Unexpected bytes inside explicit object bound"
 yield from items
def selected_rows(text,wanted,decode_observer=None):
 wanted=set(wanted);assert wanted and all(type(x) is int and x>1 for x in wanted)
 def decode(a,b,purpose):
  if decode_observer is not None:decode_observer(purpose,text[a:b])
  return D.decode(text[a:b])
 top={k:(a,b) for k,a,b in fields(text)}
 assert {"rows","selected_columns_only","nonselected_values_analyzed"}<=set(top)
 assert decode(*top["selected_columns_only"],"header_columns")==["ID","Sequence"]
 assert decode(*top["nonselected_values_analyzed"],"header_exposure") is False
 a,b=top["rows"];assert text[a]=="[" and text[b-1]=="]";i=whitespace(text,a+1,b);found={};n=0
 while i<b-1:
  j=value_end(text,i,b);assert text[i]=="{";columns={k:(u,v) for k,u,v in fields(text,i,j)}
  assert set(columns)=={"source_excel_row","ID","Sequence"}
  number=decode(*columns["source_excel_row"],"source_excel_row")
  assert type(number) is int and 1<number<=10000;n+=1;assert n<=7000
  if number in wanted:
   assert number not in found
   row=decode(i,j,"selected_WT_row");assert isinstance(row["ID"],str) and isinstance(row["Sequence"],str)
   found[number]=row
  i=whitespace(text,j,b)
  if i==b-1:break
  assert text[i]==",";i=whitespace(text,i+1,b);assert i<b-1
 assert i==b-1 and set(found)==wanted,"Every fixed WT row must be found exactly once"
 return found,n
