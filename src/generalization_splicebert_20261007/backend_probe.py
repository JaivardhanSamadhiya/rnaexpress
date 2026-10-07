"""Root-start/resource-guarded synthetic-only restricted BERT conversion.

Importing this module uses the standard library only. No project allele,
outcome, historical embedding cache or unreviewed remote model code is read.
"""
from __future__ import annotations
from collections import OrderedDict
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

from .resources import ROOT, ART, OUT, MODEL, digest, jsave, resource_state

IR = ART / "backend/splicebert_1024_fp32.xml"
PROTOCOL = ROOT / "reports/generalization_splicebert_20261007/backend_preparation_plan.md"
TEST_RECEIPT = OUT / "backend_preparation_tests_receipt_final.json"
TEST_SOURCE = Path(__file__).with_name("test_backend_preparation.py")
INPUT_NAMES = ("input_ids", "attention_mask", "token_type_ids")
TOKEN_IDS = {"A": 6, "C": 7, "G": 8, "T": 9}
CHECKPOINT_SHA = "2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d"


def tokenize_lists(sequences):
    assert sequences and all(sequence and set(sequence) <= set(TOKEN_IDS) for sequence in sequences)
    length = max(map(len, sequences)) + 2
    assert length <= 1026
    ids, masks, types = [], [], []
    for sequence in sequences:
        tokens = [2] + [TOKEN_IDS[base] for base in sequence] + [3]
        count = len(tokens)
        ids.append(tokens + [0] * (length - count))
        masks.append([1] * count + [0] * (length - count))
        types.append([0] * length)
    return dict(zip(INPUT_NAMES, (ids, masks, types)))


def synthetic_sequences(left, right):
    assert len(left) == len(right) == 20 and set(left + right) <= set(TOKEN_IDS)
    result = []
    for length in (46, 150, 190, 260):
        for replicate in range(2):
            seed = ("splicebert_backend_20261007:" + str(length) + ":" + str(replicate)).encode()
            core_length = 6 if length == 46 else length
            # Hash-generated synthetic DNA is fixed, outcome-free and independent
            # of model features; there is no downloaded project-allele lookup.
            dna = "".join("ACGT"[hashlib.sha256(seed + index.to_bytes(4, "little")).digest()[0] % 4]
                          for index in range(core_length))
            parent = left + dna + right if length == 46 else dna
            position = 23 if length == 46 else length // 2
            mutant = parent[:position] + "ACGT"[("ACGT".index(parent[position]) + 1) % 4] + parent[position + 1:]
            result.extend((parent, mutant))
    assert len(result) == len(set(result)) == 16
    return result


def check_files(receipt_path):
    receipt = json.loads(Path(receipt_path).read_text())
    assert receipt["status"] == "PASS"
    runtime = (ROOT / receipt["runtime_path"]).resolve()
    assert runtime.is_relative_to(ROOT)
    actual = {path.relative_to(runtime).as_posix() for path in runtime.rglob("*") if path.is_file()}
    assert actual == set(receipt["files"]), "Isolated runtime acquired unexpected files"
    for name, expected in receipt["files"].items():
        assert digest(runtime / name) == expected, name
    return runtime


def check_committed(path):
    value = subprocess.check_output(["git", "show", "HEAD:" + Path(path).relative_to(ROOT).as_posix()], cwd=ROOT)
    assert value == Path(path).read_bytes(), "Commit backend preparation before root start"


