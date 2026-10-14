"""CI_GLUE_NO_SEMANTICS: test transaction mechanics only, NEVER SENS semantics.

The two temporary executables below are intentionally FAKE. They test
refusal to publish without externally produced, pinned receipts; they do
not constitute a SENS semantic witness.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from argparse import Namespace

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'verify-zig-publication.py'
spec = importlib.util.spec_from_file_location('publication_gate', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

GOOD_BYTES = bytes.fromhex('638906a1')


def digest(data):
    return hashlib.sha256(data).hexdigest()


RUNNER = '''#!/usr/bin/env python3
import sys
from pathlib import Path
cmd = sys.argv[1]
if cmd == 'backend':
    print('transport=zig abi=2 semantic_authority=SENS')
elif cmd == 'open':
    if Path(sys.argv[2]).read_bytes() != bytes.fromhex('638906a1'):
        raise SystemExit(1)
    print('10 001 00 000 01')
elif cmd == 'encode':
    path = Path(sys.argv[2])
    if path.read_text() != '10 001 00 000 01\\n':
        raise SystemExit(1)
    path.with_suffix('.sens').write_bytes(bytes.fromhex('638906a1'))
else:
    raise SystemExit(2)
'''

EXECUTOR = '''#!/usr/bin/env python3
from pathlib import Path
import sys
if Path(sys.argv[1]).read_bytes() != bytes.fromhex('638906a1'):
    raise SystemExit(1)
sys.stdout.write('1\\n')
'''


class PublicationGateMechanicalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source_file = self.root / 'original.lisp'
        self.source_file.write_bytes(b'original-source')
        self.source = self.root / 'original.sens'
        self.source.write_bytes(GOOD_BYTES)
        self.runner = self.root / 'runner'
        self.runner.write_text(RUNNER)
        self.runner.chmod(0o700)
        self.executor = self.root / 'native'
        self.executor.write_text(EXECUTOR)
        self.executor.chmod(0o700)
        self.provenance = self.root / 'provenance.json'
        self.record = {
            'schema': 'sens-publication-provenance/v1',
            'source_era': 'current',
            'source_sha256': digest(self.source_file.read_bytes()),
            'physical_sha256': digest(GOOD_BYTES),
            'semantic_oracle': 'NOT_VERIFIED',
        }
        self.save_provenance()
        self.args = Namespace(
            input=self.source, source_file=self.source_file,
            out=self.root / 'public.sens', provenance=self.provenance,
            zig_runner=self.runner, zig_runner_sha256=digest(self.runner.read_bytes()),
            sens_executor=self.executor, sens_executor_sha256=digest(self.executor.read_bytes()),
            expected_output_sha256=digest(b'1\n'),
            _provenance_snapshot=self.provenance.read_bytes(),
        )

    def save_provenance(self):
        self.provenance.write_text(json.dumps(self.record))

    def check_reject(self, phrase):
        with self.assertRaises(mod.PublicationRejected) as ctx:
            mod.verify_and_publish(self.args)
        self.assertIn(phrase, str(ctx.exception))
        self.assertFalse(self.args.out.exists(), 'no rejected artifact may be published')

    def test_positive_cycle_then_no_overwrite(self):
        result = mod.verify_and_publish(self.args)
        self.assertEqual(result['physical'], 'PASS')
        self.assertEqual(result['native_sens_execution'], 'PASS')
        self.assertEqual(self.args.out.read_bytes(), GOOD_BYTES)
        with self.assertRaisesRegex(mod.PublicationRejected, 'exists'):
            mod.verify_and_publish(self.args)

    def test_ambiguous_era_rejected(self):
        self.record['source_era'] = 'auto'
        self.save_provenance()
        self.args._provenance_snapshot = self.provenance.read_bytes()
        self.check_reject('explicit current/legacy')

    def test_wrong_digest_rejected(self):
        self.record['physical_sha256'] = digest(b'wrong')
        self.save_provenance()
        self.args._provenance_snapshot = self.provenance.read_bytes()
        self.check_reject('differs from provenance')

    def test_unpinned_runner_rejected(self):
        self.args.zig_runner_sha256 = digest(b'wrong')
        self.check_reject('executable SHA256 mismatch')

    def test_wrong_native_result_rejected(self):
        self.args.expected_output_sha256 = digest(b'wrong')
        self.check_reject('SENS native verdict mismatch')

    def test_mutated_carrier_rejected(self):
        altered = bytes.fromhex('638906a0')
        self.source.write_bytes(altered)
        self.record['physical_sha256'] = digest(altered)
        self.save_provenance()
        self.args._provenance_snapshot = self.provenance.read_bytes()
        self.check_reject('rejected')


if __name__ == '__main__':
    unittest.main()
