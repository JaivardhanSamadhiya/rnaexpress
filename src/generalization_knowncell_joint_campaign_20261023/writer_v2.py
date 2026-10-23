"""Prospective fail-closed wrapper; the original 50-pin layer stays unchanged."""
from . import writer as original
from .contracts import digest


class Campaign(original.Campaign):
    """Check run birth before a checkpoint and poison on ANY attempted failure.

    In particular, the original exclusive birth write/fsync is outside its
    internal try block. This outer wrapper covers that entire call. A failed
    attempt can never be repaired/resumed on this object or its existing path.
    """
    def write_checkpoint(self,key,optimizer_callback,selection=None):
        try:
            assert not self.failed,'Campaign already failed; no resume'
            assert digest((self.directory/'campaign_birth.json').read_bytes())==self.run_birth_sha, 'Campaign birth changed before callback'
            return super().write_checkpoint(key,optimizer_callback,selection)
        except BaseException as error:
            self.failed=True
            # The old failure record, if present, is retained. This separate
            # run-level evidence also covers pre-birth and partial-write errors.
            path=self.directory/'campaign_failure_v2.json'
            if not path.exists():
                try:
                    original.write_new(path,{'status':'FAILED_V2_NO_RESUME',
                        'task_key':str(key),'error_type':type(error).__name__,
                        'error':str(error),'campaign_birth_sha256_at_creation':self.run_birth_sha,
                        'partial_outputs_retained':True,'scientific_or_gate_claim':False})
                except BaseException as record_error:
                    # Evidence can fail on the same full disk/fsync condition.
                    # Poisoning is unconditional and the original failure is
                    # re-raised with the logging failure visible to its owner.
                    error.add_note('Could not save v2 failure evidence: '+type(record_error).__name__+': '+str(record_error))
            raise
