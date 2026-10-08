
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[2]
NS="generalization_fly_construct_metadata_20261008"
OUT=ROOT/"results"/NS;RAW=ROOT/"data/raw"/NS
def run():
    candidate=json.loads((OUT/"sequence_table_text_candidates.json").read_text())
    text=next(p["text"] for p in candidate["pages"] if p["page"]==16)
    labels=["TLS","TLS∆b","TLS-2xGCED1","TLS-GCED2","TLS-2xGCED1+GCED2","TLS-GCED1/ED2","TLS-CGED1/ED2","TLS-AUED1/ED2","KSE","ILS","ILS∆b","hSL1","hSL1∆b","hSL2","bcdSLV (EM)","bcdSLV (MST)","bcdSLV∆b","GLS (EM)","GLS (MST)","GLS∆b","2NUE RNA","hSL1-hSL2","TLS-KSE"]
    inventory={}
    for label in labels:
        matches=list(re.finditer(r"(?<!\S)"+re.escape(label)+r"\s+([ACGUacgu]+(?:\s+[ACGUacgu]+)*)(?=\s|$)",text))
        assert len(matches)==1,(label,len(matches))
        sequence=re.sub(r"\s","",matches[0].group(1))
        assert sequence and set(sequence)<=set("ACGUacgu")
        inventory[label]={"source_sequence_with_case":sequence,"length":len(sequence),"non_native_lowercase_positions0":[i for i,b in enumerate(sequence) if b.islower()]}
    refs={}
    for acc in ("AY060415","X15905","M14954.2","NM_169159.4","NM_057220.3"):
        path=RAW/(acc+".gb");body=path.read_text()
        version=re.search(r"^VERSION\s+(\S+)",body,re.M).group(1)
        expected=int(re.search(r"^LOCUS\s+\S+\s+(\d+)\s+bp",body,re.M).group(1))
        origin=body.split("\nORIGIN",1)[1].split("//",1)[0]
        dna=re.sub(r"[^a-zA-Z]","",origin).upper();assert len(dna)==expected and set(dna)<=set("ACGTN")
        refs[acc]={"version":version,"length":len(dna),"record_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"rna":dna.replace("T","U")}
    bindings=[]
    for label,acc,span,reported in [
        ("TLS","AY060415",(1608,3061),1490),("hSL1","X15905",(1185,1845),730),
        ("ILS","M14954.2",(2932,3498),573),("bcdSLV (EM)","NM_169159.4",(1702,2536),839),
        ("GLS (EM)","NM_057220.3",(1,1718),1718)]:
        native="".join(b for b in inventory[label]["source_sequence_with_case"] if b.isupper())
        rna=refs[acc]["rna"];hits=[m.start() for m in re.finditer("(?="+re.escape(native)+")",rna)]
        bindings.append({"stem_label":label,"reference_version":refs[acc]["version"],"stem_native_length":len(native),
            "exact_forward_reference_start0_matches":hits,"author_injected_native_span1":span,
            "native_span_length":span[1]-span[0]+1,"reported_injected_length":reported,
            "terminal_or_context_length_difference":reported-(span[1]-span[0]+1),
            "stem_source_sequence_is_not_complete_injected_sequence":True})
    wild=inventory["TLS"]["source_sequence_with_case"];contrasts=[]
    for label,expected in (("TLS-GCED2",2),("TLS-2xGCED1",4),("TLS-2xGCED1+GCED2",6)):
        mutant=inventory[label]["source_sequence_with_case"];assert len(wild)==len(mutant)
        edits=[{"table_stem_position0":i,"reference":a,"alternate":b} for i,(a,b) in enumerate(zip(wild,mutant)) if a!=b]
        assert len(edits)==expected
        contrasts.append({"mutant":label,"WT":"TLS","substitution_count":len(edits),"exact_table_edits":edits,
            "full_injected_parent_mutant_certificate":False,"numerical_localization_outcomes_admitted":False})
    payload={"status":"PASS_AUTHOR_STEM_SEQUENCE_METADATA_NOT_FULL_INJECTION_ADMISSION",
        "source_supplement_sha256":candidate["source_sha256"],"sequence_table_pdf_page":16,"sequence_table_printed_page":15,
        "visual_table_render_sha256":hashlib.sha256((OUT/"sequence_table3_page16.png").read_bytes()).hexdigest(),
        "sequences":inventory,"references":{k:{x:y for x,y in v.items() if x!="rna"} for k,v in refs.items()},
        "native_stem_reference_bindings":bindings,"K10_substitution_metadata":contrasts,"source_table_visually_reviewed":True,
        "localization_models_fit":0,"numerical_source_workbooks_opened":False,"injected_sequence_certification_pending":True,
        "metadata_recipe_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "post_acquisition_metadata_recipe_not_prospective_outcome_protocol":True}
    path=OUT/"stem_sequence_metadata_receipt.json"
    with path.open("xb") as f:f.write((json.dumps(payload,sort_keys=True,indent=2)+"\n").encode())
    print("Author sequence inventory",len(inventory))
    print("Bindings",json.dumps(bindings,indent=2))
    print("K10 differences",json.dumps(contrasts,indent=2))
if __name__=="__main__":run()
