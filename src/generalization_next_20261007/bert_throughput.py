"""Synthetic-only fixed batch/thread feasibility check; no labels or fitting."""
from __future__ import annotations

import collections
import ctypes
import gc
import json
import time

from .bert_backend_probe import Encoder, OUT, ROOT, configure_runtime, digest, jsave, synthetic_pairs


def memory_bytes():
    class Counters(ctypes.Structure):
        _fields_ = [('cb',ctypes.c_uint32),('PageFaultCount',ctypes.c_uint32),
                    ('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),
                    ('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_uint32]
    assert psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb)
    return {'rss':counters.WorkingSetSize,'peak_rss':counters.PeakWorkingSetSize}


def run():
    configure_runtime()
    import numpy as np
    import pandas as pd
    pairs = synthetic_pairs(np)
    groups = collections.defaultdict(list)
    for pair in pairs:
        for sequence in pair:
            groups[len(sequence)].append(sequence)
    # Eight alleles per length for equal work at each batch size; duplicate
    # synthetic inputs deterministically where the initial probe had four.
    groups = {length: [seqs[i % len(seqs)] for i in range(8)] for length,seqs in sorted(groups.items())}
    reference = {}
    baseline_encoder = Encoder(2)
    for length,seqs in groups.items():
        reference[length] = [baseline_encoder.hidden([seq])[0] for seq in seqs]
    del baseline_encoder
    gc.collect()
    records = []
    for threads in (2,4):
        started = time.perf_counter()
        encoder = Encoder(threads)
        initialization = time.perf_counter()-started
        for batch_size in (1,4,8):
            record = {'threads':threads,'batch_size':batch_size,'initialization_seconds':initialization,
                      'length_timings':{},'numerical_pass':True,'max_hidden_abs_error':0.0}
            for length,seqs in groups.items():
                encoder.hidden(seqs[:batch_size]) # fixed warm-up, not counted
                elapsed=[]
                for repeat in range(3):
                    started=time.perf_counter()
                    for offset in range(0,len(seqs),batch_size):
                        values=encoder.hidden(seqs[offset:offset+batch_size])
                        for index,hidden in enumerate(values):
                            baseline=reference[length][offset+index]
                            error=float(np.max(np.abs(baseline-hidden)))
                            record['max_hidden_abs_error']=max(record['max_hidden_abs_error'],error)
                            record['numerical_pass'] &= bool(np.allclose(hidden,baseline,rtol=2e-5,atol=2e-5))
                    elapsed.append(time.perf_counter()-started)
                record['length_timings'][str(length)]={'synthetic_alleles':len(seqs),'repeat_seconds':elapsed,
                    'median_seconds_per_allele':float(np.median(elapsed)/len(seqs))}
                record['memory']=memory_bytes()
                print('Synthetic throughput',threads,batch_size,length,record['length_timings'][str(length)]['median_seconds_per_allele'],flush=True)
            records.append(record)
        del encoder
        gc.collect()
    roster = ROOT/'results/probabilistic_ranking_20260928/candidate_index.csv.gz'
    frame = pd.read_csv(roster,usecols=['dataset','parent_sequence','mutant_sequence'])
    metadata = json.loads((ROOT/'artifacts/generalization_20261007/reporter_context_metadata.json').read_text())['local_design']
    left,right=metadata['left_20nt_dna'],metadata['right_20nt_dna']
    alleles=set()
    for row in frame.itertuples(index=False):
        for sequence in (row.parent_sequence,row.mutant_sequence):
            alleles.add(left+sequence+right if row.dataset=='srle' else sequence)
    counts=collections.Counter(map(len,alleles))
    assert len(alleles)==18220 and set(counts)<=set(groups)
    for record in records:
        record['core_inference_seconds_estimate']=sum(count*record['length_timings'][str(length)]['median_seconds_per_allele'] for length,count in counts.items())
    eligible=[record for record in records if record['numerical_pass']]
    assert eligible
    selected=min(eligible,key=lambda record:(record['core_inference_seconds_estimate'],record['threads'],record['batch_size']))
    receipt={'scope':'Synthetic-only batching admission; no supervised fitting or biological inference',
             'status':'PASS','roster_sha256':digest(roster),'unique_core_alleles':len(alleles),
             'unique_alleles_by_length':dict(sorted(counts.items())),'repetitions':3,
             'fixed_admission':'all hidden values allclose to singleton two-thread reference rtol=2e-5 atol=2e-5',
             'settings':records,'selected_threads':selected['threads'],'selected_batch_size':selected['batch_size'],
             'estimated_core_inference_seconds':selected['core_inference_seconds_estimate'],
             'selection':'Lowest estimated inference runtime among numerically admitted settings, fixed ties by threads then batch',
             'estimate_limitations':'Synthetic CPU estimate excludes biological row assembly, checkpoint initialization, IO, and concurrent-load changes; add 20% planning margin'}
    jsave(OUT/'bert_synthetic_throughput.json',receipt)
    print(json.dumps({key:receipt[key] for key in ('status','unique_alleles_by_length','selected_threads','selected_batch_size','estimated_core_inference_seconds')},indent=2),flush=True)


if __name__=='__main__':
    run()
