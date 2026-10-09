"""Verify attribution without recording private emails or credentials."""
import datetime, hashlib, json, os, pathlib, subprocess
from .audit import api, git, ROOT, OUT

def main():
    pre=json.loads((OUT/'prepublication_audit.json').read_text())
    pairs=dict(line.split('=',1) for line in git('credential','fill',input='protocol=https\nhost=github.com\n\n').stdout.splitlines() if '=' in line)
    user,error=api('/user',pairs['password']); assert user and user['login']=='JaivardhanSamadhiya',error
    remote,err=api('/repos/JaivardhanSamadhiya/rnaexpress/commits/'+pre['remote_main_before'],pairs['password'])
    configured=git('config','user.email').stdout.strip()
    old_emails=git('log','--format=%ae',pre['remote_main_before']+'..'+pre['local_HEAD_at_audit']).stdout.splitlines()
    noreply=f"{user['id']}+{user['login']}@users.noreply.github.com"
    associated={noreply.lower(),f"{user['login']}@users.noreply.github.com".lower()}
    if remote and (remote.get('author') or {}).get('login')==user['login']:
        associated.add(remote['commit']['author']['email'].lower())
    current_associated=configured.lower() in associated
    # Use the account's actual GitHub-issued noreply address for future commits.
    # No historical author/name/date is changed.
    if not current_associated: git('config','--local','user.email',noreply)
    now=git('config','user.email').stdout.strip()
    out={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_FUTURE_AUTHOR_ATTRIBUTION','authenticated_login':user['login'],'remote_commit_API_error':err,'remote_commit_author_linked_to_account':bool(remote and (remote.get('author') or {}).get('login')==user['login']),'previous_configured_email_association_proven':current_associated,'previous_configured_email_SHA256':hashlib.sha256(configured.encode()).hexdigest(),'repository_local_email_changed':not current_associated,'future_commits_use_verified_account_noreply_or_existing_server_linked_email':now.lower() in associated,'outgoing_backlog_author_association_proven_count':sum(x.lower() in associated for x in old_emails),'outgoing_backlog_author_association_unknown_count':sum(x.lower() not in associated for x in old_emails),'author_emails_recorded':False,'historical_commits_rewritten':False,'private_email_API_limit':'The user/emails endpoint returned 404; the initial audit false booleans mean unverified association, not proof of non-association. This receipt supersedes that interpretation.','graph_limitations':'Backlog preserves original author dates. Publishing alone does not guarantee historical attribution; Graph can take 24 hours.'}
    (OUT/'author_attribution_receipt.json').open('x',encoding='utf-8',newline='\n').write(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
