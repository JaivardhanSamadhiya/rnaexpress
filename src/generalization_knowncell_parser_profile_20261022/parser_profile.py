"""Invented StringIO/BytesIO tests using the exact deferred pandas call."""
import hashlib
import io
from . import cases

GOLDEN_HEX = ('000000000000f43f00000000000004c000000000000000000000000000000080'
              '0000000000004043')


def run(pd):
    from src.generalization_knowncell_joint_loader_20261022.parsers import pandas_effects
    checks = []
    tests = cases.successful_cases() + [('golden_exact_binary', cases.csv_text([
        ('a','1.25','x'), ('b','-2.5','x'), ('c','0.0','x'),
        ('d','-0.0','x'), ('e','9007199254740992','x')]), [0,1,2,3,4])]
    for name, text, positions in tests:
        selected = cases.metadata(text, positions)
        ids, expected = cases.original_pandas(text, pd, selected)
        expected_bytes = cases.float_bytes(expected)
        if name == 'golden_exact_binary': assert expected_bytes.hex() == GOLDEN_HEX
        for kind, stream in [('StringIO', io.StringIO(text)), ('BytesIO', io.BytesIO(text.encode()))]:
            result = pandas_effects(stream, pd, selected)
            assert result['intervention_ids'] == ids
            raw = cases.float_bytes(result['measured_delta'])
            assert raw == expected_bytes
            assert result['parsed_effects_float64_sha256'] == hashlib.sha256(raw).hexdigest()
            checks.append({'case': name, 'stream': kind, 'rows': len(ids), 'float64_little_endian_hex': raw.hex()})
        wrong = dict(selected, rows=list(reversed(selected['rows'])))
        try: pandas_effects(io.StringIO(text), pd, wrong)
        except AssertionError: pass
        else: raise AssertionError('Selected ID/order corruption was accepted')
    rejections = []
    for name, text, positions in cases.rejected_csv_cases():
        try: cases.metadata(text, positions)
        except (AssertionError, ValueError, __import__('csv').Error): rejections.append(name)
        else: raise AssertionError('Invalid CSV prerequisite accepted: '+name)
    for name, text, positions in cases.rejected_numeric_cases():
        selected = cases.metadata(text, positions)
        for function in (lambda: cases.original_pandas(text, pd, selected),
                         lambda: pandas_effects(io.StringIO(text), pd, selected)):
            try: function()
            except (AssertionError, ValueError): pass
            else: raise AssertionError('Invalid selected numeric field accepted: '+name)
        rejections.append(name)
    return {'status': 'PASS_INVENTED_EXACT_DEFERRED_PARSER', 'checks': checks,
            'rejected_cases': rejections, 'default_float_parser_preserved': True,
            'Python_float_replacement_used': False,
            'old_interpreter_bitwise_parity_established': False,
            'scope': 'Golden exactly representable invented values, current original-call equivalence, row-mask and ID semantics; not old-versus-current interpreter bitwise parity.'}
