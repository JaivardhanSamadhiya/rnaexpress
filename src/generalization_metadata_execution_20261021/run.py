"""One ordinary background launch of the frozen WT metadata audit/replay."""
import argparse,datetime,json,pathlib,time
from src.generalization_pum_resource_calibration_20261009.winjob import memory
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'results/generalization_metadata_execution_20261021'
def run(stage):
 assert stage in ('audit','replay')
 from src.generalization_two_site_feasibility_20261009 import supervise_v3
 supervise_v3.bind_v3()
 start=time.monotonic();n=0
 with (OUT/(stage+'_admission.jsonl')).open('x',encoding='utf-8',newline='\n',buffering=1) as log:
  while True:
   state=memory();elapsed=time.monotonic()-start;ready=state['physical_available']>=1.4*2**30
   if n%10==0 or ready or elapsed>=120:log.write(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':elapsed,'memory':state,'ready_with_stricter1_4GiB_launch_buffer':ready})+'\n')
   if ready:break
   if elapsed>=120:print('NO_METADATA_CHILD_ADMITTED; original1.3GiBfloor preserved',flush=True);return
   n+=1;time.sleep(1)
 supervise_v3.run(stage)
 print('FROZEN_METADATA_STAGE_COMPLETE',stage,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=('audit','replay'),required=True);a=p.parse_args();run(a.stage)
