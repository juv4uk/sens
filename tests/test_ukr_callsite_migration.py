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
        command = [sys.executable, str(SCRIPT), '--root', str(self.root), '--require-full']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(m['active_compact_only_head_sites'], 1)

    def test_archival_latin_and_unparsed_files_are_reported_but_not_a_live_migration_red(self):
        self.put('lib/app.lisp', '(локальна-функція x)\\n')
        self.put('research/domain-archive/example.lisp', '(foreign-archive-call x)\\n')
        self.put('research/domain-archive/broken.lisp', '"unterminated')
        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--root', str(self.root), '--require-full'],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = mod.measure(self.root)
        self.assertEqual(report['active_latin_heads'], 0)
        self.assertEqual(report['active_unclassified_files'], 0)
        self.assertEqual(report['archival_latin_heads'], 1)
        self.assertEqual(report['archival_unclassified_files'], 1)
        self.assertEqual(report['latin_sites'][0]['scope'], 'archive/fixture')
        self.assertEqual(report['unclassified_files'][0]['scope'], 'archive/fixture')

    def test_historical_registry_bridge_and_generated_export_are_metadata(self):
        self.row(3, '101', 'коротко', 'повне', 'equal')
        self.put('lib/surface/semantic-registry.lisp', '((legacy registry\\n')
        self.put('lib/surface/semantic-registry-experiment.lisp', '((experiment\\n')
        self.put('lib/surface/sid8-to-domain-bridge.lisp', '((bridge\\n')
        self.put('mylisp-cml-export.lisp', '"unterminated')
        report = mod.measure(self.root)
        self.assertEqual(report['active_unclassified_files'], 0)
        self.assertEqual(report['unclassified_files'], [])
        self.assertEqual(report['metadata_files_excluded'], 5)

    def test_canon_d9_witness_calls_exact_ukrainian_surfaces_and_preserves_quoted_tag(self):
        repo_root = SCRIPT.resolve().parents[1]
        source = (repo_root / "lib" / "canon.lisp").read_text(encoding="utf-8")
        forms = mod.parse(source)
        active_heads = [head.text.casefold() for head in mod.candidate_heads(forms)]
        migrated = {
            "canon-law-result", "canon-law-satisfied", "canon-law-violated",
            "canon-law-status", "canon-conformance-result", "canon-conformance-from",
            "canon-law-empty-list", "canon-law-atom-cons", "canon-law-car-cons",
            "canon-law-cdr-cons", "canon-law-eq-reflexive-atom", "canon-law-cdr-dotted",
            "canon-law-cdr-proper", "canon-law-cdr-improper",
            "canon-law-quote-suppresses-evaluation",
            "canon-law-cond-first-match-short-circuit", "canon-law-symbolic-surface",
        }
        self.assertEqual(sorted(migrated.intersection(active_heads)), [])
        self.assertIn("(001 canon-law-result)", source)  # inert result tag, not a call
        self.assertIn("(0011 canon-law-result", source)  # definition spelling kept as compatibility evidence

        index, _ = mod.peer_index(repo_root)
        exact = {
            "канон-закон-результат": "D9:001110101",
            "канон-закон-виконаний": "D9:101000100",
            "канон-закон-порушений": "D9:001010111",
            "канон-закон-стан": "D9:001000010",
            "канон-відповідність-результат": "D9:010011011",
            "канон-відповідність-з": "D9:010010100",
            "канон-порожній-список": "D9:001111001",
            "канон-закон-порожній-список": "D9:010111011",
            "канон-закон-атом-пара": "D9:010000111",
            "канон-закон-перше-пара": "D9:010011100",
            "канон-закон-решта-пара": "D9:001000110",
            "канон-закон-рівність-рефлексивний-атом": "D9:001110010",
            "канон-закон-решта-крапковий": "D9:010110001",
            "канон-закон-решта-правильний": "D9:010000000",
            "канон-закон-решта-неправильний": "D9:001110110",
            "канон-закон-цитування-пригнічує-обчислення": "D9:010111100",
            "канон-закон-умова-перший-збіг-короткий-ланцюг": "D9:010101100",
            "канон-закон-символьний-поверхня": "D9:001111000",
            "канон-відповідає?": "D9:010111110",
        }
        for surface, identity in exact.items():
            self.assertEqual(index.get(surface), [identity], surface)
        sentinel = "ніколи-не-визначений-канон-предикат"
        self.assertIn(sentinel, active_heads)
        self.assertIsNone(index.get(sentinel), "negative sentinel must not gain a D1–D10 identity")
        self.assertNotIn("never-defined-canon-predicate", source)
        self.assertIn("(ніколи-не-визначений-канон-предикат)", source)
        expected_live_heads = {
            "канон-закон-результат", "канон-закон-виконаний",
            "канон-закон-порушений", "канон-закон-стан",
            "канон-відповідність-результат", "канон-відповідність-з",
            "канон-закон-порожній-список", "канон-закон-атом-пара",
            "канон-закон-перше-пара", "канон-закон-решта-пара",
        }
        self.assertTrue(expected_live_heads.issubset(set(active_heads)),
                        sorted(expected_live_heads.difference(active_heads)))

    def test_latin_executable_call_has_exact_file_line_and_known_identity(self):
        self.row(3, '101', 'коротко', 'повне', 'equal')
        self.put('lib/program.lisp', '; (equal а б)\n(повне а б)\n(equal а б)\n')
        m = mod.measure(self.root)
        self.assertEqual(m['ukr_call_heads'], 1)
        self.assertEqual(m['latin_call_heads'], 1)
        self.assertEqual(m['latin_sites'][0], {
            'file': 'lib/program.lisp', 'line': 3, 'column': 2,
            'head': 'equal', 'identities': ['D3:101'], 'mapping': 'unique',
            'scope': 'active'
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

    def test_encoded_head_is_not_mislabeled_as_latin_call(self):
        self.put('lib/encoded.lisp', '(#d1:1 (українська))\n')
        m = mod.measure(self.root)
        self.assertEqual(m['latin_call_heads'], 0)
        self.assertEqual([x['head'] for x in m['encoded_head_sites']], ['#d1:1'])
        p = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                            '--require-full'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn('1 active encoded heads', p.stderr)

    def test_distinguishes_compact_only_full_and_local_cyrillic(self):
        self.row(3, '101', 'коротко', 'повна-назва', 'equal')
        self.put('lib/live.lisp', '(коротко а)\n(повна-назва а)\n(власна-функція а)\n')
        m = mod.measure(self.root)
        self.assertEqual(m['ukr_full_head_sites'], 1)
        self.assertEqual(m['uk_compact_only_head_sites'], 1)
        self.assertEqual(m['local_cyrillic_head_sites'], 1)
        self.assertEqual(m['ambiguous_cyrillic_head_sites'], 0)
        self.assertEqual(m['latin_call_heads'], 0)
        p = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                            '--require-full'], capture_output=True, text=True)
        # A valid short Ukrainian peer is not a migration defect.
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn('::error::', p.stderr)

    def test_archive_latin_is_not_mislabeled_active(self):
        self.put('research/old.lisp', '(historic-call x)\n')
        self.put('lib/active.lisp', '(current-call x)\n')
        m = mod.measure(self.root)
        self.assertEqual(m['archival_latin_heads'], 1)
        self.assertEqual([x['scope'] for x in m['latin_sites']],
                         ['active', 'archive/fixture'])

    def test_empty_or_metadata_only_tree_cannot_pass_full_migration(self):
        self.row(3, '101', 'коротко', 'розгорнуте', 'equal')
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                                 '--require-full'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('0 active Latin call heads', result.stderr)


