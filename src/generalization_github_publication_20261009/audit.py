"""Read-only Git publication audit. Credentials never leave process memory."""
import collections, datetime, json, os, pathlib, re, subprocess, urllib.request, urllib.error
ROOT=pathlib.Path('D:/rnaexpress'); OUT=ROOT/'results/generalization_github_publication_20261009'
def git(*args, check=True, input=None):
    p=subprocess.run(['git',*args],cwd=ROOT,input=input,text=True,capture_output=True,timeout=180,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'})
    if check and p.returncode: raise RuntimeError('Git operation failed: '+args[0])
    return p

def api(path, secret):
    req=urllib.request.Request('https://api.github.com'+path,headers={'Authorization':'Bearer '+secret,'Accept':'application/vnd.github+json','User-Agent':'rnaexpress-publication-audit','X-GitHub-Api-Version':'2022-11-28'})
    try:
        with urllib.request.urlopen(req,timeout=25) as r: return json.load(r),None
    except urllib.error.HTTPError as e: return None,{'HTTP_status':e.code}
    except Exception as e: return None,{'error_type':type(e).__name__}

def main():
    origin=git('remote','get-url','origin').stdout.strip()
    assert origin=='https://github.com/JaivardhanSamadhiya/rnaexpress.git'
    remote=git('ls-remote','origin','refs/heads/main').stdout.split()[0]
    head=git('rev-parse','HEAD').stdout.strip()
    assert git('merge-base','--is-ancestor',remote,head,check=False).returncode==0
    assert not git('diff','--cached','--name-only').stdout.strip()
    creds=git('credential','fill',check=False,input='protocol=https\nhost=github.com\n\n')
    pairs=dict(line.split('=',1) for line in creds.stdout.splitlines() if '=' in line)
    secret=pairs.get('password'); assert secret, 'No credential available'
    repo,repo_error=api('/repos/JaivardhanSamadhiya/rnaexpress',secret)
    user,ue=api('/user',secret)
    emails,ee=api('/user/emails',secret)
    associated=set(x['email'].lower() for x in (emails or []) if x.get('verified'))
    if user:
        associated|={f"{user['login']}@users.noreply.github.com".lower(),f"{user['id']}+{user['login']}@users.noreply.github.com".lower()}
    config_email=git('config','user.email').stdout.strip().lower()
    authors=git('log','--format=%ae',remote+'..HEAD').stdout.splitlines()
    dates=collections.Counter(git('log','--format=%aI',remote+'..HEAD').stdout.splitlines())
    objects=git('rev-list','--objects',remote+'..HEAD').stdout.splitlines()
    suspicious=[]
    for line in objects:
        if ' ' not in line: continue
        oid,name=line.split(' ',1)
        if re.search(r'(^|/)(\.env(?:\..*)?|id_rsa|credentials(?:\.json)?|\.netrc)$|(?:^|/)(?:\.aws|\.ssh)(?:/|$)|\.(?:pem|key)$',name,re.I):
            suspicious.append({'object':oid,'path':name})
    boundaries=[]
    commits=git('rev-list','--first-parent','--reverse',remote+'..HEAD').stdout.splitlines()
    previous=remote
    for ix in range(0,len(commits),25):
        target=commits[min(ix+24,len(commits)-1)]
        ids=git('rev-list','--objects','--no-object-names',previous+'..'+target).stdout
        chk=git('cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)',input=ids).stdout.splitlines()
        blobs=[(parts[0],int(parts[2])) for line in chk if len(parts:=line.split())==3 and parts[1]=='blob']
        size=sum(s for _,s in blobs)
        assert max((s for _,s in blobs),default=0)<100*1024**2
        assert size<1536*1024**2, 'Publication batch raw-size cap exceeded'
        boundaries.append({'target':target,'previous':previous,'commits_in_first_parent_batch':min(25,len(commits)-ix),'introduced_blobs':len(blobs),'uncompressed_blob_bytes':size,'maximum_blob_bytes':max((s for _,s in blobs),default=0)})
        previous=target
    receipt={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_READ_ONLY_PUBLICATION_AUDIT' if repo and user and not suspicious else 'REVIEW_REQUIRED','remote_main_before':remote,'local_HEAD_at_audit':head,'remote_latest_commit_committer_date':git('show','-s','--format=%cI',remote).stdout.strip(),'ahead_count':len(authors),'index_empty':True,'remote_is_ancestor':True,'remote_URL_verified':True,'repo':{k:repo.get(k) for k in ('full_name','private','fork','default_branch','pushed_at','updated_at','visibility')} if repo else None,'repository_API_error':repo_error,'authenticated_login':user.get('login') if user else None,'account_API_error':ue,'verified_emails_API_error':ee,'configured_author_email_account_associated':config_email in associated if user else None,'outgoing_authors_associated_count':sum(x.lower() in associated for x in authors),'outgoing_authors_total_count':len(authors),'outgoing_author_dates_min':min(dates,default=None),'outgoing_author_dates_max':max(dates,default=None),'credential_bytes_or_email_values_recorded':False,'suspicious_sensitive_file_names':suspicious,'publication_batches':boundaries,'history_rewrite':False,'force_push':False,'LFS_used':False,'purchase_or_payment':False,'local_user_changes_staged':False,'source_scope':'Git object names/types/sizes and commit metadata only; no scientific outcome payloads opened'}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'prepublication_audit.json').open('x',encoding='utf-8',newline='\n').write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__': main()
