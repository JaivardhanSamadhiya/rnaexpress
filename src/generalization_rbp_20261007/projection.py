"""Four fixed label-blind PFM pool projections, shared by raw/accessibility."""
from .common import np, ART, OUT, sha256, save, jsave
from .scoring import FEATURE_POOLS
import io

WIDTH, DIMENSION, SEED = 421, 64, 20261007


def generate():
    rng = np.random.default_rng(SEED)
    return [np.asarray(rng.standard_normal((WIDTH, DIMENSION)) / np.sqrt(DIMENSION), dtype=np.float32)
            for _ in FEATURE_POOLS]


def prepare():
    paths = []
    for pool, matrix in zip(FEATURE_POOLS, generate()):
        path = ART / ("projection_" + pool + ".npy")
        buffer = io.BytesIO(); np.save(buffer, matrix, allow_pickle=False)
        save(path, buffer.getvalue()); paths.append(path)
    jsave(OUT / "projection_receipt.json", {
        "status": "PASS", "seed": SEED, "pool_order": list(FEATURE_POOLS),
        "draw": "Independent Gaussian default float64 in pool order, /sqrt64, then cast float32",
        "shape_per_pool": [WIDTH, DIMENSION], "raw_access_use_same_matrices": True,
        "files": {path.relative_to(ART.parents[1]).as_posix(): sha256(path) for path in paths},
        "outcomes_used": False, "project_features_built": False,
    })
    print("Four fixed421x64 projection matrices saved", flush=True)


def load_projections():
    from .common import ROOT, readj
    receipt = readj(OUT / "projection_receipt.json")
    for name, checksum in receipt["files"].items():
        assert sha256(ROOT / name) == checksum, name
    result = [np.load(ART / ("projection_" + pool + ".npy"), allow_pickle=False) for pool in FEATURE_POOLS]
    for stored, expected in zip(result, generate()):
        assert stored.shape == (WIDTH, DIMENSION) and stored.dtype == np.float32
        np.testing.assert_array_equal(stored, expected)
    return result


def project_pool_summaries(value, matrices):
    """Keep allele summaries float64; final delta alone is cast float32."""
    value = np.asarray(value, dtype=float).reshape(WIDTH, len(FEATURE_POOLS))
    return np.concatenate([value[:, index] @ matrix for index, matrix in enumerate(matrices)])


if __name__ == "__main__":
    prepare()
