"""Negative-gate regressions: no assertions may be silently optimized away."""
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'scripts/d10_mechanical_filter.py'
spec = importlib.util.spec_from_file_location('d10_mechanical_filter', MODULE)
filter_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filter_mod)

class FilterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        k = self.root / 'knowledge'
        k.mkdir()
        (k / 'd1-d9-foundation.json').write_text('{}')
        inventory = {'width': 10, 'capacity': 1024, 'rows': [
            {'coordinate': '0'*10, 'stable_id': 'occupied'}]}
        data = (json.dumps(inventory) + '\n').encode()
        (k / 'd10-test.json').write_bytes(data)
        ptr = {'canonical_current': {'path': 'knowledge/d10-test.json', 'git_blob': filter_mod.git_blob(data)}}
        (k / 'd10-current-inventory.json').write_text(json.dumps(ptr))
        donor = k / 'source.json'
        donor.write_text('{"law": 1}\n')
        self.row = dict.fromkeys(filter_mod.COLUMNS, '')
        self.row.update(candidate_id='test.one', semantic_name='TEST', semantic_law='input->output',
                        donor_provenance='knowledge/source.json:1', source_pin=filter_mod.git_blob(donor.read_bytes()),
                        ratification_state='UNRATIFIED')
        self.inv_sha = ptr['canonical_current']['git_blob']
        self.foundation_sha = filter_mod.git_blob((k / 'd1-d9-foundation.json').read_bytes())
        self.coords = {'0'*10: 'occupied'}

    def put_proof(self, name, obj):
        raw = json.dumps(obj, sort_keys=True).encode()
        (self.root / name).write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def set_valid_witness(self):
        self.row['witness_command'] = 'python oracle.py'
        self.row['witness_artifact'] = 'witness.json'
        self.row['witness_sha'] = self.put_proof('witness.json', {
            'candidate_id': 'test.one', 'source_pin': self.row['source_pin'],
            'command': 'python oracle.py', 'exit_code': 0,
            'positive': 'PASS', 'negative': 'PASS'})
        self.row['witness_exit_status'] = '0'
        self.row['witness_verdict'] = 'PASS'

    def set_valid_dedup(self, outcome='DISTINCT', target=None):
        cert = {'candidate_id': 'test.one', 'inventory_sha': self.inv_sha,
                'foundation_sha': self.foundation_sha, 'd1_d9_checked': True,
                'selected_d10_checked': True, 'comparison_evidence': ['tested observable outputs'],
                'outcome': outcome}
        if target:
            cert['duplicate_target'] = target
            self.row['duplicate_target'] = target
        digest = self.put_proof('cert.json', cert)
        self.row['semantic_dedup_certificate'] = 'cert.json#sha256=' + digest

    def result(self):
        return filter_mod.evaluate(self.row, self.root, self.inv_sha, self.foundation_sha, self.coords)

    def test_provenance_gate(self):
        self.row['source_pin'] = '1'*40
        self.assertEqual('HOLD_UNVERIFIED_PIN', self.result()['reason'])

    def test_witness_exists_but_not_run(self):
        self.row['witness_artifact'] = 'witness.json'
        self.assertEqual('HOLD_NOT_RUN', self.result()['reason'])

    def test_failed_witness(self):
        self.set_valid_witness()
        data = json.loads((self.root / 'witness.json').read_text())
        data['negative'] = 'FAIL'
        self.row['witness_sha'] = self.put_proof('witness.json', data)
        self.assertEqual('REJECT_FAILED_WITNESS', self.result()['reason'])

    def test_semantic_dedup_hold_is_not_accepted(self):
        self.set_valid_witness()
        self.assertEqual('HOLD_DEDUP_UNPROVEN', self.result()['reason'])

    def test_distinct_can_reach_review_queue(self):
        self.set_valid_witness()
        self.set_valid_dedup()
        self.assertEqual('accepted', self.result()['decision'])

    def test_semantic_duplicate_has_target(self):
        self.set_valid_witness()
        self.set_valid_dedup('DUPLICATE', 'd9.id')
        self.assertEqual('EXCLUDE_DUP', self.result()['reason'])

    def test_occupied_coordinate_is_escalated(self):
        self.set_valid_witness()
        self.set_valid_dedup()
        self.row['coordinate'] = '0'*10
        self.assertEqual('ESCALATE_OWNER_COORDINATE', self.result()['reason'])

    def test_empty_coordinate_is_not_conflict(self):
        self.set_valid_witness()
        self.set_valid_dedup()
        self.row['coordinate'] = ''
        self.assertEqual('accepted', self.result()['decision'])

    def test_bad_sha_receipt_rejected(self):
        self.set_valid_witness()
        self.set_valid_dedup()
        self.row['witness_sha'] = 'f'*64
        self.assertEqual('HOLD_NOT_RUN', self.result()['reason'])

    def test_no_lost_or_duplicate_rows(self):
        self.set_valid_witness()
        self.set_valid_dedup()
        src = self.root / 'in.tsv'
        with src.open('w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=filter_mod.COLUMNS, delimiter='\t')
            w.writeheader()
            w.writerow(self.row)
        counts = filter_mod.filter_file(self.root, src, self.root / 'out')
        self.assertEqual({'accepted': 1, 'rejected': 0, 'escalated': 0}, counts)
        with src.open('a') as fh:
            fh.write('\t'.join(self.row.get(k, '') for k in filter_mod.COLUMNS) + '\n')
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_OR_MISSING'):
            filter_mod.filter_file(self.root, src, self.root / 'out')

if __name__ == '__main__':
    unittest.main()
