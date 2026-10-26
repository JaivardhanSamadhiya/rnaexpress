"""Real fresh new-process owner and C-native checks; no injectable owner."""
import ctypes as C
import os
import time
from . import common as c
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_owned_workingset_probe_v2_20261025 import working_set


class CurrentOwner:
    def __init__(self,parent_pid,generation,birth_sha,identity_sha,started,manifest):
        self.parent_pid,self.generation,self.birth_sha,self.identity_sha,self.started=parent_pid,generation,birth_sha,identity_sha,started
        self.expected_input_map_sha=c.digest(c.canonical(c.bind_read_set(manifest)))
        self.closed=False;self.owner_record_sha=None;self.fresh()

    def fresh(self):
        assert not self.closed
        c.source_mode();assert os.getppid()==self.parent_pid
        birth_raw=c.BIRTH.read_bytes();identity_raw=c.CHILD_IDENTITY.read_bytes();owner_raw=c.CHILD_OWNER.read_bytes()
        assert c.digest(birth_raw)==self.birth_sha and c.digest(identity_raw)==self.identity_sha
        if self.owner_record_sha is None:self.owner_record_sha=c.digest(owner_raw)
        assert c.digest(owner_raw)==self.owner_record_sha
        birth,identity,actual=c.decode(birth_raw),c.decode(identity_raw),c.decode(owner_raw)
        assert birth['status']=='NEW_EXCLUSIVE_READONLY_FORENSIC_ATTEMPT_NOT_FIT_RETRY'
        assert birth['stage']==c.STAGE
        assert birth['generation_manifest_sha256']==self.generation and birth['parent_pid']==self.parent_pid
        assert birth['input_pin_map_sha256']==self.expected_input_map_sha
        assert birth['total_started_monotonic']==self.started and birth['automatic_retry'] is False
        assert identity['parent_pid']==self.parent_pid
        assert identity['birth_sha256']==self.birth_sha and identity['generation_manifest_sha256']==self.generation
        assert identity['prospective_job_limits']==c.JOB_LIMITS and identity['resident_request']==c.RESIDENT_REQUEST
        assert actual['worker_pid']==os.getpid() and actual['parent_pid']==self.parent_pid
        assert actual['birth_sha256']==self.birth_sha and actual['generation_manifest_sha256']==self.generation
        assert actual['owned_child_identity_sha256']==self.identity_sha
        assert actual['exact_parent_owned_Job_membership_checked_before_resume'] is True
        assert actual['job_limits']==c.JOB_LIMITS and actual['resident_cap']['after']['maximum']==c.RESIDENT_REQUEST
        api=headless.original._api();kernel=api.kernel32
        kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=headless.original.HANDLE
        current=kernel.GetCurrentProcess()
        answer=headless.original.BOOL()
        assert api.IsProcessInJob(current,None,C.byref(answer)) and answer.value
        assert working_set.native().query(current)==actual['resident_cap']['after']
        process=headless.process_memory(current)
        assert process['peak_private_commit']<=c.PRIVATE_CAP and process['working_set']<=process['peak_working_set']<=c.RESIDENT_CEILING
        value=headless.memory();assert c.resource_failure(value,time.monotonic()-self.started) is None
        return value

    def descriptor(self):
        self.fresh()
        return {'stage':c.STAGE,'current_pid':os.getpid(),'parent_pid':self.parent_pid,
            'generation_manifest_sha256':self.generation,'birth_sha256':self.birth_sha,
            'owned_child_identity_sha256':self.identity_sha,'in_owned_job_now':True,
            'current_child_record_sha256':self.owner_record_sha,
            'actual_old_campaign_owner_claimed':False}


class Runtime:
    def __init__(self,owner,manifest):
        assert isinstance(owner,CurrentOwner),'Fixed actual-owner type required'
        self.owner,self.manifest=owner,manifest;self.proofs={};owner.fresh()
        from src.generalization_cdrive_numeric_profile_20261025 import runtime
        self.module=runtime
        values=runtime.bootstrap(manifest,owner.fresh)
        self.np,self.pd,self.scipy=values[:3]
        self.threadpoolctl,self.runtime,self.inventory,self.payload=values[5:]
        self._objects=tuple((name,getattr(self,name)) for name in ('np','pd','scipy','threadpoolctl'))
        # The imported optimize/special objects are neither retained nor called.
        del values
        self.first=self.proof()

    def proof(self,key=None):
        if key is not None:assert key not in self.proofs,'No duplicate checkpoint proof or resume'
        assert all(getattr(self,name) is value for name,value in self._objects),'Runtime objects changed'
        self.owner.fresh()
        native=self.module.actual_proof(self.np,self.pd,self.scipy,self.threadpoolctl,self.runtime,self.inventory,self.manifest)
        self.owner.fresh()
        value={**self.owner.descriptor(),'native_origins':native,'checkpoint_key':key,
            'software_certificate_sha256':c.PROFILE_CERTIFICATE_SHA,'forensic_readonly_scope':True,
            'optimizer_calls':0,'historical_campaign_authority_reused':False}
        if key is not None:
            assert key not in self.proofs
            path=c.OUT/('runtime_'+key+'.json')
            self.proofs[key]=c.save_new(path,value)
        return value
