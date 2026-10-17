"""Negative and positive witnesses for the static Ukrainian call-site audit.

These tests use their own temporary roots; they NEVER rewrite project Lisp.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check_ukr_callsite_migration.py'
_spec = importlib.util.spec_from_file_location('check_ukr_callsite_migration', SCRIPT)
mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = mod
_spec.loader.exec_module(mod)


class CallsiteAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def row(self, d: int, bits: str, uk: str, ukr: str, en: str):
        return self.put(f'lib/domains/d{d}.lisp',
                        f'({bits} (ук {uk}) (укр {ukr}) (san ()) '
                        f'(en {en}) (LISP {en.upper()}) (sym ()))\n')

    def test_compact_and_full_peer_can_differ_with_exact_same_identity(self):
        self.row(3, '101', 'коротко', 'повне-українське-імя', 'equal')
        self.put('lib/app.lisp', '(повне-українське-імя а б)\n(коротко а б)\n')
        m = mod.measure(self.root)
        self.assertEqual(m['peer_index']['valid_distinct_peer_spellings'], 1)
        self.assertEqual(m['ukr_call_heads'], 2)
        self.assertEqual(m['latin_call_heads'], 0)
        idx, _ = mod.peer_index(self.root)
        self.assertEqual(idx['коротко'], ['D3:101'])
        self.assertEqual(idx['повне-українське-імя'], ['D3:101'])
        self.assertEqual(idx['equal'], ['D3:101'])

    def test_latin_executable_call_has_exact_file_line_and_known_identity(self):
        self.row(3, '101', 'коротко', 'повне', 'equal')
        self.put('lib/program.lisp', '; (equal а б)\n(повне а б)\n(equal а б)\n')
        m = mod.measure(self.root)
        self.assertEqual(m['ukr_call_heads'], 1)
        self.assertEqual(m['latin_call_heads'], 1)
        self.assertEqual(m['latin_sites'][0], {
            'file': 'lib/program.lisp', 'line': 3, 'column': 2,
            'head': 'equal', 'identities': ['D3:101'], 'mapping': 'unique'
        })

    def test_quotes_comments_strings_and_formals_not_false_calls(self):
        self.put('lib/program.lisp', '''; (unused)
"(hidden foo)"
'(quoted-call (other))
(quote (also-quoted bar))
(001 (quoted-in-binary baz))
(0011 визначення (0010 (fake-formal) (реальне fake-argument)))
(визначити x (функція (param-name) (виконати param-name)))
#| (block-one)
   #| (block-two) |#
|#
''')
        m = mod.measure(self.root)
        self.assertEqual(m['latin_call_heads'], 0, m['latin_sites'])
        self.assertEqual(m['ukr_call_heads'], 4)
        self.assertEqual(m['unclassified_files'], [])

    def test_quasiquote_unquote_executes_only_unquoted_subtree(self):
        self.put('lib/q.lisp', chr(96) + '(data (no-call a) ,(actual-call b))\n')
        m = mod.measure(self.root)
        self.assertEqual([s['head'] for s in m['latin_sites']], ['actual-call'])

    def test_symbol_or_raw_token_inside_string_cannot_inject_fake_call(self):
        self.put('lib/s.lisp', '"(ukr ((english)))"\n; (latin)\n(дійсне "(latin)")\n')
        self.assertEqual(mod.measure(self.root)['latin_call_heads'], 0)

    def test_domain_rows_and_registry_are_metadata_not_latin_calls(self):
        self.row(3, '101', 'коротко', 'розгорнуте', 'equal')
        self.put('lib/surface/semantic-registry.lisp',
                 '((00000001 (en equal) (ук коротко) (укр розгорнуте) (sa ())))\n')
        m = mod.measure(self.root)
        self.assertEqual(m['metadata_files_excluded'], 2)
        self.assertEqual(m['latin_call_heads'], 0)

    def test_ambiguous_spelling_is_not_rewritten_or_assumed_unique(self):
        self.row(3, '101', 'назва', 'спільна', 'equal')
        self.row(4, '0001', 'інше', 'спільна', 'eval')
        self.put('lib/calls.lisp', '(equal x y)\n')
        m = mod.measure(self.root)
        self.assertEqual(m['peer_index']['ambiguous_names'], 1)
        self.assertEqual(m['latin_sites'][0]['mapping'], 'unique')
        index, _ = mod.peer_index(self.root)
        self.assertEqual(index['спільна'], ['D3:101', 'D4:0001'])

    def test_unknown_latin_head_fails_closed_with_unresolved_mapping(self):
        self.put('lib/app.lisp', '(unknown-foreign-call a b)\n')
        m = mod.measure(self.root)
        self.assertEqual(m['latin_sites'][0]['mapping'], 'unresolved')

    def test_bad_syntax_is_unclassified_not_silently_green(self):
        self.put('lib/app.lisp', '(виклик (незакритий)\n')
        m = mod.measure(self.root)
        self.assertEqual(len(m['unclassified_files']), 1)
        self.assertIn('unclosed list', m['unclassified_files'][0]['reason'])

    def test_unclosed_string_and_nested_block_comment_are_fail_closed(self):
        self.put('lib/app.lisp', '#| outer #| inner |# still outer\n')
        m = mod.measure(self.root)
        self.assertEqual(len(m['unclassified_files']), 1)
        self.assertIn('unclosed block comment', m['unclassified_files'][0]['reason'])
        self.put('lib/app.lisp', '"unterminated')
        self.assertIn('unclosed string', mod.measure(self.root)['unclassified_files'][0]['reason'])

    def test_cli_red_green_no_write_json_and_determinism(self):
        source = self.put('lib/app.lisp', '(повне x)\n(foreign-head y)\n')
        original = source.read_bytes()
        out = self.root / 'report.json'
        command = [sys.executable, str(SCRIPT), '--root', str(self.root),
                   '--require-full', '--json', str(out)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('::error::', result.stderr)
        self.assertEqual(source.read_bytes(), original)
        first = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(first['latin_sites'][0]['head'], 'foreign-head')
        self.assertEqual(first, mod.measure(self.root))
        source.write_text('(повне x)\n', encoding='utf-8')
        passed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0, passed.stderr)

    def test_symlink_to_external_file_is_unclassified_never_followed(self):
        foreign = self.put('outside.lisp', '(foreign-head x)\n')
        sub = self.root / 'lib'
        sub.mkdir(parents=True, exist_ok=True)
        (sub / 'linked.lisp').symlink_to(foreign)
        m = mod.measure(self.root)
        self.assertEqual(len(m['unclassified_files']), 1)
        self.assertIn('symlink', m['unclassified_files'][0]['reason'])

    def test_empty_or_metadata_only_tree_cannot_pass_full_migration(self):
        self.row(3, '101', 'коротко', 'розгорнуте', 'equal')
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                                 '--require-full'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('0 Latin call heads', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
