"""Synthetic-only native benchmark entrypoint; no file reader for project data."""
import sys
import time
import traceback
from . import common as c, kernels as k, spec as s, guard

def check_numerics(np, optimizer, started):
    checks = []
    x, y, b = k.invented(22, 6, 1)
    contexts = [{'name': 'small-a', 'indices': list(range(12)), 'mass': .25},
                {'name': 'small-b', 'indices': list(range(12, 19)), 'mass': .75},
                {'name': 'small-tied', 'indices': list(range(19, 22)), 'mass': .6}]
    y[19:] = [2., 2., 2.]
    prepared = k.prepare_contexts(y, contexts, np=np)
    assert len(prepared) == 2 and [r['mass'] for r in prepared] == [.25, .75]
    z, mean, scale, active = k.transformed(np, x, prepared, original_contexts=contexts); beta = np.asarray(b)[active]
    assert not active[-1] and scale[-1] == 1.
    raw = np.asarray(x, dtype=float); pairs = [edge for row in prepared for edge in row['cap']]
    left, right = np.asarray(pairs, dtype=int).T
    pw = np.asarray([row['mass']/len(row['cap']) for row in prepared for _ in row['cap']])
    rms = np.sqrt((pw[:, None]*(raw[left]-raw[right])**2).sum(axis=0)/pw.sum())
    expected_active = rms >= 1e-8; rms[~expected_active] = 1.
    assert np.array_equal(active, expected_active) and np.max(np.abs(scale-rms)) <= s.GRADIENT_ABS_BOUND
    candidate_weights = np.asarray([next(row['mass']/len(row['indices']) for row in contexts if i in row['indices']) for i in range(len(y))])
    expected_mean = (raw*candidate_weights[:, None]).sum(axis=0)/candidate_weights.sum()
    assert np.max(np.abs(mean-expected_mean)) <= s.GRADIENT_ABS_BOUND
    checks.append({'fixed_source_cap_RMS_support_error': float(np.max(np.abs(scale-rms))),
                   'all_original_candidate_mean_error': float(np.max(np.abs(mean-expected_mean))), 'empty_cap_context_not_revived': True})
    for mode in ('cap', 'all'):
        risk, gradient = k.objective(np, z, beta, y, prepared, mode)
        rr, rg = k.materialized(np, z, beta, y, prepared, mode)
        error = max(abs(risk - rr), float(np.abs(gradient - rg).max()))
        assert error <= s.GRADIENT_ABS_BOUND
        fd_error = 0.
        for j in range(len(beta)):
            lo, hi = beta.copy(), beta.copy(); lo[j] -= 1e-6; hi[j] += 1e-6
            fd = (k.objective(np, z, hi, y, prepared, mode)[0] - k.objective(np, z, lo, y, prepared, mode)[0]) / 2e-6
            fd_error = max(fd_error, abs(fd - gradient[j]))
        assert fd_error <= s.FINITE_DIFFERENCE_BOUND
        checks.append({'mode': mode, 'materialized_max_abs_error': error, 'finite_difference_max_abs_error': fd_error})
    # Exact signed-zero ties, large margins and parent offsets are semantic controls.
    extreme_z = np.asarray([[500.],[-500.]])
    extreme_prepared = k.prepare_contexts([1.,0.], [{'name':'extreme','indices':[0,1],'mass':1.}], np=np)
    for beta_value in (-1.,1.):
        aa = k.objective(np, extreme_z, np.asarray([beta_value]), [1.,0.], extreme_prepared, 'all')
        bb = k.materialized(np, extreme_z, np.asarray([beta_value]), [1.,0.], extreme_prepared, 'all')
        assert abs(aa[0]-bb[0]) <= s.GRADIENT_ABS_BOUND and np.max(np.abs(aa[1]-bb[1])) <= s.GRADIENT_ABS_BOUND
    shifted = z.copy()
    for row in prepared: shifted[row['indices']] += 3.5 if row['name']=='small-a' else -2.25
    aa = k.objective(np,z,beta,y,prepared,'all'); bb=k.objective(np,shifted,beta,y,prepared,'all')
    assert abs(aa[0]-bb[0])<=s.GRADIENT_ABS_BOUND and np.max(np.abs(aa[1]-bb[1]))<=s.GRADIENT_ABS_BOUND
    assert k.non_tied_count([0.,-0.,1.,1.])==4
    checks.append({'large_margin_finite': True, 'signed_zero_exact_ties': True, 'parent_shift_max_abs_error': float(np.max(np.abs(aa[1]-bb[1])))})
    # A separate >23 menu exercises an incomplete cap and full upper triangle.
    x, y, b = k.invented(*s.SMALL_OPTIMIZER_SHAPE, 2)
    p = k.prepare_contexts(y, [{'name': 'optimizer-invented', 'indices': list(range(len(y))), 'mass': 1.}], np=np)
    z, _, _, active = k.transformed(np, x, p); zero = np.zeros(int(active.sum()))
    for mode in ('cap', 'all'):
        aa = optimizer.minimize(lambda beta: k.objective(np, z, beta, y, p, mode), zero.copy(), jac=True, method='L-BFGS-B', options=s.OPTIMIZER_OPTIONS)
        guard.time_contract(time.perf_counter()-started)
        bb = optimizer.minimize(lambda beta: k.materialized(np, z, beta, y, p, mode), zero.copy(), jac=True, method='L-BFGS-B', options=s.OPTIMIZER_OPTIONS)
        guard.time_contract(time.perf_counter()-started)
        coefficient_error = float(np.abs(aa.x - bb.x).max()); risk_error = abs(float(aa.fun - bb.fun))
        assert aa.success and bb.success and coefficient_error <= s.OPTIMIZER_COEFFICIENT_BOUND and risk_error <= s.OPTIMIZER_RISK_BOUND
        checks.append({'mode': mode, 'invented_optimizer_only': True, 'candidate_status': int(aa.status), 'reference_status': int(bb.status),
                       'coefficient_max_abs_error': coefficient_error, 'risk_abs_error': risk_error, 'iterations': [int(aa.nit), int(bb.nit)]})
    return checks

