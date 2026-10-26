"""Invented-only boundary tests. No scientific imports or biological reads."""
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as Obj
import unittest
from unittest.mock import patch
from . import inputs,pools,common as c


def audit_fixture():
    return {inputs.spec.CHECKPOINT_PREFIX+'campaign_birth.json':'a'*64} | {
        inputs.spec.CHECKPOINT_PREFIX+inputs.lc.task_key(task)+suffix:'b'*64
        for task in inputs.lc.task_roster() for suffix in ('.birth.json','.model.json','.complete.json')}


class Boundaries(unittest.TestCase):
    def pins(self,pins):
        raw=json.dumps({'files_sha256':pins}).encode()
        return patch.multiple(inputs.spec,SAVED_AUDIT=Obj(read_bytes=lambda:raw),SAVED_AUDIT_SHA=c.digest(raw))

    def test_exact190_hash_metadata_only(self):
        pins=audit_fixture()
        with self.pins(pins):self.assertEqual(inputs.checkpoint_pins(),pins)

    def test_missing_checkpoint_refused(self):
        pins=audit_fixture();pins.pop(next(iter(pins)))
        with self.pins(pins),self.assertRaises(AssertionError):inputs.checkpoint_pins()

    def test_extra_checkpoint_refused(self):
        pins=audit_fixture();pins[inputs.spec.CHECKPOINT_PREFIX+'campaign_complete.json']='c'*64
        with self.pins(pins),self.assertRaises(AssertionError):inputs.checkpoint_pins()

    def test_nonhex_hash_refused(self):
        pins=audit_fixture();pins[next(iter(pins))]='z'*64
        with self.pins(pins),self.assertRaises(AssertionError):inputs.checkpoint_pins()

    def test_saved_records_exact_raw_roles_no_parse(self):
        pins=audit_fixture();calls=[]
        def read(name,want,**kwargs):calls.append(name);self.assertEqual(want,pins[name]);return name.encode()
        with patch.object(inputs,'checkpoint_pins',return_value=pins),patch.object(c,'read_exact',side_effect=read),patch.object(c,'old_absences'):
            rows=inputs.load_records(Obj(checkpoint_hashes=pins),fresh=lambda:None)
        self.assertEqual(len(rows),63);self.assertEqual(len(set(calls)),189)
        for row in rows:
            self.assertEqual(set(row),{'task_key','birth_raw','checkpoint_raw','completion_raw'})
            self.assertTrue(row['checkpoint_raw'].endswith(b'.model.json'))

    def test_reader_rejects_wrong_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented';path.write_bytes(b'invented')
            with patch.object(c,'relative',return_value=path),self.assertRaises(AssertionError):
                c.read_exact('invented','a'*64,fresh=lambda:None)

    def test_fresh_guard_precedes_open(self):
        def stop():raise RuntimeError('invented expired owner')
        with patch.object(c,'relative',side_effect=AssertionError('reader must not run')),self.assertRaises(RuntimeError):
            c.read_exact('invented','a'*64,fresh=stop)

    def test_exact_ast_compile_uses_no_old_factory(self):
        model=b'PAIR_CACHE={}\ndef pair_indices(frame):\n    return frame\n'
        common=('SEED='+str(pools.ss.SEED)+'\n').encode();values={pools.ss.MODEL_SOURCE:model,pools.ss.COMMON_SOURCE:common}
        with patch.object(c,'read_exact',side_effect=lambda name,*args,**kwargs:values[name]),patch.multiple(pools.ss,MODEL_SHA=c.digest(model),COMMON_SHA=c.digest(common)),patch.object(pools.sampler,'load_original_sampler',side_effect=AssertionError('old factory forbidden')):
            token=object();function=pools.original_function(object(),fresh=lambda:None)
            self.assertIs(function(token),token)

    def test_pool_translation_matches_original_operations(self):
        class Values(list):
            def tolist(self):return list(self)
        class Frame:
            def __init__(self,rows,columns):self.rows=rows;self.columns=columns;self.index=range(len(rows))
            def reset_index(self,drop):assert drop is True;return self
        class Matrix:
            def __getitem__(self,index):return ['feature'+str(i) for i in index]
        np=Obj(asarray=lambda value:value,array=lambda value,**kwargs:list(value),float64=object())
        pd=Obj(DataFrame=Frame)
        metadata=[{'intervention_id':str(i),'cell_type':'CAD'} for i in range(3)]
        inp=Obj(metadata=metadata,matrix=Matrix(),effects={'0':1.,'1':-1.,'2':0.})
        def pairs(frame):return Values([0]),Values([1]),Values([1]),Values([1.]),Values(['mikl_gse173098'])
        with patch.object(pools.reference,'preference_contract',return_value=[1.]),patch.object(pools.numeric,'prepare_training',side_effect=lambda *args:{'arguments':args[1:]}),patch.object(pools.adapter,'pool_binding',return_value={'invented':True}),patch.object(pools.adapter,'gate',return_value=None):
            actual=pools.one_pool(np,pd,pairs,inp,[0,1],[2],fresh=lambda:None)
            expected=pools.adapter.one_pool(np,pd,pairs,metadata,inp.matrix,inp.effects,[0,1],[2],None,None)
        self.assertEqual(actual,expected)


def run():
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boundaries))
    print(stream.getvalue(),end='')
    value={'status':'INVENTED_ONLY_INPUT_POOL_BOUNDARIES','tests':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'actual_data_reads':0,'actual_native_jobs':0,
        'source_sha256':{p.relative_to(c.ROOT).as_posix():c.sha(p) for p in (c.SRC/'inputs.py',c.SRC/'pools.py',Path(__file__))}}
    assert result.wasSuccessful()
    c.save_new(c.OUT/'inputs_pools_tests_receipt.json',value)


if __name__=='__main__':run()
