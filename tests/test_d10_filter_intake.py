#!/usr/bin/env python3
"""Strict negative regression probes for the D10 intake partitioner."""
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT.parent / 'scripts' / 'd10_filter_intake.py'
spec = importlib.util.spec_from_file_location('d10_filter_intake', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class D10FilterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.commit = 'a' * 40
        self.provenance = f'juv4uk/sens@{self.commit}:lib/historical.lisp:11'
        self.row = dict.fromkeys(mod.INPUT, '')
        self.row.update(candidate_id='D10P-TEST', semantic_name='EXAMPLE',
                        semantic_law='test law', donor_provenance=self.provenance,
                        witness_result_ref='witness.log', source_refs=self.provenance,
                        requested_coordinate='NONE')
        self.record = {}

    def proof(self, name):
        data = name.encode()
        (self.root / name).write_bytes(data)
        return {'verified': True, 'artifact': name,
                'sha256': hashlib.sha256(data).hexdigest()}

    def prime(self):
        self.record['provenance'] = dict(self.proof('source.proof'),
                                         source_ref=self.provenance,
                                         content_sha256=hashlib.sha256(b'donor bytes').hexdigest())
        self.record['witness'] = dict(self.proof('witness.log'),
                                      source_ref=self.provenance, run_commit=self.commit,
                                      result='PASS', exit_code=0, positive_pass=True,
                                      negative_pass=True, oracle_pass=True,
                                      run_url='https://github.com/juv4uk/sens/actions/runs/1',
                                      tool_version='test-oracle-1')
        self.record['semantic'] = dict(self.proof('semantic.proof'),
                                       classification='distinct', counterexample_checked=True,
                                       lower_domain_review=True, current_d10_review=True)
        self.record['conflict'] = dict(self.proof('conflict.proof'), status='none')

    def status(self):
        return mod.classify(self.row, self.record, self.root)['status']

    def test_no_evidence_rejected(self):
        self.assertEqual(self.status(), 'EXCLUDE_NO_PROVENANCE')

    def test_witness_is_not_just_a_pass_string(self):
        self.prime()
        self.record['witness'].pop('negative_pass')
        self.assertEqual(self.status(), 'EXCLUDE_NO_WITNESS')

    def test_wrong_witness_commit_rejected(self):
        self.prime()
        self.record['witness']['run_commit'] = 'b' * 40
        self.assertEqual(self.status(), 'EXCLUDE_NO_WITNESS')

    def test_witness_log_tamper_rejected(self):
        self.prime()
        (self.root / 'witness.log').write_bytes(b'tampered')
        self.assertEqual(self.status(), 'EXCLUDE_NO_WITNESS')

    def test_semantic_uncertain_not_duplicate(self):
        self.prime()
        self.record['semantic']['classification'] = 'unknown'
        self.assertEqual(self.status(), 'EXCLUDE_UNPROVEN_DISTINCTNESS')

    def test_proven_duplicate_needs_target(self):
        self.prime()
        self.record['semantic'].update(classification='duplicate', bidirectional=True)
        self.assertEqual(self.status(), 'EXCLUDE_UNPROVEN_DISTINCTNESS')
        self.record['semantic']['duplicate_of'] = 'D9:001001'
        self.assertEqual(self.status(), 'EXCLUDE_DUP')

    def test_real_coordinate_request_escalates(self):
        self.prime()
        self.row['requested_coordinate'] = '1010101010'
        self.assertEqual(self.status(), 'ESCALATE_OWNER')

    def test_clean_record_is_review_only(self):
        self.prime()
        self.assertEqual(self.status(), 'ACCEPT_PENDING_BULK_APPROVAL')

    def test_runner_preserves_rows_and_does_not_claim_bulk(self):
        self.prime()
        input_path = self.root / 'all-candidates.tsv'
        with input_path.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=mod.INPUT, delimiter='\t')
            w.writeheader()
            w.writerow(self.row)
        (self.root / 'evidence.json').write_text(json.dumps({self.row['candidate_id']: self.record}))
        (self.root / 'census.json').write_text(json.dumps({
            'coverage_complete': True, 'source_manifest_verified': True,
            'unreadable_sources': 0, 'candidate_count': 1}))
        cmd = [sys.executable, str(SCRIPT), '--input', str(input_path),
               '--evidence', str(self.root/'evidence.json'),
               '--census', str(self.root/'census.json'),
               '--evidence-root', str(self.root), '--out-dir', str(self.root/'out')]
        for flags in ([], ['-O']):
            process = subprocess.run([sys.executable, *flags, *cmd[1:]],
                                     capture_output=True, text=True, check=False)
            self.assertEqual(process.returncode, 0, process.stderr)
            report = json.loads(process.stdout)
            self.assertEqual((report['accepted'], report['rejected'], report['escalated']), (1,0,0))
            self.assertFalse(report['bulk_ready'])
        with input_path.open('a', encoding='utf-8') as f:
            f.write('\t'.join(self.row[x] for x in mod.INPUT) + '\n')
        process = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(process.returncode, 2, process.stdout)
        self.assertIn('duplicate candidate_id', process.stderr)


if __name__ == '__main__':
    unittest.main()
