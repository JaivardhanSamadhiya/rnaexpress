"""Create a compact local checkpoint without modifying the Git index."""
from .common import ROOT, sha256, write_new, write_json
from pathlib import Path
import io
import zipfile


def run():
    paths = []
    for directory, suffixes in (
        ('src/research_20260921', {'.py'}),
        ('reports/research_20260921', {'.md'}),
        ('results/research_20260921', {'.json','.csv','.log'})):
        paths.extend(p for p in (ROOT/directory).iterdir() if p.is_file() and p.suffix in suffixes
                     and p.name != 'checkpoint_bundle_receipt.json')
    data = ROOT/'data/external/research_20260921'
    paths.extend(data.rglob('*.receipt.json'))
    paths.extend(data/name for name in ('srle_gsa_runs_all','srle_raw_checksums','srle_author_count_code'))
    buffer = io.BytesIO()
    hashes = {}
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(set(paths)):
            if path.stat().st_size > 10*1024*1024:
                raise ValueError('Unexpectedly large compact checkpoint member')
            relative = path.relative_to(ROOT).as_posix()
            hashes[relative] = sha256(path)
            info = zipfile.ZipInfo(relative, date_time=(2026,9,21,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info,path.read_bytes())
    path = ROOT/'results/research_20260921/checkpoint_bundle.zip'
    write_new(path,buffer.getvalue())
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Checkpoint archive CRC failed')
    write_json(path.with_name('checkpoint_bundle_receipt.json'), {
        'sha256':sha256(path),'bytes':path.stat().st_size,'members':hashes,
        'scope':'Code, reports, derived results, source metadata and receipts; large source archives/raw reads remain in local data namespace'})
    print({'bundle':str(path),'bytes':path.stat().st_size,'members':len(hashes),'sha256':sha256(path)})


if __name__ == '__main__':
    run()
