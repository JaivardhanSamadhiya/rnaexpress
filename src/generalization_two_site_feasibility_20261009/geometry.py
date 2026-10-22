"""Invented or admitted WT strings only. Does not fold RNA or estimate occupancy."""
import re,itertools,math
from .design import RULE
PATTERN=re.compile(RULE["core_regex"])
def sites(sequence,energy_function):
 assert isinstance(sequence,str) and len(sequence)<=140 and set(sequence)<=set("ACGT")
 rna=sequence.replace("T","U")
 matched=[i for i in range(max(0,len(rna)-7)) if PATTERN.fullmatch(rna[i:i+8])]
 output=[];terminal=[]
 for i in matched:
  if i+9>len(rna):
   terminal.append({"core_start_0based":i,"core_end_0based_exclusive":i+8,"reason":"No literal9th base"})
   continue
  contact=rna[i:i+9];energy=energy_function(contact)
  assert math.isfinite(energy)
  output.append({"start_0based":i,"core_end_0based_exclusive":i+8,"contact_end_0based_exclusive":i+9,
   "core_RNA":rna[i:i+8],"contact_RNA":contact,"fixed_consecutive_energy_kcal":energy,
   "fixed_recognition_positions_0based":[0,1,2,3,5,6,7],"free_recognition_position_0based":4})
 return output,terminal
def pairs(site_records):
 records=sorted(site_records,key=lambda x:x["start_0based"]);result=[]
 assert len({x["start_0based"] for x in records})==len(records)
 for a,b in itertools.combinations(records,2):
  if a["contact_end_0based_exclusive"]>b["start_0based"]:continue
  result.append({"left_start_0based":a["start_0based"],"right_start_0based":b["start_0based"],
   "left_contact_end_0based_exclusive":a["contact_end_0based_exclusive"],
   "right_contact_end_0based_exclusive":b["contact_end_0based_exclusive"],
   "intervening_bases":b["start_0based"]-a["contact_end_0based_exclusive"],
   "core_gap_bases":b["start_0based"]-a["core_end_0based_exclusive"],
   "pair_energy_sum_kcal":math.fsum((a["fixed_consecutive_energy_kcal"],b["fixed_consecutive_energy_kcal"]))})
 return result
def select_pair(records):
 return min(records,key=lambda p:(p["pair_energy_sum_kcal"],p["left_start_0based"],p["right_start_0based"])) if records else None
def audit_sequence(sequence,energy_function):
 site_records,terminal=sites(sequence,energy_function);p=pairs(site_records)
 return {"sites":site_records,"terminal_ineligible_cores":terminal,"all_nonoverlapping_pairs":p,
  "site_count":len(site_records),"nonoverlapping_pair_count":len(p),"selected_pair":select_pair(p),
  "same_start_unique_site_count":True,"sequence_sha256":__import__("hashlib").sha256(sequence.encode()).hexdigest()}