class PersistentMapLifeUkrWitnessTests(unittest.TestCase):
    """Перевірка проєкції саме виконуваних голів без семантичного Python-оракула."""

    def test_current_d3_d4_authority_and_two_live_libraries(self):
        root = Path(__file__).resolve().parents[1]
        peers = (
            (3, "001", "як-є"),
            (3, "010", "атом?"),
            (3, "011", "решта"),
            (3, "100", "перше"),
            (3, "101", "тотожне?"),
            (3, "110", "за-умовою"),
            (3, "111", "сполучити"),
            (4, "0010", "функція"),
            (4, "0100", "хибне?"),
            (4, "0101", "порожній?"),
            (4, "1110", "список"),
        )
        for width, bits, spelling in peers:
            with self.subTest(domain=f"D{width}", bits=bits):
                lines = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8").splitlines()
                matches = [line for line in lines if line.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(matches), 1)
                self.assertIn(f"(укр {spelling})", matches[0])

        examples = {
            "lib/persistent-map.lisp": (
                "за-умовою", "порожній?", "тотожне?", "сполучити", "перше", "решта",
            ),
            "lib/life-1-scheduler.lisp": (
                "за-умовою", "атом?", "тотожне?", "сполучити", "хибне?", "як-є",
            ),
        }
        for name, required in examples.items():
            with self.subTest(path=name):
                src = (root / name).read_text(encoding="utf-8")
                heads = [x.text for x in mod.candidate_heads(mod.parse(src))]
                for spelling in required:
                    self.assertIn(spelling, heads, (name, spelling))

    def test_quote_data_and_exact_d1_are_not_coerced_into_calls(self):
        root = Path(__file__).resolve().parents[1]
        map_source = (root / "lib/persistent-map.lisp").read_text(encoding="utf-8")
        life_source = (root / "lib/life-1-scheduler.lisp").read_text(encoding="utf-8")
        self.assertIn("(як-є (scheduler-selection none))", life_source)
        self.assertIn("(як-є producer)", life_source)
        self.assertIn("#d1:1", map_source)
        self.assertIn("#d1:0", life_source)
        sample = "(як-є (100 цитоване)) (сполучити (як-є ліве) (як-є ()))"
        heads = [x.text for x in mod.candidate_heads(mod.parse(sample))]
        self.assertNotIn("100", heads)
        self.assertIn("сполучити", heads)


