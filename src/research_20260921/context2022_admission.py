"""Free official context-comparison tables: acquire and inspect header rows only."""
from .common import ROOT,sha256,write_json
from .resources import URLS,fetch
from concurrent.futures import ThreadPoolExecutor
import json,sys,zipfile,openpyxl

DATA=ROOT/'data/external/research_20260921'
BASE='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-022-30183-0/MediaObjects/'
ASSETS={'context2022_data1.xlsx':BASE+'41467_2022_30183_MOESM4_ESM.xlsx',
        'context2022_data3.xlsx':BASE+'41467_2022_30183_MOESM6_ESM.xlsx'}


def acquire():
    URLS.update(ASSETS)
    with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(fetch,ASSETS))


def inspect():
    result={}
    for name in ASSETS:
        path=DATA/name
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None or '[Content_Types].xml' not in archive.namelist():
                raise ValueError('Invalid workbook')
            active=[n for n in archive.namelist() if 'vbaproject' in n.lower() or 'externallinks' in n.lower()]
        workbook=openpyxl.load_workbook(path,read_only=True,data_only=True)
        sheets=[{'sheet':s.title,'rows':s.max_row,'columns':s.max_column,
                 'first_row':list(s.iter_rows(min_row=1,max_row=1,values_only=True))} for s in workbook]
        workbook.close()
        result[name]={'sha256':sha256(path),'source':ASSETS[name],'archive_crc_valid':True,
                       'active_content':active,'sheets':sheets}
    write_json(ROOT/'results/research_20260921/context2022_schema.json',result)
    print(json.dumps(result,indent=2,default=str),flush=True)


if __name__=='__main__': {'acquire':acquire,'inspect':inspect}[sys.argv[1]]()
