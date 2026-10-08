import unittest
from src.generalization_rdata_metadata_feasibility_20261008.tests import Tests as OriginalTests,node,strings,pair,char,Arr
from . import metadata as m
def frame(columns):
    return node("VEC",list(columns.values()),attrs=pair({"class":strings(["data.frame"]),"names":strings(list(columns))}))
class Tests(unittest.TestCase):
    def test_shared_reference_dag_allowed(self):
        shared=char("a");self.assertEqual(m.count_metadata_nodes(node("VEC",[shared,shared])),2)
    def test_value_and_reference_cycles_rejected(self):
        for is_ref in (False,True):
            n=node("REF" if is_ref else "VEC")
            if is_ref:n.referenced_object=n
            else:n.value=[n]
            with self.assertRaises(AssertionError):m.count_metadata_nodes(n)
    def test_annotation_node_bound_and_unsafe_types_rejected(self):
        with self.assertRaises(AssertionError):m.count_metadata_nodes(node("VEC",[char("a")]),cap=1)
        for kind in ("ALTREP","CLO","PROM","ENV","EXTPTR","EXPR"):
            with self.assertRaises(AssertionError):m.count_metadata_nodes(node(kind))
    def test_integral_real_design_only_and_missing(self):
        values,meta=m.column(node("REAL",Arr([1.,None,float("nan"),-2.])),True)
        self.assertEqual(values,[1,None,None,-2]);self.assertEqual(meta["type"],"integer_valued_REAL_design_metadata")
        with self.assertRaises(AssertionError):m.column(node("REAL",Arr([1.])))
    def test_nonintegral_nonfinite_overflow_and_classes_rejected(self):
        for value in (1.5,float("inf"),float("-inf"),float(2**54)):
            with self.assertRaises(AssertionError):m.column(node("REAL",Arr([value])),True)
        with self.assertRaises(AssertionError):m.column(node("REAL",Arr([1.]),attrs=pair({"class":strings(["unsafe"])})),True)
    def test_no_unselected_count_values_exported(self):
        annotation=frame({"tileID":strings(["WT","mut"]),"group":strings(["WT","Single"]),"counts":node("REAL",Arr([123.,456.]))})
        result=m.export(annotation);self.assertEqual(result["exported_allowlist_columns"],["tileID","group"])
        self.assertNotIn("counts",result["rows"][0]);self.assertIn("counts",result["all_annotation_column_names"])
    def test_ids_and_equal_length_rejected(self):
        for columns in ({"tileID":strings(["WT","WT"])},{"tileID":strings([None])},{"tileID":strings(["WT","mut"]),"group":strings(["WT"])}):
            with self.assertRaises(AssertionError):m.export(frame(columns))
    def test_binding_real_not_accepted_as_tile_identifier(self):
        with self.assertRaises(AssertionError):m.export(frame({"tileID":node("REAL",Arr([1.]))}))
    def test_missing_duplicate_and_malformed_global_bindings(self):
        from src.generalization_rdata_metadata_feasibility_20261008 import decode as d
        with self.assertRaises(AssertionError):m.select_annotation(pair({"other":char("x")}))
        bad=node("LIST",(char("x"),node("NILVALUE")),tag=node("INT",Arr([1])))
        with self.assertRaises(AssertionError):m.select_annotation(bad)
        duplicate=node("LIST",(char("x"),pair({"tile.annot":char("y")})),tag=node("SYM",char("tile.annot")))
        with self.assertRaises(AssertionError):m.select_annotation(duplicate)
        with self.assertRaises(AssertionError):d.pairs(pair({"a":char("a"),"b":char("b")}),cap=1)
    def test_global_pairlist_cycle_and_root_type_rejected(self):
        global_=pair({"tile.annot":char("x")});global_.value=(global_.value[0],global_)
        with self.assertRaises(AssertionError):m.select_annotation(global_)
        with self.assertRaises(AssertionError):m.select_annotation(node("VEC",[]))
    def test_edge_cap_for_many_shared_children(self):
        child=char("x")
        with self.assertRaises(AssertionError):m.count_metadata_nodes(node("VEC",[child]*20),edge_cap=10)
    def test_attribute_cycles_and_unrelated_globals(self):
        a=char("x");a.attributes=a
        with self.assertRaises(AssertionError):m.count_metadata_nodes(a)
        annotation=frame({"tileID":strings(["WT"])})
        _,selected=m.select_annotation(pair({"unrelated":node("REAL",Arr([999.]*10001)),"tile.annot":annotation}))
        self.assertEqual(m.export(selected),m.export(annotation))
    def test_string_and_vector_shape_caps(self):
        with self.assertRaises(AssertionError):m.count_metadata_nodes(node("CHAR",b"x"*10001))
        with self.assertRaises(AssertionError):m.count_metadata_nodes(node("REAL",Arr([1.]*10001)))
        with self.assertRaises(AssertionError):m.export(frame({"tileID":strings(["WT"]),"other":node("VEC",[char("x")])}))
        with self.assertRaises(AssertionError):m.export(frame({"tileID":strings(["WT"]),"other":strings(["a","b"])}))
    def test_compact_row_names_and_factors(self):
        from src.generalization_rdata_metadata_feasibility_20261008 import decode as d
        annotation=frame({"tileID":strings(["WT","mut"])})
        attributes=d.pairs(annotation.attributes);attributes["row.names"]=node("INT",Arr([-2147483648,-2]))
        annotation.attributes=pair(attributes)
        self.assertEqual(len(m.export(annotation)["rows"]),2)
if __name__=="__main__":unittest.main(verbosity=2)
