"""Actual frozen PFMs/projections on synthetic alleles; no project inputs."""
import time
from .common import *
from .feasibility import benchmark_sequences, ALLELE_COUNTS
from .production import score
from .runtime import check as runtime_check
from src.generalization_rbp_20261007.projection import load_projections

def run():
    runtime_check(); matrices = load_projections(); records = []
    for length, index, sequence in benchmark_sequences():
        sequence = sequence.replace('U', 'T')
        # Synthetic requests test reuse of one fold across distinct edit-site sets.
        requested = [(i,) for i in range(16)]
        start = time.perf_counter(); global_value, local = score(sequence, requested, matrices)
        records.append({'length': length, 'synthetic_index': index, 'requests': 16,
            'elapsed_seconds': time.perf_counter() - start, 'projected_output_bytes': global_value.nbytes + local.nbytes})
    medians = {str(length): float(np.median([row['elapsed_seconds'] for row in records if row['length'] == length])) for length in ALLELE_COUNTS}
    estimate = sum(ALLELE_COUNTS[length] * medians[str(length)] for length in ALLELE_COUNTS)
    jsave(OUT / 'synthetic_pool_benchmark_receipt.json', {'status': 'PASS', 'records': records, 'median_seconds_by_length': medians,
        '18220_synthetic_16_request_per_allele_fold_scan_pool_projection_estimate_seconds': estimate,
        'planning_margin_50_percent_seconds': estimate * 1.5, 'runtime_binding_sha256': sha256(OUT / 'runtime_binding_receipt.json'),
        'actual_project_alleles_read': False, 'project_outcomes_read': False, 'fits': 0,
        'excludes': ['cache write/hash/read', 'row assembly', 'actual request-count variation', 'concurrent CPU/memory load'],
        'not_a_timing_guarantee': True})
    print(json.dumps({'status': 'PASS', 'median_seconds': medians, 'estimate_minutes': estimate / 60, 'with_margin_minutes': estimate * 1.5 / 60}), flush=True)

if __name__ == '__main__':
    run()