class MetaEvaluatorUkrProjectionTests(unittest.TestCase):
    """Source-only peer identities; native SENS law witnesses stay independent."""

    def test_current_d3_d4_peers_in_both_meta_evaluators(self):
        root = Path(__file__).resolve().parents[1]
        peers = (
            (3, "001", "як-є"), (3, "010", "атом?"),
            (3, "011", "решта"), (3, "100", "перше"),
            (3, "101", "тотожне?"), (3, "110", "за-умовою"),
            (3, "111", "сполучити"), (4, "0010", "функція"),
            (4, "1001", "друге"), (4, "1110", "список"),
        )
        for width, bits, ukr in peers:
            with self.subTest(width=width, bits=bits):
                table = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8")
                row = [ln for ln in table.splitlines() if ln.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(row), 1)
                self.assertIn(f"(укр {ukr})", row[0])

        examples = {
            "lib/meta-eval-first-class.lisp": (
                "сполучити", "як-є", "тотожне?", "перше", "решта", "функція",
            ),
            "lib/meta-eval-mutual.lisp": (
                "за-умовою", "як-є", "тотожне?", "перше", "решта", "функція",
            ),
        }
        for path, required in examples.items():
            with self.subTest(path=path):
                src = (root / path).read_text(encoding="utf-8")
                calls = [node.text for node in mod.candidate_heads(mod.parse(src))]
                for spelling in required:
                    self.assertIn(spelling, calls, (path, spelling))

    def test_quoted_code_data_and_explicit_d1_remain_separate(self):
        root = Path(__file__).resolve().parents[1]
        first = (root / "lib/meta-eval-first-class.lisp").read_text(encoding="utf-8")
        mutual = (root / "lib/meta-eval-mutual.lisp").read_text(encoding="utf-8")
        self.assertIn("(сполучити (як-є atom) (my-fc-primitive (як-є atom)))", first)
        self.assertIn("(тотожне? (перше form) (як-є def))", mutual)
        self.assertIn("#d1:1", first)
        self.assertIn("#d1:0", mutual)
        self.assertIn("(0011 my-fc-env-lookup", first)
        self.assertIn("(0011 my-group-eval", mutual)
        # Negative witness: numeric operator behind QUOTE remains data, not callable.
        sample = "(як-є (100 quoted)) (сполучити (як-є datum) (перше xs))"
        heads = [x.text for x in mod.candidate_heads(mod.parse(sample))]
        self.assertNotIn("100", heads)
        self.assertIn("сполучити", heads)
        self.assertIn("перше", heads)


if __name__ == '__main__':
    unittest.main(verbosity=2)
