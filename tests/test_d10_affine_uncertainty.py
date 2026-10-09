"""Mathematical witnesses + independent exhaustive rational grid; research, not SENS runtime."""
import copy
import importlib.util
import itertools
import json
import sys
import unittest
from fractions import Fraction as Q
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('d10_affine',ROOT/'scripts/check_d10_affine_uncertainty.py')
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

class ResearchProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(m.MANIFEST.read_text())

    def test_research_only(self):
        self.assertEqual(m.check(self.manifest)['selected_additions'],0)

    def test_same_measurement_cancels_exactly(self):
        a=m.Affine.make(Q(10),{'sensor':Q(1,3),'clock':Q(-2,5)})
        self.assertEqual(m.linear(a,a,-1).hull(),(Q(0),Q(0)))

    def test_independent_measurements_do_not_cancel(self):
        a=m.Affine.make(Q(10),{'sensor_a':Q(1)})
        b=m.Affine.make(Q(10),{'sensor_b':Q(1)})
        self.assertEqual(m.linear(a,b,-1).hull(),(Q(-2),Q(2)))

    def test_shared_coefficients(self):
        a=m.Affine.make(Q(3,2),{'a':Q(7,3),'b':Q(1,4)})
        b=m.Affine.make(Q(1,2),{'a':Q(7,3),'b':Q(-1,4)})
        self.assertEqual(m.linear(a,b,-1).hull(),(Q(1,2),Q(3,2)))

    def test_exact_constant_times_affine(self):
        a=m.Affine.make(Q(2),{})
        b=m.Affine.make(Q(3),{'x':Q(4)})
        self.assertEqual(m.product_enclosure(a,b,'fresh'),m.Affine.make(Q(6),{'x':Q(8)}))

    def test_sound_product_for_all_bounded_grid_valuations(self):
        cases=[
            (m.Affine.make(Q(1),{'a':Q(1)}),m.Affine.make(Q(1),{'a':Q(-1)})),
            (m.Affine.make(Q(-2,3),{'a':Q(1,2),'b':Q(3,5)}),m.Affine.make(Q(5,4),{'a':Q(1,3),'c':Q(-1,8)})),
            (m.Affine.make(Q(0),{'a':Q(1)}),m.Affine.make(Q(0),{'a':Q(1)})),
            (m.Affine.make(Q(4),{}),m.Affine.make(Q(-2),{'b':Q(3)})),
            (m.Affine.make(Q(7,8),{'a':Q(-1,4),'b':Q(2,5)}),m.Affine.make(Q(-3,7),{'a':Q(1,9),'b':Q(5,8)})),
        ]
        samples=(Q(-1),Q(-1,2),Q(0),Q(1,2),Q(1));count=0
        for x,y in cases:
            z=m.product_enclosure(x,y,'fresh')
            low,high=z.hull()
            ids=sorted(set(x.dictionary())|set(y.dictionary()))
            for values in itertools.product(samples,repeat=len(ids)):
                env=dict(zip(ids,values))
                actual=x.value(env)*y.value(env)
                self.assertLessEqual(low,actual)
                self.assertLessEqual(actual,high)
                count+=1
        self.assertGreaterEqual(count,160)

    def test_reusing_fresh_noise_is_error(self):
        a=m.Affine.make(Q(0),{'a':Q(1)})
        with self.assertRaises(ValueError):m.product_enclosure(a,a,'a')

    def test_no_floats(self):
        with self.assertRaises(TypeError):m.Affine.make(1.0,{'x':Q(1)})
        with self.assertRaises(TypeError):m.Affine.make(Q(1),{'x':0.5})

    def test_noise_valuation_bounds(self):
        a=m.Affine.make(Q(0),{'x':Q(1)})
        with self.assertRaises(ValueError):a.value({'x':Q(3,2)})

    def test_dossier_fail_closed_mutations(self):
        for key,value in [('coordinate','0000000000'),('ratified_resident',True),
                          ('selected_in_canonical_inventory',True),('physical_t5_authorized',True),
                          ('status','SELECT'),('positive_witnesses',[])]:
            with self.subTest(key=key):
                obj=copy.deepcopy(self.manifest)
                obj['rows'][0][key]=value
                with self.assertRaises(AssertionError):m.check(obj)
        obj=copy.deepcopy(self.manifest)
        obj['rows'][1]['semantic_name']=obj['rows'][0]['semantic_name']
        with self.assertRaises(AssertionError):m.check(obj)

if __name__=='__main__':
    unittest.main()
