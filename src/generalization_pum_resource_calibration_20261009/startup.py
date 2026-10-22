"""Short ordinary background admission wait; execute exactly one approved phase."""
import argparse,datetime,json,time
from . import controller,worker,winjob

def run(phase):
 worker.admitted();path=worker.OUT/(phase+'_admission_wait.jsonl')
 assert not path.exists(),'Preserve existing admission attempt'
 started=time.monotonic();sample=0
 with path.open('x',encoding='utf-8',newline='\n',buffering=1) as log:
  while True:
   state=winjob.memory();elapsed=time.monotonic()-started
   # Extra32MiB startup headroom protects the following child-import admission;
   # original approved floors remain exact in every controller/child check.
   ready=state['physical_available']>=512*2**20 and state['commit_headroom']>=896*2**20+2**30+32*2**20 and state['disk_available']>=2**30
   if sample%10==0 or ready or elapsed>=120:
    log.write(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':elapsed,'memory':state,'ready_with_extra32MiB_start_buffer':ready,'no_scientific_child_started':True})+'\n')
   if ready:
    print('ADMITTED_AFTER_ORDINARY_BACKGROUND_WAIT',phase,elapsed,flush=True);controller.run(phase);return
   if elapsed>=120:
    print('NO_CHILD_ADMITTED_WITHIN120_SECONDS; all approved floors preserved',flush=True);return
   sample+=1;time.sleep(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=sorted(worker.MODULES),required=True);a=p.parse_args();run(a.phase)
