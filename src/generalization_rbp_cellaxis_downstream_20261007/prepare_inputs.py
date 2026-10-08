"""Additive fresh-resource wrapper; original six preparation sources unchanged."""
from .common import design_check,resource_check,committed,readj


def run(command,root_start=False):
    assert command in ('metadata','matrices')
    design_check(root_start);resource_check(3.,1.)
    from .runtime_guard import python_contract,SCIENTIFIC
    committed(SCIENTIFIC);python_contract(readj(SCIENTIFIC))
    from src.generalization_rbp_cellaxis_20261007 import prepare
    # The original entry point also checks its own committed preparation/root
    # start. The new wrapper supplies the mandatory fresh floor before runtime
    # import and before any full source matrix can be decoded.
    getattr(prepare,command)(root_start=True)


if __name__=='__main__':
    import sys
    run(sys.argv[1],'--root-start' in sys.argv[2:])
