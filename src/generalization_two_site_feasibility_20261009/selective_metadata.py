"""Skip nonselected literal JSON row values without decoding their sequences."""
import json,re
from .common import strict_pairs
D=json.JSONDecoder(object_pairs_hook=strict_pairs)
def whitespace(text,i):
 while i<len(text) and text[i] in " \r\n\t":i+=1
 return i
def value_end(text,i):
 i=whitespace(text,i);assert i<len(text)
 if text[i]=='"':
  j=i+1
  while j<len(text):
   if text[j]=="\\":j+=2;continue
   if text[j]=='"':return j+1
   assert ord(text[j])>=32
   j+=1
  raise ValueError("Unterminated string")
 if text[i] in "{[":
  stack=[text[i]];j=i+1
  while j<len(text):
   if text[j]=='"':j=value_end(text,j);continue
   if text[j] in "{[":stack.append(text[j])
   elif text[j] in "}]":
    assert stack and (stack[-1],text[j]) in (("{","}"),("[","]"))
    stack.pop()
    if not stack:return j+1
   j+=1
  raise ValueError("Unterminated container")
 j=i
 while j<len(text) and text[j] not in ",]} \r\n\t":j+=1
 assert j>i
 return j
def fields(text,start=0,end=None):
 end=len(text) if end is None else end;i=whitespace(text,start);assert text[i]=="{";i+=1;seen=set()
 while True:
  i=whitespace(text,i);assert i<end
  if text[i]=="}":
   assert whitespace(text,i+1)==end
   return
  key,j=D.raw_decode(text,i);assert isinstance(key,str) and key not in seen;seen.add(key)
  i=whitespace(text,j);assert text[i]==":";a=whitespace(text,i+1);b=value_end(text,a)
  yield key,a,b
  i=whitespace(text,b);assert i<end
  if text[i]=="}":
   assert whitespace(text,i+1)==end
   return
  assert text[i]==",";i=whitespace(text,i+1);assert text[i]!="}"
def selected_rows(text,wanted):
 """Whole bytes are resident; ONLY wanted row dictionaries and header scalars are semantically decoded."""
 wanted=set(wanted);assert wanted and all(type(x) is int and x>1 for x in wanted)
 top={k:(a,b) for k,a,b in fields(text)}
 assert "rows" in top and "selected_columns_only" in top and "nonselected_values_analyzed" in top
 assert D.decode(text[slice(*top["selected_columns_only"])])==["ID","Sequence"]
 assert D.decode(text[slice(*top["nonselected_values_analyzed"])]) is False
 a,b=top["rows"];assert text[a]=="[" and text[b-1]=="]";i=a+1;found={};n=0
 while True:
  i=whitespace(text,i)
  if text[i]=="]":assert i==b-1;break
  j=value_end(text,i);assert text[i]=="{";columns={k:(u,v) for k,u,v in fields(text,i,j)}
  assert set(columns)=={"source_excel_row","ID","Sequence"}
  row_number=D.decode(text[slice(*columns["source_excel_row"])])
  assert type(row_number) is int and 1<row_number<=10000;n+=1;assert n<=7000
  if row_number in wanted:
   assert row_number not in found
   row=D.decode(text[i:j])
   assert isinstance(row["ID"],str) and isinstance(row["Sequence"],str)
   found[row_number]=row
  i=whitespace(text,j)
  if text[i]=="]":assert i==b-1;break
  assert text[i]==",";i=whitespace(text,i+1);assert text[i]!="]"
 assert set(found)==wanted,"Every fixed WT row must be found exactly once"
 return found,n
