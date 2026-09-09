"""Read-only reconstruction audit; never execute an RBPNet checkpoint."""
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.run_finalshot_direct_models import sha256

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'


def main():
    signature_path = OUT / 'rbp_signature_manifest.json'
    signature = json.loads(signature_path.read_text())
    manifest = json.loads((OUT / 'rbp_feature_matrix_manifest.json').read_text())
    progress = json.loads((ROOT / 'data/interim/finalshot_rbpnet_cache/progress_manifest.json').read_text())
    checkpoints = pd.read_csv(OUT / 'rbpnet_checkpoint_manifest.csv').set_index('task')
    assert signature['checkpoint_count'] == len(checkpoints) == len(progress) == 103
    assert sha256(signature_path) == manifest['signature_manifest_sha256']
    assert sha256(ROOT / manifest['matrix_path']) == manifest['matrix_sha256']
    assert sha256(ROOT / manifest['dictionary_path']) == manifest['dictionary_sha256']
    index = signature['sequence_index']
    assert sha256(ROOT / index['path']) == index['sha256']
    sequences = pd.read_csv(ROOT / index['path'])
    hashes = np.asarray([hashlib.sha256(s.encode()).hexdigest() for s in sequences.sequence], dtype='S64')
    assert np.array_equal(hashes, sequences.sequence_sha256.to_numpy(dtype='S64'))
    lengths = sequences.length.to_numpy()
    assert np.array_equal(lengths, sequences.sequence.str.len().to_numpy())
    assert len(sequences) == 72998 and set(lengths) == {150, 260}
    assert sequences.sequence_sha256.nunique() == len(sequences)
    assert sha256(ROOT / signature['source_interventions']['path']) == signature['source_interventions']['sha256']
    matrix = np.load(ROOT / manifest['matrix_path'], mmap_mode='r')
    assert matrix.shape == (62665, 927) and matrix.dtype == np.float32
    records = []
    for group, item in enumerate(signature['checkpoint_caches']):
        task = item['task']
        assert task == sorted(checkpoints.index)[group]
        assert {k:v for k,v in item.items() if k != 'task'} == progress[task]
        row = checkpoints.loc[task]
        checkpoint = ROOT / 'data/raw/finalshot_resource_audit/RBPNet_models/models' / row.filename
        assert sha256(checkpoint) == row.sha256 == item['checkpoint_sha256']
        assert sha256(ROOT / item['profile_file']) == item['profile_sha256']
        assert sha256(ROOT / item['feature_file']) == item['feature_sha256']
        with np.load(ROOT / item['profile_file'], allow_pickle=False) as archive:
            profile, mixing = archive['target_profile'], archive['mixing']
            assert np.array_equal(archive['sequence_sha256'], hashes)
            assert np.array_equal(archive['lengths'], lengths)
        assert profile.shape == (72998, 260) and mixing.shape == (72998,)
        assert np.isfinite(profile).all() and np.isfinite(mixing).all()
        assert (profile >= 0).all() and ((mixing >= 0) & (mixing <= 1)).all()
        assert np.count_nonzero(profile[lengths == 150, 150:]) == 0
        error = float(np.max(np.abs(profile.sum(axis=1)-1)))
        assert error <= 2e-6
        with np.load(ROOT / item['feature_file'], allow_pickle=False) as archive:
            features = archive['values']
            assert np.array_equal(archive['feature_row'], np.arange(62665))
            assert archive['feature_names'].tolist() == signature['feature_names']
        assert features.shape == (62665, 9) and np.isfinite(features).all()
        assert np.array_equal(features, matrix[:, group*9:(group+1)*9])
        gain_loss = float(np.max(np.abs(features[:,4]-features[:,5])))
        assert gain_loss <= 5e-6
        records.append({'task': task, 'checkpoint_profile_feature_hashes_verified': True,
            'sequence_order_lengths_verified': True, 'matrix_block_bitwise_verified': True,
            'profile_sum_max_error': error, 'gain_loss_max_error': gain_loss})
        if (group+1) % 10 == 0:
            print(f'{group+1}/103 verified', flush=True)
    result = {'status': 'pass', 'checkpoints': len(records), 'unique_sequences': len(sequences),
        'matrix_shape': list(matrix.shape), 'records': records,
        'scope': 'Checkpoint/cache bytes, sequence hashes/order/native lengths, profile/mixing invariants, feature/matrix equality. No new inference or intervention-summary reconstruction.',
        'nzip_outcomes_accessed': False, 'astrocyte_data_accessed': False}
    (OUT / 'reconstruction_reverification_20260909.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('103/103 checkpoints and profile/feature shards verified', flush=True)


if __name__ == '__main__':
    main()
