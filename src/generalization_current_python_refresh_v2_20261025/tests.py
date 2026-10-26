"""Invented full42-native metadata; no actual42/7998 byte reads."""
import copy
import unittest
from src.generalization_current_python_refresh_20261025.contracts import compare_inventory,payload_contract
from src.generalization_current_python_refresh_20261025.tests import payload_fixture
from .contracts import bind_discovery,full_native_contract

A,B,C,D=('a'*64,'b'*64,'c'*64,'d'*64)
STATUS='DISCOVERED_CURRENT42_NATIVE_BYTE_PINS_NOT_COMPATIBILITY_OR_ORIGIN_PROOF'


def fixture():
    home='C:\\bundled'
    names=['python.exe','python3.dll','python312.dll']+['DLLs\\module'+str(i)+'.pyd' for i in range(39)]
    old={home+'\\'+name:A for name in names}
    current=dict(old)
    anchors={'python.exe':B,'python3.dll':C,'python312.dll':D}
    current.update({home+'\\'+name:want for name,want in anchors.items()})
    current.update({home+'\\DLLs\\module'+str(i)+'.pyd':D for i in range(35)})
    changes={name:{'prior_sha256':old[name],'current_sha256':want} for name,want in current.items() if old[name]!=want}
    value={'status':STATUS,'current_native_files':current,'native_file_metadata':{name:{} for name in current},
        'native_file_count':42,'changed_file_count':38,'unchanged_file_count':4,
        'changes_from_prior_inventory':changes,'actually_loaded_DLL_origins_verified':False,
        'numerical_compatibility_established':False,'scientific_payload_files_read':0,'biological_inputs_read':False}
    return old,current,anchors,home,value


class Tests(unittest.TestCase):
    def test_exact42_roster_and38_explicit_changes(self):
        old,current,anchors,home,value=fixture()
        changes=full_native_contract(old,current,anchors,home)
        self.assertEqual(len(changes),38);self.assertEqual(changes,value['changes_from_prior_inventory'])

    def test_missing_extra_or_replaced_path_rejected(self):
        for mode in ('missing','extra','replaced'):
            old,current,anchors,home,value=fixture()
            if mode=='missing':current.pop(home+'\\DLLs\\module38.pyd')
            if mode=='extra':current[home+'\\DLLs\\extra.pyd']=B
            if mode=='replaced':current[home+'\\DLLs\\extra.pyd']=current.pop(home+'\\DLLs\\module38.pyd')
            with self.assertRaises(AssertionError):full_native_contract(old,current,anchors,home)

    def test_root_three_anchor_changes_remain_required(self):
        old,current,anchors,home,value=fixture();current[home+'\\python.exe']=C
        with self.assertRaises(AssertionError):full_native_contract(old,current,anchors,home)

    def test_discovery_count37_or39_rejected(self):
        for extra in (False,True):
            old,current,anchors,home,value=fixture()
            current[home+'\\DLLs\\module'+('35' if extra else '34')+'.pyd']=D if extra else A
            with self.assertRaises(AssertionError):full_native_contract(old,current,anchors,home)

    def test_fixed_discovery_future_native_drift_rejected(self):
        old,current,anchors,home,value=fixture();expected=dict(current)
        current[home+'\\DLLs\\module0.pyd']=B
        with self.assertRaises(AssertionError):compare_inventory(expected,current,'fixed42')

    def test_discovery_byte_mapping_and_difference_proof_bound(self):
        old,current,anchors,home,value=fixture()
        self.assertEqual(bind_discovery(value,old,anchors,home,STATUS),(current,value['changes_from_prior_inventory']))
        value['changes_from_prior_inventory'].pop(home+'\\python.exe')
        with self.assertRaises(AssertionError):bind_discovery(value,old,anchors,home,STATUS)

    def test_discovery_false_origin_parity_or_payload_read_rejected(self):
        for key in ('actually_loaded_DLL_origins_verified','numerical_compatibility_established','scientific_payload_files_read','biological_inputs_read'):
            old,current,anchors,home,value=fixture();value[key]=True
            with self.assertRaises(AssertionError):bind_discovery(value,old,anchors,home,STATUS)

    def test_discovery_metadata_roster_or_status_rejected(self):
        for mode in ('metadata','status'):
            old,current,anchors,home,value=fixture()
            if mode=='metadata':value['native_file_metadata'].pop(home+'\\python.exe')
            else:value['status']='PASS_NUMERICAL_EQUIVALENCE'
            with self.assertRaises(AssertionError):bind_discovery(value,old,anchors,home,STATUS)

    def test_original7996_plus_two_cache_membership_remains_exact(self):
        base,expanded,full,caches=payload_fixture()
        self.assertEqual(len(payload_contract(base,expanded,full,caches,['numpy'])),7998)
        expanded['files']['numpy/item0.txt']=D
        with self.assertRaises(AssertionError):payload_contract(base,expanded,full,caches,['numpy'])


if __name__=='__main__':unittest.main(verbosity=2)
