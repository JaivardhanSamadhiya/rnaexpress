"""Capture the isolated runtime, hardware and exact installed dependency versions."""
from __future__ import annotations
import importlib.metadata
import os
import platform
import sys
from .io import ROOT,write_json,write_once,git


def capture():
    packages=sorted({f'{d.metadata["Name"]}=={d.version}' for d in importlib.metadata.distributions(
        path=[str(ROOT/'data/interim/mechanism_v2/runtime')])})
    write_once('configs/mechanism_v2/environment.lock.txt',('\n'.join(packages)+'\n').encode())
    result={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
        'cpu':platform.processor(),'logical_cpu_count':os.cpu_count(),'packages':packages,
        'gpu_used':False,'scope':'Mechanism-v2 CPU feature/audit runtime, not the archived training environment',
        'base_experiment_commit':git('rev-parse','98ffc02')}
    write_json('results/mechanism_v2/manifests/environment.json',result)
    return result


if __name__=='__main__':
    capture()