def guard(root_start=False):
    assert root_start, "Root must explicitly start conversion/synthetic inference"
    state = resource_state()
    assert state["resource_admission_now"], "Require fresh3GiB freeRAM/5GiB disk before model work"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == os.environ.get("OMP_NUM_THREADS") == "2"
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    manifest_path = OUT / "backend_preparation_manifest.json"
    check_committed(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "FROZEN_SYNTHETIC_BACKEND_PREPARATION_ONLY"
    for name, expected in manifest["files"].items():
        assert digest(ROOT / name) == expected, name
    for path in (Path(__file__), TEST_SOURCE, PROTOCOL, TEST_RECEIPT):
        check_committed(path)
    tests = json.loads(TEST_RECEIPT.read_text())
    assert tests["status"] == "PASS" and tests["backend_probe_sha256"] == digest(__file__)
    assert tests["test_source_sha256"] == digest(TEST_SOURCE)
    audit = json.loads((OUT / "resource_audit.json").read_text())
    assert audit["status"] == "PASS" and audit["author_archive_identity"].startswith("All selected")
    for name, record in audit["cached_files"].items():
        assert digest(MODEL / name) == record["sha256"]
    assert digest(MODEL / "pytorch_model.bin") == CHECKPOINT_SHA
    assert not IR.exists() and not IR.with_suffix(".bin").exists(), "Preserve backend candidate/cache"
    assert not (OUT / "backend_synthetic_receipt.json").exists(), "Preserve completed synthetic probe"
    torch_runtime = check_files(OUT / "cpu_runtime_extraction_receipt.json")
    dependencies = check_files(OUT / "dependency_runtime_receipt.json")
    ov_receipt_path = ROOT / "results/generalization_next_20261007/bert_runtime_integrity.json"
    ov_receipt = json.loads(ov_receipt_path.read_text())
    ov_runtime = ROOT / "artifacts/generalization_next_20261007/runtime"
    assert {path.relative_to(ROOT).as_posix() for path in ov_runtime.rglob("*") if path.is_file()} == set(ov_receipt["files"])
    for name, expected in ov_receipt["files"].items():
        assert (ROOT / name).resolve().is_relative_to(ov_runtime.resolve())
        assert digest(ROOT / name) == expected, name
    reused = json.loads((OUT / "reused_runtime_receipt.json").read_text())
    assert reused["status"] == "PASS"
    for name, expected in reused["files"].items():
        assert digest(Path(name)) == expected, name
    # No addsitedir/pip installation or .pth execution. Fixed inspected local
    # Transformers4.40.2 takes priority over the broader workspace package set.
    paths = (dependencies, torch_runtime, ov_runtime, ROOT / ".transformers_runtime", ROOT / ".python_packages")
    for path in reversed(paths):
        sys.path.insert(0, str(path))
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        os.environ[name] = "1"
    state = resource_state()
    assert state["resource_admission_now"], "RAM changed while checking resources; defer import"
    return state


def run(root_start=False):
    headroom = guard(root_start)
    import numpy as np
    import torch
    import openvino as ov
    from transformers import BertConfig, BertModel, BertTokenizer
    assert torch.__version__ == "2.6.0+cpu"
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    started = time.perf_counter()
    config = BertConfig.from_json_file(str(MODEL / "config.json"))
    assert config.hidden_size == 512 and config.num_hidden_layers == 6 and config.vocab_size == 10
    config.output_hidden_states = False
    model = BertModel(config, add_pooling_layer=False).float().eval()
    # Restricted loading only; no safe-global additions or unsafe fallback.
    checkpoint = torch.load(MODEL / "pytorch_model.bin", map_location="cpu", weights_only=True,
                            mmap=zipfile.is_zipfile(MODEL / "pytorch_model.bin"))
    assert isinstance(checkpoint, (dict, OrderedDict)) and checkpoint
    assert all(isinstance(key, str) and isinstance(value, torch.Tensor) for key, value in checkpoint.items())
    state = {key[5:]: value for key, value in checkpoint.items() if key.startswith("bert.")}
    unused = sorted(key for key in checkpoint if not key.startswith("bert."))
    assert all(key.startswith("cls.") for key in unused), "Unexpected non-encoder checkpoint entries"
    deterministic_buffers = []
    for key in ("embeddings.position_ids", "embeddings.token_type_ids"):
        if key in state and key not in model.state_dict():
            expected = (torch.arange(config.max_position_embeddings).reshape(1, -1)
                        if key.endswith("position_ids") else torch.zeros((1, config.max_position_embeddings), dtype=torch.long))
            assert torch.equal(state[key], expected), "Noncanonical old deterministic token buffer"
            state.pop(key); deterministic_buffers.append(key)
    model.load_state_dict(state, strict=True)
    assert all(torch.isfinite(value).all() for value in model.parameters())
    del checkpoint, state; gc.collect()
    context_path = ROOT / "artifacts/generalization_20261007/reporter_context_metadata.json"
    assert digest(context_path) == "e7ee4fea706d3b7e611f63d491304cfe835efcd3c9b6a9a4f0282abf384f725c"
    design = json.loads(context_path.read_text())["local_design"]
    sequences = synthetic_sequences(design["left_20nt_dna"], design["right_20nt_dna"])
    tokenizer = BertTokenizer.from_pretrained(MODEL, local_files_only=True)
    example_lists = tokenize_lists(sequences[:2])
    authored = tokenizer([" ".join(sequence) for sequence in sequences[:2]], padding=True)
    assert all(authored[name] == example_lists[name] for name in INPUT_NAMES)

    class BertWrapper(torch.nn.Module):
        def __init__(self, encoder):
            super().__init__(); self.encoder = encoder
        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.encoder(input_ids=input_ids, attention_mask=attention_mask,
                                token_type_ids=token_type_ids, return_dict=False)[0]

    wrapper = BertWrapper(model).eval()
    example = tuple(torch.tensor(example_lists[name], dtype=torch.long) for name in INPUT_NAMES)
    converted = ov.convert_model(wrapper, example_input=example,
                                 input=[ov.PartialShape([-1, -1])] * 3)
    assert len(converted.inputs) == 3 and len(converted.outputs) == 1
    for port, name in zip(converted.inputs, INPUT_NAMES):
        port.get_tensor().set_names({name})
    IR.parent.mkdir(parents=True, exist_ok=True)
    ov.save_model(converted, IR, compress_to_fp16=False)
    core = ov.Core()
    compiled = core.compile_model(converted, "CPU", {"INFERENCE_NUM_THREADS": 2,
        "INFERENCE_PRECISION_HINT": "f32", "NUM_STREAMS": 1})
    errors, reference_time, ov_time = [], 0., 0.
    for first in range(0, len(sequences), 2):
        batch = sequences[first:first + 2]
        encoded = tokenize_lists(batch)
        native = tuple(torch.tensor(encoded[name], dtype=torch.long) for name in INPUT_NAMES)
        began = time.perf_counter()
        with torch.inference_mode():
            reference = wrapper(*native).numpy()
        reference_time += time.perf_counter() - began
        began = time.perf_counter()
        actual = np.asarray(compiled({name: np.asarray(encoded[name], dtype=np.int64) for name in INPUT_NAMES})[0])
        ov_time += time.perf_counter() - began
        assert actual.shape == reference.shape == (2, len(batch[0]) + 2, 512)
        assert np.isfinite(actual).all() and np.isfinite(reference).all()
        difference = np.abs(actual - reference)
        cosine = np.sum(actual * reference, axis=-1) / (np.linalg.norm(actual, axis=-1) * np.linalg.norm(reference, axis=-1))
        checks = {"maximum_hidden_difference_at_most_0_001": float(difference.max()) <= .001,
                  "mean_hidden_difference_at_most_0_0001": float(difference.mean()) <= .0001,
                  "minimum_token_cosine_at_least_0_999999": float(cosine.min()) >= .999999}
        assert all(checks.values()), "Synthetic CPU Torch/OpenVINO mismatch; retain uncertified candidate IR"
        errors.append({"length_nt": len(batch[0]), "maximum_hidden_absolute_difference": float(difference.max()),
                       "mean_hidden_absolute_difference": float(difference.mean()),
                       "minimum_token_cosine": float(cosine.min()), "checks": checks})
        print("SpliceBERT synthetic native/IR", len(batch[0]), "nt PASS", flush=True)
    jsave(OUT / "backend_synthetic_receipt.json", {
        "status": "PASS", "scope": "SYNTHETIC_CPU_BACKEND_ADMISSION_ONLY",
        "torch_version": torch.__version__, "openvino_version": ov.get_version(),
        "checkpoint_sha256": CHECKPOINT_SHA, "load": "weights_only=True,map_location=cpu; mmap for ZIP only; strict encoder state",
        "unused_MLM_head_keys": unused, "validated_legacy_deterministic_buffers": deterministic_buffers,
        "IR_xml_sha256": digest(IR), "IR_bin_sha256": digest(IR.with_suffix(".bin")),
        "synthetic_alleles": len(sequences), "synthetic_sequence_sha256": [hashlib.sha256(s.encode()).hexdigest() for s in sequences],
        "comparisons": errors, "headroom_before_import": headroom,
        "CPU_threads": 2, "torch_inference_seconds": reference_time, "OpenVINO_inference_seconds": ov_time,
        "total_seconds": time.perf_counter() - started, "project_alleles_inferred": 0,
        "outcomes_used": False, "models_fit": 0, "SRLE46nt_outside_author_recommended_training_length": True,
        "full_production_authorized": False})


if __name__ == "__main__":
    assert sys.argv[1:] == ["--root-start"]
    run(root_start=True)
