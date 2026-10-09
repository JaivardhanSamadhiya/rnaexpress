"""Publish audited history as ordinary fast forwards, with bounded Git packing."""
import argparse, datetime, hashlib, json, os, pathlib, subprocess, time
from .audit import ROOT, OUT, git

def protect():
    p=ROOT/'results/generalization_prelib_binding_descriptive_20261008/protected_user_file_snapshot.json'
    d=json.loads(p.read_text())['user_modified_files_at_turn_start']
    for path,want in d.items():
        got=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        assert got==want,(path,'protected user modification changed')
    return len(d)

def main():
    args=argparse.ArgumentParser();args.add_argument('--execute-authorized-push',action='store_true');opts=args.parse_args()
    assert opts.execute_authorized_push, 'Explicit execution flag required'
    pre=json.loads((OUT/'prepublication_audit.json').read_text());author=json.loads((OUT/'author_attribution_receipt.json').read_text())
    assert pre['status']=='PASS_READ_ONLY_PUBLICATION_AUDIT'
    assert pre['repo']['full_name']=='JaivardhanSamadhiya/rnaexpress' and pre['repo']['default_branch']=='main' and not pre['repo']['fork']
    assert author['future_commits_use_verified_account_noreply_or_existing_server_linked_email']
    assert git('branch','--show-current').stdout.strip()=='main'
    assert not git('diff','--cached','--name-only').stdout.strip()
    assert git('remote','get-url','origin').stdout.strip()=='https://github.com/JaivardhanSamadhiya/rnaexpress.git'
    local=git('rev-parse','HEAD').stdout.strip()
    assert git('merge-base','--is-ancestor',pre['local_HEAD_at_audit'],local,check=False).returncode==0
    targets=[b['target'] for b in pre['publication_batches']]
    if targets[-1]!=local: targets.append(local)
    OUT.mkdir(exist_ok=True,parents=True)
    log=OUT/'push_events.jsonl'
    def event(data):
        data['UTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with log.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data)+'\n')
        print(json.dumps(data),flush=True)
    remote=git('ls-remote','origin','refs/heads/main').stdout.split()[0]
    admitted={pre['remote_main_before'],*targets}
    assert remote in admitted, 'Remote advanced outside audited roster; preserve and review'
    started=time.monotonic()
    for number,target in enumerate(targets,1):
        if git('merge-base','--is-ancestor',target,remote,check=False).returncode==0:
            event({'phase':'already_published','batch':number,'target':target});continue
        assert git('merge-base','--is-ancestor',remote,target,check=False).returncode==0
        assert git('ls-remote','origin','refs/heads/main').stdout.split()[0]==remote, 'Concurrent remote update'
        protected_count=protect()
        cmd=['git','-c','maintenance.auto=false','-c','gc.auto=0','-c','pack.threads=1','-c','pack.windowMemory=32m','-c','pack.deltaCacheSize=32m','push','--porcelain','origin',target+':refs/heads/main']
        event({'phase':'push_started','batch':number,'target':target,'previous':remote,'protected_user_files_verified':protected_count,'pack_threads':1,'pack_window_memory_MiB':32,'pack_delta_cache_MiB':32,'force':False})
        path=OUT/f'batch_{number:02d}.log'
        with path.open('ab') as f:
            p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=1800,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'})
        now=git('ls-remote','origin','refs/heads/main').stdout.split()[0]
        event({'phase':'push_completed' if p.returncode==0 and now==target else 'push_failed','batch':number,'returncode':p.returncode,'remote_main':now,'log':str(path.relative_to(ROOT))})
        assert p.returncode==0 and now==target, 'Push failure; no automatic retries or history rewrite'
        remote=now
    receipt={'status':'PASS_REMOTE_MAIN_SYNCHRONIZED','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'initial_remote_main':pre['remote_main_before'],'published_HEAD':local,'remote_main_verified':remote,'published_historical_commits':pre['ahead_count'],'additional_commits_since_initial_audit':int(git('rev-list','--count',pre['local_HEAD_at_audit']+'..'+local).stdout),'elapsed_seconds':time.monotonic()-started,'protected_user_files_verified':protect(),'force_push':False,'history_rewrite':False,'payment':False,'credentials_recorded':False,'scientific_payloads_opened':False,'safeguards_changed':False}
    (OUT/'publication_receipt.json').open('x',encoding='utf-8',newline='\n').write(json.dumps(receipt,indent=2)+'\n');event(receipt)
if __name__=='__main__':main()
