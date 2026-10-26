"""Real new-stage owner. Old forensic or historical owner claims are rejected."""
import ctypes as C
import os
import time
from . import common as c
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_owned_workingset_probe_v2_20261025 import working_set


class Owner:
    def __init__(self,stage,generation,run_sha,birth_sha,identity_sha,parent_pid,started):
        self.stage,self.generation,self.run_sha=stage,generation,run_sha
        self.birth_sha,self.identity_sha=birth_sha,identity_sha
        # Parent captured this record before first resume. Its exact hash is
        # independently compared to this child's captured hash at acceptance.
        self.owner_sha=c.sha(stage.path('owned_child_started.json'))
        self.parent_pid,self.started=parent_pid,started
        self.closed=False;self.fresh()

    def fresh(self):
        assert not self.closed;c.source_mode();assert os.getppid()==self.parent_pid
        auth_raw,_=c.authorization(self.generation)
        run_raw=self.stage.path('run_admission.json').read_bytes();assert c.digest(run_raw)==self.run_sha
        run=c.decode(run_raw);assert run['new_manual_authorization_sha256']==c.digest(auth_raw)
        birth_raw=self.stage.path('attempt_birth.json').read_bytes();assert c.digest(birth_raw)==self.birth_sha
        identity_raw=self.stage.path('owned_child_identity.json').read_bytes();assert c.digest(identity_raw)==self.identity_sha
        owner_raw=self.stage.path('owned_child_started.json').read_bytes();assert c.digest(owner_raw)==self.owner_sha
        birth,identity,actual=map(c.decode,(birth_raw,identity_raw,owner_raw))
        assert birth['status']=='NEW_MANUALLY_AUTHORIZED_CURRENT_STUDY_STAGE_NOT_OLD_RETRY'
        assert birth['stage']==self.stage.name and birth['source_manifest_sha256']==self.generation
        assert birth['run_admission_sha256']==self.run_sha and birth['parent_pid']==self.parent_pid
        assert birth['started_monotonic']==self.started and birth['automatic_retry'] is False
        assert identity['birth_sha256']==actual['birth_sha256']==self.birth_sha
        assert identity['parent_pid']==actual['parent_pid']==self.parent_pid
        assert identity['source_manifest_sha256']==actual['source_manifest_sha256']==self.generation
        assert actual['owned_child_identity_sha256']==self.identity_sha and actual['worker_pid']==os.getpid()
        assert identity['job_limits']==actual['job_limits']==c.CAPS
        assert actual['exact_parent_owned_membership_checked_before_resume'] is True
        assert actual['resident_cap']['after']['maximum']==c.RESIDENT
        api=headless.original._api();kernel=api.kernel32
        kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=headless.original.HANDLE
        process=kernel.GetCurrentProcess();answer=headless.original.BOOL()
        assert api.IsProcessInJob(process,None,C.byref(answer)) and answer.value
        assert working_set.native().query(process)==actual['resident_cap']['after']
        counters=headless.process_memory(process)
        assert counters['peak_private_commit']<=c.PRIVATE
        assert counters['working_set']<=counters['peak_working_set']<=c.CEILING
        state=headless.memory();assert c.resource_failure(state,time.monotonic()-self.started) is None
        return state

    def descriptor(self):
        self.fresh()
        return {'stage':self.stage.name,'parent_pid':self.parent_pid,'worker_pid':os.getpid(),
            'source_manifest_sha256':self.generation,'run_admission_sha256':self.run_sha,
            'birth_sha256':self.birth_sha,'owned_child_identity_sha256':self.identity_sha,
            'current_child_record_sha256':self.owner_sha,'actual_in_owned_job_now':True,
            'old_or_forensic_stage_authority_reused':False}


class Runtime:
    def __init__(self,owner,manifest):
        from src.generalization_cdrive_numeric_profile_20261025 import runtime
        self.owner,self.manifest,self.module=owner,manifest,runtime
        values=runtime.bootstrap(manifest,owner.fresh)
        self.np,self.pd,self.scipy,self.minimize,self.expit,self.threadpoolctl,self.runtime,self.inventory,self.payload=values
        self.proofs={};self.before=self.proof()

    def proof(self,key=None):
        self.owner.fresh()
        assert self.scipy.optimize.minimize is self.minimize and self.scipy.special.expit is self.expit
        native=self.module.actual_proof(self.np,self.pd,self.scipy,self.threadpoolctl,self.runtime,self.inventory,self.manifest)
        self.owner.fresh()
        value={**self.owner.descriptor(),'actual_current_native_origins':native,
            'actual_minimize_module':self.minimize.__module__,'checkpoint_key':key}
        if key is not None:
            assert key not in self.proofs
            self.proofs[key]=c.save_new(self.owner.stage.path('runtime_'+key+'.json'),value)
        return value
