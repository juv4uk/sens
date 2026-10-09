import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / 'scripts/check_d10_d9_donor_dedup.py'
spec = importlib.util.spec_from_file_location('checker', SRC)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('lib', 'knowledge'):
            (self.root / folder).mkdir()
        self.review = json.loads((BASE / checker.REVIEW).read_text())
        self.fnd={'domains':{'D9':{'residents':{x['coordinate']:x['semantic_name'] for x in self.review['d9_existing']}}}}
        self.inv={'rows':[{'semantic_name':'SEARCH'}], 'accounting':{'selected_semantic_candidates':1,'ratified_d10_residents':0}}
        self.review['selected_main_snapshot'] = 1
        for source in self.review['donors']:
            matching = [x for x in self.review['d9_existing'] if x['donor']==source['path']]
            data = [''] * max(x['line'] for x in matching)
            for row in matching:
                data[row['line']-1] = '(00001001 '+row['source_name'] if source['path'].endswith('vector.lisp') else '(00001011 '+row['source_name']
            raw = ('\n'.join(data)+'\n').encode()
            source['git_blob_sha'] = checker.sha_blob(raw)
            (self.root / source['path']).write_bytes(raw)
        self.save()

    def save(self):
        (self.root / checker.REVIEW).write_text(json.dumps(self.review))
        (self.root / checker.D9).write_text(json.dumps(self.fnd))
        (self.root / checker.D10).write_text(json.dumps(self.inv))

    def test_clean_research_dossier(self):
        self.assertEqual(checker.verify(self.root)['new_d10_selected'],0)

    def test_catches_corrupt_source(self):
        (self.root / 'lib/persistent-vector.lisp').write_text('TAMPER')
        with self.assertRaises(AssertionError): checker.verify(self.root)

    def test_catches_renumbered_d9_coordinate(self):
        self.fnd['domains']['D9']['residents']['101011101']='DIFFERENT'
        self.save()
        with self.assertRaises(AssertionError): checker.verify(self.root)

    def test_catches_false_d10_admission(self):
        self.inv['rows'].append({'semantic_name':'VEC-CONJ'})
        self.inv['accounting']['selected_semantic_candidates']=2
        self.save()
        with self.assertRaises(AssertionError): checker.verify(self.root)

    def test_catches_guessed_coordinate(self):
        self.review['separate_review'][0]['coordinate']='0000000001'
        self.save()
        with self.assertRaises(AssertionError): checker.verify(self.root)

    def test_catches_false_ratification(self):
        self.inv['accounting']['ratified_d10_residents']=1
        self.save()
        with self.assertRaises(AssertionError): checker.verify(self.root)

    def test_catches_witness_falsifier_removed(self):
        self.review['false_promotions'][0]['falsifier']=''
        self.save()
        with self.assertRaises(AssertionError): checker.verify(self.root)

if __name__=='__main__': unittest.main()
