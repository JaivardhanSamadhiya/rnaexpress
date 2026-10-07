"""Outcome-free local 3UTRBERT resource audit and synthetic CPU benchmark.

No supervised model, biological outcome, or prior inference cache is loaded.
The only network action is explicit retrieval of a public official runtime
wheel, hash checked against authoritative PyPI metadata. Inference uses the
existing FP32 OpenVINO model consistently, rather than mixing old backends.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_next_20261007'
ART, OUT, REP = [ROOT / folder / NS for folder in ('artifacts', 'results', 'reports')]
RUNTIME = ART / 'runtime'
MODEL = ROOT / 'data/external/3utrbert/yangheng-3utrbert'
IR = ROOT / 'data/interim/v4_phaseB_3utrbert_openvino.xml'
CHECKPOINT_SHA = '7aca71823ab74771006be1030d9e7239220bba40a16858575929a02e6d2a7471'
CONTEXT = ROOT / 'artifacts/generalization_20261007/reporter_context_metadata.json'
RUNTIME_VERSION = '2026.3.1'
WHEEL_NAME = 'openvino-2026.3.1-22476-cp312-cp312-win_amd64.whl'
WHEEL_SHA = 'b686302a47abf7c87b48cb265b3a894f787a1b6380f4ab9f5a511de838ba3c64'
TOKENIZER_WHEEL = 'tokenizers-0.19.1-cp312-none-win_amd64.whl'
TOKENIZER_SHA = 'b70bfbe3a82d3e3fb2a5e9b22a39f8d1740c96c68b6ace0086b39074f08ab89a'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path = Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (ART, OUT, REP))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, 'Preserve existing probe artifact: ' + str(path)
    else:
        path.write_bytes(data)


def jsave(path, data):
    save(path, (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())


def bootstrap():
    metadata_url = 'https://pypi.org/pypi/openvino/' + RUNTIME_VERSION + '/json'
    with urllib.request.urlopen(metadata_url, timeout=30) as response:
        metadata_bytes = response.read()
    metadata = json.loads(metadata_bytes)
    match = [entry for entry in metadata['urls'] if entry['filename'] == WHEEL_NAME]
    assert len(match) == 1 and match[0]['digests']['sha256'] == WHEEL_SHA
    entry = match[0]
    assert entry['url'].startswith('https://files.pythonhosted.org/packages/')
    wheel = ART / 'wheels' / WHEEL_NAME
    if not wheel.exists():
        print('Retrieving official public free OpenVINO runtime wheel', entry['size'], 'bytes', flush=True)
        with urllib.request.urlopen(entry['url'], timeout=60) as response:
            content = response.read()
        assert len(content) == entry['size'] and hashlib.sha256(content).hexdigest() == WHEEL_SHA
        save(wheel, content)
    assert digest(wheel) == WHEEL_SHA
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert not any(name.endswith('.pth') for name in names)
        for item in archive.infolist():
            target = (RUNTIME / item.filename).resolve()
            assert target.is_relative_to(RUNTIME.resolve())
            if not item.is_dir():
                save(target, archive.read(item.filename))
        license_names = [name for name in names if 'dist-info' in name and name.upper().endswith('LICENSE')]
        assert license_names and any(b'Apache License' in archive.read(name) for name in license_names)
    jsave(OUT / 'openvino_resource.json', {
        'package': 'openvino', 'version': RUNTIME_VERSION, 'wheel_filename': WHEEL_NAME,
        'wheel_sha256': WHEEL_SHA, 'wheel_bytes': entry['size'], 'wheel_url': entry['url'],
        'metadata_url': metadata_url, 'metadata_sha256': hashlib.sha256(metadata_bytes).hexdigest(),
        'publisher': 'OpenVINO Developers, Intel', 'license': 'Apache-2.0',
        'public_free': True, 'system_install_modified': False,
        'installation': 'hash-verified wheel files extracted to namespace-local runtime only',
        'telemetry_package_installed': False,
    })
    print('Namespace-local OpenVINO runtime prepared', flush=True)


def configure_runtime():
    # Use existing trusted NumPy and tokenizer packages; this leaves old dirs untouched.
    for path in (ROOT / '.python_packages', ROOT / '.transformers_runtime', ROOT / '.tf_runtime',
                 ROOT / 'data/interim/mechanism_v2/runtime', RUNTIME):
        if path.is_dir():
            sys.path.insert(0, str(path))


def bootstrap_tokenizers():
    # Preserve the initial technical failure before repairing the isolated ABI.
    jsave(OUT / 'bert_probe_runtime_incident.json', {
        'stage': 'AutoTokenizer import, before encoder construction and inference',
        'error': "ModuleNotFoundError: No module named 'tokenizers.tokenizers'",
        'cause': 'Existing tokenizers 0.19.1 lacked a CPython 3.12 native extension',
        'biological_inference_performed': False, 'supervised_fitting_performed': False,
        'repair': 'Official CPython 3.12 wheel extracted to new namespace runtime only',
    })
    metadata_url = 'https://pypi.org/pypi/tokenizers/0.19.1/json'
    with urllib.request.urlopen(metadata_url, timeout=30) as response:
        metadata_bytes = response.read()
    metadata = json.loads(metadata_bytes)
    match = [entry for entry in metadata['urls'] if entry['filename'] == TOKENIZER_WHEEL]
    assert len(match) == 1 and match[0]['digests']['sha256'] == TOKENIZER_SHA
    entry = match[0]
    assert entry['url'].startswith('https://files.pythonhosted.org/packages/')
    wheel = ART / 'wheels' / TOKENIZER_WHEEL
    if not wheel.exists():
        print('Retrieving official public free Hugging Face Tokenizers wheel', entry['size'], 'bytes', flush=True)
        with urllib.request.urlopen(entry['url'], timeout=60) as response:
            content = response.read()
        assert len(content) == entry['size'] and hashlib.sha256(content).hexdigest() == TOKENIZER_SHA
        save(wheel, content)
    assert digest(wheel) == TOKENIZER_SHA
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert not any(name.endswith('.pth') for name in names)
        for item in archive.infolist():
            target = (RUNTIME / item.filename).resolve()
            assert target.is_relative_to(RUNTIME.resolve())
            if not item.is_dir():
                save(target, archive.read(item.filename))
        wheel_metadata = archive.read('tokenizers-0.19.1.dist-info/METADATA')
        assert b'License :: OSI Approved :: Apache Software License' in wheel_metadata
    license_url = 'https://raw.githubusercontent.com/huggingface/tokenizers/v0.19.1/LICENSE'
    with urllib.request.urlopen(license_url, timeout=30) as response:
        license_bytes = response.read()
    assert b'Apache License' in license_bytes and b'Version 2.0' in license_bytes
    save(ART / 'resource_licenses' / 'tokenizers_v0.19.1_LICENSE', license_bytes)
    jsave(OUT / 'tokenizers_resource.json', {
        'package': 'tokenizers', 'version': '0.19.1', 'wheel_filename': TOKENIZER_WHEEL,
        'wheel_sha256': TOKENIZER_SHA, 'wheel_bytes': entry['size'], 'wheel_url': entry['url'],
        'metadata_url': metadata_url, 'metadata_sha256': hashlib.sha256(metadata_bytes).hexdigest(),
        'publisher': 'Hugging Face', 'license': 'Apache-2.0', 'public_free': True,
        'license_url': license_url, 'license_sha256': hashlib.sha256(license_bytes).hexdigest(),
        'system_install_modified': False,
        'installation': 'hash-verified wheel files extracted to namespace-local runtime only',
    })
    print('Namespace-local compatible tokenizer prepared', flush=True)


class Encoder:
    def __init__(self, threads=2):
        configure_runtime()
        import numpy as np
        import openvino as ov
        from transformers import AutoTokenizer
        self.np = np
        assert digest(MODEL / 'pytorch_model.bin') == CHECKPOINT_SHA
        self.config = json.loads((MODEL / 'config.json').read_text())
        assert self.config['hidden_size'] == 768 and self.config['max_position_embeddings'] == 512
        self.vocabulary = (MODEL / 'vocab.txt').read_text().splitlines()
        self.ids = {token: index for index, token in enumerate(self.vocabulary)}
        assert len(self.ids) == 69
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=False, use_fast=False)
        self.core = ov.Core()
        self.ov_version = ov.get_version()
        self.available_devices = self.core.available_devices
        assert 'CPU' in self.available_devices
        assert threads in (2, 4)
        self.compiled = self.core.compile_model(self.core.read_model(IR), 'CPU', {
            'INFERENCE_PRECISION_HINT': 'f32', 'INFERENCE_NUM_THREADS': threads,
        })
        # IR attention_mask also has a numeric alias ('29'); get_any_name is
        # unspecified. Resolve only the explicit canonical tokenizer names.
        canonical = {'input_ids', 'attention_mask', 'token_type_ids'}
        self.input_port_aliases = [sorted(port.get_names()) for port in self.compiled.inputs]
        matches = [canonical.intersection(port.get_names()) for port in self.compiled.inputs]
        assert all(len(names) == 1 for names in matches)
        self.parameter_names = [next(iter(names)) for names in matches]
        assert set(self.parameter_names) == {'input_ids', 'attention_mask', 'token_type_ids'}

    def tokenize(self, sequences):
        np = self.np
        normalized = [str(sequence).upper().replace('T', 'U') for sequence in sequences]
        assert all(len(s) >= 3 and len(s) <= 512 and not set(s) - set('ACGU') for s in normalized)
        tokens = [' '.join(s[i:i+3] for i in range(len(s) - 2)) for s in normalized]
        encoded = self.tokenizer(tokens, padding=True, return_tensors='np')
        expected = np.asarray([len(sequence) for sequence in normalized])
        assert np.array_equal(encoded['attention_mask'].sum(1), expected)
        for index, sequence in enumerate(normalized):
            manual = [self.ids['[CLS]']] + [self.ids[sequence[i:i+3]] for i in range(len(sequence) - 2)] + [self.ids['[SEP]']]
            assert encoded['input_ids'][index, :len(manual)].tolist() == manual
        assert not (encoded['input_ids'] == self.ids['[UNK]']).any()
        return {key: np.asarray(encoded[key], dtype=np.int64) for key in self.parameter_names}

    def hidden(self, sequences):
        result = self.compiled(self.tokenize(sequences))[0]
        hidden = self.np.array(result, dtype=self.np.float32, copy=True)
        assert hidden.shape == (len(sequences), max(map(len, sequences)), 768)
        assert self.np.isfinite(hidden).all()
        return hidden

    def paired_features(self, parent, mutant, parent_hidden, mutant_hidden):
        np = self.np
        assert len(parent) == len(mutant)
        positions = [index for index, pair in enumerate(zip(parent, mutant)) if pair[0] != pair[1]]
        assert positions
        starts = sorted({start for position in positions
                         for start in range(max(0, position - 2), min(position, len(parent) - 3) + 1)})
        # CLS is position0; the token for 3-mer start i is at hidden position i+1.
        tokens = np.asarray(starts, dtype=int) + 1
        edit_delta = (mutant_hidden[tokens] - parent_hidden[tokens]).mean(0)
        global_delta = mutant_hidden[1:len(parent)-1].mean(0) - parent_hidden[1:len(parent)-1].mean(0)
        vector = np.r_[global_delta, edit_delta].astype(np.float32)
        assert vector.shape == (1536,) and np.isfinite(vector).all()
        return vector


def synthetic_pairs(np):
    context = json.loads(CONTEXT.read_text())['local_design']
    left, right = context['left_20nt_dna'], context['right_20nt_dna']
    assert len(left) == len(right) == 20 and context['length_nt'] == 46
    rng = np.random.default_rng(20261007)
    result = []
    for index, length in enumerate((46, 46, 46, 46, 150, 150, 190, 190, 260, 260)):
        parent = ''.join(rng.choice(list('ACGT'), length))
        if length == 46:
            parent = left + ''.join(rng.choice(list('ACGT'), 6)) + right
            positions = [20 + index % 6]
        else:
            positions = [length // 2 + index % 3]
        mutant = list(parent)
        for position in positions:
            mutant[position] = 'ACGT'[('ACGT'.index(mutant[position]) + 1) % 4]
        result.append((parent, ''.join(mutant)))
    return result


def benchmark():
    configure_runtime()
    import numpy as np
    started = time.perf_counter()
    encoder = Encoder()
    initialization_seconds = time.perf_counter() - started
    pairs = synthetic_pairs(np)
    sequences = [sequence for pair in pairs for sequence in pair]
    timings, singles = [], []
    for index, sequence in enumerate(sequences):
        started = time.perf_counter()
        hidden = encoder.hidden([sequence])[0]
        seconds = time.perf_counter() - started
        singles.append(hidden)
        timings.append({'allele': index, 'length': len(sequence), 'seconds': seconds})
    mixed = encoder.hidden(sequences)
    errors = [float(np.max(np.abs(hidden - mixed[index, :len(sequence)])))
              for index, (sequence, hidden) in enumerate(zip(sequences, singles))]
    replay = encoder.hidden([sequences[0]])[0]
    replay_error = float(np.max(np.abs(replay - singles[0])))
    vectors, batch_vectors = [], []
    for index, (parent, mutant) in enumerate(pairs):
        vectors.append(encoder.paired_features(parent, mutant, singles[2*index], singles[2*index+1]))
        batch_vectors.append(encoder.paired_features(parent, mutant, mixed[2*index], mixed[2*index+1]))
    vector_error = float(np.max(np.abs(np.asarray(vectors) - np.asarray(batch_vectors))))
    raw = np.asarray(vectors)
    assert np.isfinite(raw).all() and np.all(np.linalg.norm(raw, axis=1) > 0)
    const_types = {}
    for node in ET.parse(IR).getroot().findall('./layers/layer'):
        if node.attrib['type'] == 'Const':
            kind = node.find('data').attrib['element_type']
            const_types[kind] = const_types.get(kind, 0) + 1
    # This is a numerical/backend admission check, fixed before biological extraction.
    padding_pass = bool(all(np.allclose(hidden, mixed[index, :len(sequence)], rtol=2e-5, atol=2e-5)
                            for index, (sequence, hidden) in enumerate(zip(sequences, singles))))
    delta_pass = bool(np.allclose(raw, np.asarray(batch_vectors), rtol=2e-4, atol=2e-5))
    receipt = {
        'status': 'PASS' if padding_pass and delta_pass and replay_error <= 1e-7 else 'FAIL',
        'scope': 'synthetic resource/inference benchmark; no biological outcomes or supervised fitting',
        'synthetic_pairs': 10, 'synthetic_alleles': 20, 'lengths': [46, 150, 190, 260],
        'srle_scope': 'author-certified local 20+6+20 synthesis window, not entire mature RNA',
        'srle_context_metadata_sha256': digest(CONTEXT), 'initialization_seconds': initialization_seconds,
        'backend': 'OpenVINO CPU, f32 inference hint, two threads',
        'openvino_version': encoder.ov_version, 'devices_available': encoder.available_devices,
        'input_port_aliases': encoder.input_port_aliases,
        'checkpoint_sha256': CHECKPOINT_SHA, 'ir_xml_sha256': digest(IR), 'ir_bin_sha256': digest(IR.with_suffix('.bin')),
        'tokenizer_hashes': {name: digest(MODEL/name) for name in ('config.json','vocab.txt','tokenizer_config.json','special_tokens_map.json')},
        'ir_constant_element_types': const_types,
        'torch_cross_backend_equivalence': 'NOT_RETESTED_TORCH_UNAVAILABLE',
        'hidden_batch_padding_max_abs_error': max(errors), 'paired_feature_batch_max_abs_error': vector_error,
        'repeat_hidden_max_abs_error': replay_error, 'padding_pass': padding_pass, 'paired_delta_pass': delta_pass,
        'features': '1536 native dimensions: global nucleotide-token mean allele delta + affected3mer token mean delta',
        'singleton_allele_timings': timings,
        'total_singleton_inference_seconds': sum(row['seconds'] for row in timings),
        'full_core_18220_alleles_seconds_naive_estimate': 18220 * np.mean([row['seconds'] for row in timings]).item(),
    }
    jsave(OUT/'bert_synthetic_benchmark.json', receipt)
    buffer = io.BytesIO(); np.savez_compressed(buffer, features=raw)
    save(ART/'bert_synthetic_features.npz', buffer.getvalue())
    print(json.dumps({key: receipt[key] for key in ('status','initialization_seconds','hidden_batch_padding_max_abs_error',
          'paired_feature_batch_max_abs_error','repeat_hidden_max_abs_error','total_singleton_inference_seconds',
          'full_core_18220_alleles_seconds_naive_estimate')}, indent=2), flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('bootstrap', 'tokenizers', 'benchmark')
    {'bootstrap': bootstrap, 'tokenizers': bootstrap_tokenizers, 'benchmark': benchmark}[sys.argv[1]]()
