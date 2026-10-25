"""Exclusive, bounded, durable operational telemetry; no scientific values."""
import json
import os
from pathlib import Path
import time


class Journal:
    MAX_BYTES = 8 * 2**20

    def __init__(self, path):
        self.path = Path(path)
        self.stream = None
        self.bytes = 0
        self.last_sample = None

    def __enter__(self):
        self.stream = self.path.open('xb')
        return self

    def event(self, status, **fields):
        assert isinstance(status, str) and self.stream is not None
        raw = (json.dumps({'status': status, 'monotonic': time.monotonic(), **fields},
            sort_keys=True, allow_nan=False) + '\n').encode('utf8')
        assert len(raw) <= 64 * 2**10 and self.bytes + len(raw) <= self.MAX_BYTES
        assert self.stream.write(raw) == len(raw)
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.bytes += len(raw)

    def sample(self, value):
        elapsed = value['elapsed_seconds']
        assert type(elapsed) in (int, float) and elapsed >= 0
        if (self.last_sample is None or elapsed - self.last_sample >= 1
                or value['exit_code'] is not None or value['pending_failure'] is not None):
            self.event('OWNED_WORKER_SAMPLE', **value)
            self.last_sample = elapsed

    def __exit__(self, *_):
        self.stream.close()
        self.stream = None
