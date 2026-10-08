"""Standard-library/invented-logit tests only: imports/model/weight calls zero."""
import ast
from dataclasses import replace
import json
import math
from pathlib import Path
import unittest

from . import common as c
from . import token_math as m


def fake_logits(inputs):
    assert set(inputs) == {'input_ids','attention_mask','token_type_ids'}
    result = []
    for ids in inputs['input_ids']:
        # Invented deterministic values only; depends on supplied context, no ID.
        total = sum(ids)
        result.append([[float(i*.25+t*.5+total*.001) for t in range(10)] for i in range(len(ids))])
    return result


def fake_admission():
    z='a'*64
    backend={'status':'PASS','scope':'SYNTHETIC_CPU_BACKEND_ADMISSION_ONLY','checkpoint_sha256':c.CHECKPOINT_SHA,
        'synthetic_alleles':16,'project_alleles_inferred':0,'models_fit':0,'outcomes_used':False,
        'unused_MLM_head_keys':list(c.HEAD_KEYS),'comparisons':[{'length_nt':n,'maximum_hidden_absolute_difference':.00001,
            'mean_hidden_absolute_difference':.000001,'minimum_token_cosine':1.,'checks':{'all':True}} for n in [46,46,150,150,190,190,260,260]],
        'IR_xml_sha256':z,'IR_bin_sha256':z}
    compatibility={'status':'PASS_SYNTHETIC_BACKEND_WITH_VERIFIED_NUMPY_ORIGIN','full_production_authorized':False,
        'project_alleles':0,'models_fit':0,'outcomes_read':False,'original_guard_binding_restored':True,
        'IR_xml_sha256':z,'IR_bin_sha256':z,'original_backend_synthetic_receipt_sha256':z,
        'NumPy_import_receipt_sha256':z,'repair_preparation_sha256':z}
    proof={'status':'PASS','numpy_version':'1.26.4','model_packages_imported_before_NumPy_verification':False,
        'numpy_origin':'synthetic/numpy/__init__.py','native_core_origin':'synthetic/numpy/core/example.pyd',
        'native_core_sha256':z,'repair_preparation_sha256':z,'scientific_runtime_receipt_sha256':z}
    observed={'numpy_origin':proof['numpy_origin'],'native_core_origin':proof['native_core_origin'],
        'native_core_sha256':z,'IR_xml_sha256':z,'IR_bin_sha256':z,'backend_sha256':z,'numpy_proof_sha256':z,
        'repair_preparation_sha256':z,'scientific_runtime_receipt_sha256':z}
    return backend,compatibility,proof,observed


