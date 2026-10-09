"""Adversarial historical finite-code law tests: no D2 control or new D10 slots."""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'scripts/check_d10_unique_decipherability_historical.py'
spec=importlib.util.spec_from_file_location('d10_ud_guard',SRC)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class UniqueDecipherability(unittest.TestCase):
    def test_classical_counterexamples(self):
        items=[
            ([('a','0'),('b','11')],True),
            ([('a','0'),('b','01')],True),
            ([('a','0'),('b','01'),('c','10')],False),
            ([('a','0'),('b','1'),('c','000000')],False),
            ([('a','00'),('b','00')],False),
            ([('a','00'),('b','01'),('c','10'),('d','11')],True),
            ([],True),
            ([('a','0')],True),
        ]
        for d,expected in items:
            with self.subTest(d=d):
                got,w=module.unique_decoding_with_witness(d)
                self.assertEqual(got,expected)
                self.assertEqual(module.sardinas_patterson_decision(d),expected)
                if not got:
                    a,b=w
                    self.assertNotEqual(a,b)
                    x=dict(d)
                    self.assertEqual(''.join(x[s] for s in a),''.join(x[s] for s in b))

    def test_exhaustive_independent_suffix_fixedpoint(self):
        words=[''.join(w) for size in (1,2,3)
               for w in itertools.product('01',repeat=size)]
        checked=0
        for size in (2,3,4):
            for sample in itertools.combinations(words,size):
                d=list(zip([str(i) for i in range(size)],sample))
                got,w=module.unique_decoding_with_witness(d)
                independently=module.sardinas_patterson_decision(d)
                self.assertEqual(got,independently,(d,w))
                if not got:
                    a,b=w
                    x=dict(d)
                    self.assertNotEqual(a,b)
                    self.assertEqual(''.join(x[s] for s in a),''.join(x[s] for s in b))
                checked+=1
        self.assertEqual(checked,1456)

    def test_reject_invalid_input(self):
        for x in ([('a','')],[('a','02')],[('a','1'),('a','0')],
                  [('a',1)], [('','0')], [('a','0','1')], {'a':'0'}):
            with self.subTest(x=x):
                with self.assertRaises(ValueError):
                    module.unique_decoding_with_witness(x)

    @classmethod
    def setUpClass(cls):
        load=lambda p: json.loads((ROOT/p).read_text(encoding='utf-8'))
        cls.ledger=load('knowledge/d10-unique-decipherability-historical-20261009.json')
        cls.foundation=load('knowledge/d1-d9-foundation.json')
        cls.inventory=load('knowledge/d10-v1-semantic-inventory.json')

    def test_live_domain_inventory(self):
        x=module.validate_ledger(self.ledger,self.foundation,self.inventory)
        self.assertEqual(x['newly_selected'],0)
        self.assertEqual(x['ratified'],0)

    def test_no_invented_coordinates(self):
        for update in ({'coordinate':'0000000000'},{'ratified':True},
                       {'selected':True},{'physical_t5_authorized':True}):
            ledger=copy.deepcopy(self.ledger)
            ledger['proposals'][0].update(update)
            with self.subTest(update=update),self.assertRaises(AssertionError):
                module.validate_ledger(ledger,self.foundation,self.inventory)

    def test_lower_and_selected_collisions(self):
        for name in ('STRING-PREFIX?',self.inventory['rows'][0]['semantic_name']):
            ledger=copy.deepcopy(self.ledger)
            ledger['proposals'][0]['semantic_name']=name
            with self.subTest(name=name),self.assertRaises(AssertionError):
                module.validate_ledger(ledger,self.foundation,self.inventory)

    def test_must_not_borrow_control(self):
        ledger=copy.deepcopy(self.ledger)
        ledger['changes_to_d2_or_t5']=True
        with self.assertRaises(AssertionError):
            module.validate_ledger(ledger,self.foundation,self.inventory)

if __name__=='__main__': unittest.main()