def completed_call(n,p,mode,phase,duration,risk,gradient,np,started):
    """Retain a completed call BEFORE refusing a late/time/memory result."""
    elapsed=time.perf_counter()-started;mem=guard.memory()
    c.jsave(c.OUT/('case_n'+str(n)+'_p'+str(p)+'_'+mode+'_'+phase+'.json'),
            {'n':n,'dimensions_before_support':p,'mode':mode,'phase':phase,'seconds':duration,
             'numeric_elapsed_seconds':elapsed,'risk':risk,'gradient_norm':float(np.linalg.norm(gradient)),
             'memory':mem,'passes_time_bound':elapsed<=s.MAX_PROBE_SECONDS,
             'passes_memory_bound':mem['peak_working_set_bytes']<=s.MAX_WORKING_SET})
    guard.time_contract(time.perf_counter()-started)
    assert mem['peak_working_set_bytes']<=s.MAX_WORKING_SET,'Peak >400MiB; stop'

def benchmark(np, started):
    rows = []
    for n in s.SIZES:
        for p in s.WIDTHS:
            guard.resource_contract(guard.resources())
            guard.time_contract(time.perf_counter()-started)
            x, y, b = k.invented(n, p, 3); prepared = k.prepare_contexts(y, [{'name': 'large-' + str(n), 'indices': list(range(n)), 'mass': 1.}], np=np)
            z, mean, scale, active = k.transformed(np, x, prepared); del x; beta = np.asarray(b)[active]
            assert len(prepared[0]['cap']) <= s.CAP and not active[-1]
            row = {'n': n, 'dimensions_before_support': p, 'dimensions_supported': int(active.sum()),
                   'valid_cap_pairs': len(prepared[0]['cap']), 'all_non_tied_pairs': prepared[0]['all_count'], 'matrix_bytes': int(z.nbytes),
                   'mean_sha256': c.hashlib.sha256(mean.astype('<f8').tobytes()).hexdigest(),
                   'same_cap_RMS_for_both_arms_sha256': c.hashlib.sha256(scale.astype('<f8').tobytes()).hexdigest(), 'timings': {}}
            for mode in ('cap', 'all'):
                begin=time.perf_counter();risk,gradient=k.objective(np,z,beta,y,prepared,mode) # Exactly one fixed warmup.
                completed_call(n,p,mode,'warmup',time.perf_counter()-begin,risk,gradient,np,started)
                elapsed = []
                for repeat in range(s.REPEATS):
                    begin = time.perf_counter(); risk, gradient = k.objective(np, z, beta, y, prepared, mode); duration=time.perf_counter()-begin;elapsed.append(duration)
                    completed_call(n,p,mode,'repeat'+str(repeat),duration,risk,gradient,np,started)
                row['timings'][mode] = {'seconds': elapsed, 'median_seconds': sorted(elapsed)[len(elapsed)//2], 'risk': risk, 'gradient_norm': float(np.linalg.norm(gradient))}
                mem = guard.memory(); assert mem['peak_working_set_bytes'] <= s.MAX_WORKING_SET, 'Peak >400MiB; stop'
            row['memory_after'] = mem; rows.append(row)
            c.jsave(c.OUT / ('case_n' + str(n) + '_p' + str(p) + '.json'), row)
            guard.time_contract(time.perf_counter()-started)
            print('Invented pair benchmark case', n, p, 'cap', row['timings']['cap']['median_seconds'], 'all', row['timings']['all']['median_seconds'], flush=True)
            del z, beta
    return rows

def run(root_start=False):
    assert root_start, 'Root explicit native synthetic start required'
    c.freshness()
    try:
        np, optimizer, runtime, manifest = guard.admit(root_start)
        started = time.perf_counter(); checks = check_numerics(np, optimizer,started)
        guard.time_contract(time.perf_counter()-started)
        cases = benchmark(np, started)
        from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
        origins = guard.actual_origins(runtime, launcher.process_native_paths())
        c.manifest_checks(manifest)
        receipt={'status': 'PASS_INVENTED_NATIVE_FEASIBILITY_ONLY', 'small_checks': checks, 'cases': cases,
            'final_origins': origins,
            'preparation_manifest_sha256': c.sha(c.MANIFEST), 'import_receipt_sha256': c.sha(c.OUT/'current_runtime_import_receipt.json'),
            'case_receipts_sha256': {p.relative_to(c.ROOT).as_posix():c.sha(p) for p in sorted(c.OUT.glob('case_n*_p*.json'))},
            'project_sequences_labels_features_models_read': False, 'biological_fits': 0, 'invented_optimizer_calls': 4,
            'tractability_implies_generalization': False, 'production_admission_authorized': False}
        receipt['final_memory']=guard.memory();assert receipt['final_memory']['peak_working_set_bytes']<=s.MAX_WORKING_SET
        receipt['native_numeric_elapsed_seconds']=guard.time_contract(time.perf_counter()-started)
        c.jsave(c.OUT / 'native_receipt.json',receipt)
        print('Invented native all-pair feasibility PASS', c.sha(c.OUT/'native_receipt.json'), flush=True)
    except Exception:
        c.jsave(c.OUT / 'native_attempt_incident.json', {'status':'PRESERVED_NATIVE_ATTEMPT_FAILURE_NO_AUTOMATIC_RETRY', 'traceback':traceback.format_exc(),
                'project_data_reads':0, 'biological_fits':0})
        raise

if __name__ == '__main__': run('--root-start' in sys.argv[1:])
