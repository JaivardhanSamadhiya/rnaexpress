"""Hash inspected existing runtime sources without executing those packages."""
from pathlib import Path
import sys
from .resources import ROOT, OUT, digest, jsave

PACKAGES = ("filelock", "fsspec", "typing_extensions", "packaging", "huggingface_hub",
            "numpy", "regex", "requests", "yaml", "_yaml", "tqdm", "safetensors",
            "certifi", "charset_normalizer", "idna", "urllib3", "colorama")


def run():
    package_root = ROOT / ".python_packages"
    paths = [ROOT / ".transformers_runtime/transformers", ROOT / ".transformers_runtime/transformers-4.40.2.dist-info"]
    for name in PACKAGES:
        candidates = [path for path in package_root.glob(name + "*")
                      if path.name == name or path.name == name + ".py" or path.name == name + ".libs"
                      or path.name.startswith(name + "-") and path.name.endswith(".dist-info")]
        assert candidates, name
        paths.extend(candidates)
    site = Path(sys.executable).parent / "Lib/site-packages"
    paths.extend([site / "setuptools", site / "setuptools-84.0.0.dist-info", site / "_distutils_hack"])
    files = {}
    for path in paths:
        assert path.exists(), str(path)
        for member in ([path] if path.is_file() else sorted(path.rglob("*"))):
            if member.is_file():
                files[str(member.resolve())] = digest(member)
    jsave(OUT / "reused_runtime_receipt.json", {"status": "PASS", "scope": "OUTCOME_FREE_LOCAL_SOURCE_SNAPSHOT_NOT_ORIGINAL_WHEEL_PARITY",
          "files": files, "sources": [str(path.resolve()) for path in paths],
          "packages_imported": False, "model_loaded": False, "system_install_modified": False,
          "limitation": "Existing project and bundled dependencies are pinned by observed source bytes; original wheel-to-extracted parity exists only for newly downloaded Torch/dependencies and prior isolated OpenVINO/tokenizers."})
    print("Reused local dependency source snapshot:", len(files), "files", flush=True)


if __name__ == "__main__":
    assert not sys.argv[1:]
    run()
