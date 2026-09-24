"""Outcome-free construct/replicate inventory for the public Faraway library."""
from .common import ROOT,sha256,write_json,write_new
import csv,io,json,zipfile,xml.etree.ElementTree as ET
from collections import Counter,defaultdict

DATA=ROOT/'data/external/research_20260921'
OUT=ROOT/'results/research_20260921'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
SCHEMAS={
 'transfection_1':('sheet2.xml',{'A':'bc_number','B':'n_introns','C':'n_opt','D':'replicate','H':'structure','I':'int_pattern'}),
 'transfection_2':('sheet3.xml',{'A':'bc_number','B':'n_introns','C':'n_opt','D':'time','E':'replicate','I':'structure','J':'int_pattern'}),
 'dox_timepoints':('sheet4.xml',{'A':'bc_number','B':'n_introns','C':'n_opt','D':'time','E':'replicate','I':'structure','J':'int_pattern'}),
 'clk_vs_dmso':('sheet5.xml',{'A':'bc_number','B':'n_introns','C':'n_opt','D':'experiment','E':'replicate','I':'structure','J':'int_pattern'})}


def decode_genotype(structure,introns):
    g=structure.split('-');i=introns.split('-')
    if len(g)!=8 or len(i)!=8 or set(g)-{'Opt','DeO'} or set(i)-{'Int','NoInt'}:
        raise ValueError('Unknown genotype encoding')
    return ''.join('1' if s=='Opt' else '0' for s in g)+''.join('1' if s=='Int' else '0' for s in i)


def metadata_rows(path,sheet):
    if sheet not in SCHEMAS:raise PermissionError('Non-admitted metadata sheet')
    member,columns=SCHEMAS[sheet]
    with zipfile.ZipFile(path) as z:
        # Only return whitelisted metadata cells. Outcome cell values are never decoded.
        strings=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        for _,row in ET.iterparse(z.open('xl/worksheets/'+member),events=['end']):
            if row.tag!='{'+NS['m']+'}row':continue
            number=int(row.get('r'));values={}
            for cell in row:
                col=''.join(x for x in cell.get('r','') if x.isalpha())
                if col not in columns:continue
                v=cell.find('m:v',NS)
                if v is not None:values[columns[col]]=strings[int(v.text)] if cell.get('t')=='s' else v.text
            if number==1:
                if any(values.get(n)!=n for n in columns.values()):raise ValueError('Metadata header changed')
            elif values:
                values.update(sheet=sheet,excel_row=number)
                yield values
            row.clear()


def run():
    path=DATA/'faraway2025_supptable_3.xlsx'
    if sha256(path)!='e99bd2951ff4339916002a76b72d1a1adde2a2dc5a72ed26e1cbf8829da62760':raise ValueError('Source changed')
    rows=[];summaries={}
    for sheet in SCHEMAS:
        subset=list(metadata_rows(path,sheet));seen=defaultdict(set);groups=defaultdict(set)
        for r in subset:
            genotype=decode_genotype(r['structure'],r['int_pattern']);r['genotype']=genotype
            if sum(map(int,genotype[:8]))!=int(r['n_opt']) or sum(map(int,genotype[8:]))!=int(r['n_introns']):
                raise ValueError('Genotype count mismatch')
            seen[r['bc_number']].add(genotype)
            groups[(r.get('time',r.get('experiment','16h')),r['replicate'])].add(genotype)
        if any(len(x)!=1 for x in seen.values()):raise ValueError('Ambiguous within-sheet barcode genotype')
        summaries[sheet]={'metadata_rows':len(subset),'barcode_ids':len(seen),'unique_genotypes':len(set(r['genotype'] for r in subset)),
            'condition_replicate_unique_genotypes':{'/'.join(k):len(v) for k,v in sorted(groups.items())}}
        rows.extend(subset)
    f=io.StringIO();columns=['sheet','excel_row','bc_number','n_introns','n_opt','replicate','time','experiment','structure','int_pattern','genotype']
    w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader();w.writerows(rows)
    write_new(OUT/'faraway2025_construct_metadata.csv',f.getvalue().encode())
    a={(r['bc_number'],r['replicate'],r['genotype']) for r in rows if r['sheet']=='transfection_1'}
    overlap={}
    for condition in sorted(set(r.get('time') for r in rows if r['sheet']=='transfection_2')):
        b={(r['bc_number'],r['replicate'],r['genotype']) for r in rows if r['sheet']=='transfection_2' and r['time']==condition}
        overlap[condition]={'rows':len(b),'metadata_keys_shared_with_transfection1':len(a&b)}
    result={'scope':'Only construct identities, intron/GA design, time and replicate metadata; all localization and stability outcomes unopened.',
        'sheet_inventory':summaries,'transfection2_metadata_overlap':overlap,
        'warning':'Barcode IDs are sheet-specific. Shared genotype or metadata keys across sheets are not independent biological observations; compare sample provenance.',
        'source_sha256':sha256(path),'code_sha256':sha256(__file__)}
    write_json(OUT/'faraway2025_metadata_inventory.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':run()
