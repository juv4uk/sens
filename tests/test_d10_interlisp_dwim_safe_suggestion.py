"""Independent one-edit witness and mandatory fail-closed research rules."""
import copy
import importlib.util
import json
from pathlib import Path
import itertools
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'scripts/check_d10_interlisp_dwim_safe_suggestion.py'
spec = importlib.util.spec_from_file_location('dwim', SRC)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def one_edit(a, b):
    """Independent generator/reference for zero or exactly one edit; not dynamic programming."""
    if a == b:
        return 0
    alphabet = 'ab'
    neigh = {a[:i] + a[i+1:] for i in range(len(a))}
    neigh |= {a[:i] + x + a[i:] for x in alphabet for i in range(len(a)+1)}
    neigh |= {a[:i] + x + a[i+1:] for x in alphabet for i in range(len(a))}
    neigh |= {a[:i] + a[i+1] + a[i] + a[i+2:] for i in range(len(a)-1)}
    return 1 if b in neigh else 2


class DWIMSafe(unittest.TestCase):
    def test_reference_edit1_exhaustive(self):
        words = [''.join(seq) for n in range(0, 6) for seq in itertools.product('ab', repeat=n)]
        for a in words:
            for b in words:
                self.assertEqual(min(2, module.osa_distance(a, b)), one_edit(a, b), (a, b))

    def test_historical_doubled_and_adjacent(self):
        for word in ('CONNS', 'CNOS'):
            z = module.propose(word, [('CONS', '100')]); self.assertEqual((z['status'], z['distance']), ('SUGGEST', 1))
        self.assertEqual(module.propose('CONS', [('CONS', '100')])['status'], 'EXACT')

    def test_context_and_distinct_id_ambiguity(self):
        z = module.propose('CONX', [('CONS', '100'), ('COND', '101')])
        self.assertEqual(z['status'], 'AMBIGUOUS')
        self.assertEqual(z['candidate'], None)
        self.assertEqual(z['alternatives'], [['COND','101'], ['CONS','100']])
        self.assertEqual(module.propose('CONX', [('COND','101')])['status'], 'SUGGEST')
        z = module.propose('CONS', [('CONS','100'), ('CONS','101')]); self.assertEqual(z['status'], 'AMBIGUOUS')

    def test_exact_identity_bits_and_d2_never_rewritten(self):
        for token in ('01011', '()', '(', '.', 'a b', "'CONS", '"CONS"', ''):
            z = module.propose(token, [('CONS', '100')]); self.assertEqual(z['status'], 'BLOCKED-SURFACE', token)
        self.assertEqual(module.propose('CONS', [('CONS', '100'), ('CONS', '100')])['status'], 'EXACT')

    def test_unicode_and_no_auto_execute(self):
        z = module.propose('сандх', [('сандхі','1010101')]); self.assertEqual(z['status'], 'SUGGEST')
        c = [('сандхі','1010101')]; module.propose('сандх', c); self.assertEqual(c, [('сандхі','1010101')])

    def test_numeric_limits_and_bad_candidates_fail_closed(self):
        for limit in (-1, 3, 1.0, True, None):
            with self.assertRaises(ValueError): module.propose('AB', [('ABC','010')], limit=limit)
        for table in ([[('abc','notbits')][0]], [('abc','100'), ('xyz','100')], [('()', '100')]):
            with self.assertRaises(ValueError): module.propose('abc', table)
        self.assertEqual(module.propose('XYZ', [('CONS','100')])['status'], 'ABSENT')

    def test_research_gate_mutations(self):
        ledger = json.loads((ROOT/'knowledge/d10-interlisp-dwim-safe-suggestion-v1.json').read_text())
        self.assertEqual(module.validate_dossier(ledger)['selected'], 0)
        for field, val in [('coordinate','0000000001'), ('selected',True), ('ratified',True), ('physical_t5_authorized',True), ('automatic_rewrite_authorized',True), ('automatic_execute_authorized',True)]:
            x=copy.deepcopy(ledger); x['candidate'][field]=val
            with self.subTest(field=field), self.assertRaises(AssertionError): module.validate_dossier(x)
        x=copy.deepcopy(ledger); x['status']='SELECTED'
        with self.assertRaises(AssertionError): module.validate_dossier(x)

    def test_real_semantic_overlap_blocks(self):
        ledger=json.loads((ROOT/'knowledge/d10-interlisp-dwim-safe-suggestion-v1.json').read_text())
        foundation={'domains': {'D9': {'residents': {'0001': 'UNIQUE-SURFACE-CORRECTION-SUGGESTION'}}}}
        inv={'rows': [{'semantic_name':'SOME'}], 'accounting': {'selected_semantic_candidates':1,'ratified_d10_residents':0}}
        with self.assertRaises(AssertionError): module.validate_dossier(ledger,foundation,inv)
        foundation['domains']['D9']['residents']={'0001':'UNIFY'}
        inv['rows'][0]['semantic_name']='UNIQUE-SURFACE-CORRECTION-SUGGESTION'
        with self.assertRaises(AssertionError): module.validate_dossier(ledger,foundation,inv)


if __name__ == '__main__': unittest.main()