class Tests(unittest.TestCase):
    def test_01_union_mask_has_one_exact_shared_context(self):
        r=m.request('AACGTA','TACGTT');rev=m.request(r.mutant,r.parent)
        self.assertEqual(r.positions,(0,5));self.assertEqual(r.input_ids,(2,4,6,7,8,9,4,3))
        self.assertEqual(r.input_ids,rev.input_ids);self.assertEqual(r.context_sha256,rev.context_sha256)
        self.assertEqual(m.model_inputs([r])['attention_mask'],[[1]*8])

    def test_02_logsoftmax_matched_normalizer_and_offsets(self):
        r=m.request('AC','TC');logits=fake_logits(m.model_inputs([r]))[0];v=m.score(r,logits)
        self.assertEqual(v['score'],1.5);self.assertEqual(v['per_edit'][0]['token_position'],1)
        self.assertAlmostEqual(sum(math.exp(x) for x in m.log_softmax(logits[1])),1.,places=14)
        self.assertAlmostEqual(v['per_edit'][0]['logp_alternate']-v['per_edit'][0]['logp_reference'],v['score'],places=14)

    def test_03_noedit_zero_never_calls_predictor(self):
        r=m.request('ACGT','ACGT');v=m.evaluate([r],lambda _:self.fail('No model call'))
        self.assertEqual(v[0]['score'],0.);self.assertEqual(v[0]['per_edit'],[])

    def test_04_reversal_and_multisite_sum(self):
        r=m.request('ACGTAC','TGCATG');rev=m.request(r.mutant,r.parent)
        v=m.evaluate([r,rev],fake_logits)
        self.assertEqual(v[0]['score'],-v[1]['score']);self.assertEqual(len(v[0]['per_edit']),6)
        self.assertEqual(v[0]['score'],math.fsum(e['log_ratio'] for e in v[0]['per_edit']))

    def test_05_stable_large_logits_and_shift_invariance(self):
        a=m.log_softmax([1000.+i for i in range(10)]);b=m.log_softmax([i for i in range(10)])
        self.assertEqual(a,b);self.assertTrue(all(math.isfinite(x) for x in a))
        self.assertAlmostEqual(sum(math.exp(x) for x in a),1.,places=14)

    def test_06_invalid_bases_length_indels_and_edit_count(self):
        for a,b in [('AC','AN'),('AC','AU'),('ac','AC'),('AC','T'),('AAAAAAA','TTTTTTT'),('','')]:
            with self.assertRaises(AssertionError):m.request(a,b)

    def test_07_unknown_mask_wrong_positions_and_refs_rejected(self):
        r=m.request('AC','TC')
        for bad in [replace(r,input_ids=(2,1,7,3)),replace(r,input_ids=(2,6,7,3)),replace(r,positions=(1,)),replace(r,reference_ids=(4,))]:
            with self.assertRaises(AssertionError):m.model_inputs([bad])
            with self.assertRaises(AssertionError):m.score(bad,[[0.]*10]*4)

    def test_08_invalid_logits_shapes_and_nonfinite_rejected(self):
        r=m.request('AC','TC')
        for rows in [[[0.]*10]*3,[[0.]*9]*4,[[math.nan]*10]*4,[[math.inf]*10]*4]:
            with self.assertRaises(AssertionError):m.score(r,rows)
        with self.assertRaises(AssertionError):m.log_softmax([1e308,-1e308]+[0.]*8)

    def test_09_tail_duplicate_one_call_and_no_fake_padding(self):
        requests=[m.request('ACGT','TCGT'),m.request('ACGT','AGGT'),m.request('ACGT','ACGA')]
        calls=[]
        def predictor(x):calls.append(x);return fake_logits(x)
        result=m.evaluate(requests,predictor)
        self.assertEqual(len(calls),2);self.assertEqual(calls[1]['input_ids'][0],calls[1]['input_ids'][1])
        self.assertEqual(len(result),3)
        for value,expected in zip(result,[1.5,.5,-1.5]):self.assertAlmostEqual(value['score'],expected,delta=1e-12)
        self.assertNotIn(0,sum([x['input_ids'][0] for x in calls],[]))

    def test_10_group_lengths_predictor_receives_only_context(self):
        r=m.request('ACGT','TCGT');s=m.request('AC','TC')
        with self.assertRaises(AssertionError):m.model_inputs([r,s])
        batches=list(m.batches([r,s]));self.assertEqual([len(v[0][0].input_ids) for v in batches],[4,6])
        self.assertEqual(set(m.model_inputs([r])),{'input_ids','attention_mask','token_type_ids'})

    def test_11_synthetic_original16_and_additional20(self):
        left,right='GCCCACAAGTATCACTAAGC','ATCATAATCAGCCATACCAC'
        original=m.synthetic_sequences(left,right);self.assertEqual(original,m.synthetic_sequences(left,right))
        self.assertEqual(len(original),16);self.assertEqual(sorted(map(len,original)),[46]*4+[150]*4+[190]*4+[260]*4)
        pairs=[m.request(original[i],original[i+1]) for i in range(0,16,2)]
        self.assertEqual([len(r.positions) for r in pairs],[1]*8)
        extra=m.additional_synthetic_requests(original);self.assertEqual(len(extra),20)
        for count in (2,3,4,5,6):self.assertEqual(sum(len(r.positions)==count for r in extra),4)
        self.assertTrue(all(0 in r.positions and len(r.parent)-1 in r.positions for r in extra))

    def test_12_tied_head_metadata_alias_and_shape_contract(self):
        fields={n:{'shape':list(shape),'dtype':'float32','finite':True,'sha256':'a'*64} for n,shape in c.HEAD_KEYS.items()}
        fields['bert.embeddings.word_embeddings.weight']={'shape':[10,512],'dtype':'float32','finite':True,'sha256':'a'*64}
        self.assertTrue(c.certify_alias_metadata(fields))
        for key in ('cls.predictions.decoder.weight','cls.predictions.decoder.bias'):
            changed={k:dict(v) for k,v in fields.items()};changed[key]['sha256']='b'*64
            with self.assertRaises(AssertionError):c.certify_alias_metadata(changed)
        changed={k:dict(v) for k,v in fields.items()};changed['cls.predictions.decoder.weight']['shape']=[512,10]
        with self.assertRaises(AssertionError):c.certify_alias_metadata(changed)

    def test_13_backend_origin_ir_and_receipt_chain_mismatches(self):
        records=fake_admission();self.assertTrue(c.certify_encoder_metadata(*records))
        for key in ('IR_bin_sha256','native_core_origin','backend_sha256','scientific_runtime_receipt_sha256'):
            changed=dict(records[3]);changed[key]='wrong'
            with self.assertRaises(AssertionError):c.certify_encoder_metadata(*records[:3],changed)

    def test_14_failed_backend_wrong_head_and_numpy_rejected(self):
        records=fake_admission();backend=dict(records[0]);backend['status']='FAIL'
        with self.assertRaises(AssertionError):c.certify_encoder_metadata(backend,*records[1:])
        backend=dict(records[0]);backend['unused_MLM_head_keys']=[]
        with self.assertRaises(AssertionError):c.certify_encoder_metadata(backend,*records[1:])
        proof=dict(records[2]);proof['numpy_version']='2.4.6'
        with self.assertRaises(AssertionError):c.certify_encoder_metadata(records[0],records[1],proof,records[3])

    def test_15_source_is_stdlib_only_four_byte_attributes(self):
        c.clean_imports()
        for path in c.SRC.glob('*.py'):
            tree=ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    self.assertTrue(all(n.name.split('.')[0] not in c.BLOCKED for n in node.names))
                if isinstance(node,ast.ImportFrom) and node.module:
                    self.assertNotIn(node.module.split('.')[0],c.BLOCKED)
        for folder in (c.SRC,c.ART,c.OUT,c.REP):self.assertEqual((folder/'.gitattributes').read_bytes(),b'* -text\n')
        with self.assertRaises(AssertionError):c.clean_imports({'torch':object()})


def run():
    c.clean_imports()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert result.wasSuccessful();c.clean_imports()
    c.jsave(c.OUT/'synthetic_tests_receipt.json',{'status':'PASS','tests':result.testsRun,
        'source_hashes':{p.relative_to(c.ROOT).as_posix():c.sha256(p) for p in sorted(c.SRC.glob('*.py'))},
        'plan_sha256':c.sha256(c.REP/'plan.md'),'actual_numeric_imports':0,'actual_model_imports':0,
        'checkpoint_loads':0,'model_calls':0,'project_sequences_read':0,'outcomes_read':False,'fits':0,
        'scope':'Standard-library masking/math and mocked head/runtime metadata only; no native certification'})
    print('Masked-likelihood stdlib/mock tests PASS',result.testsRun,flush=True)


if __name__=='__main__':run()
