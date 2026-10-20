"""Negative and positive witnesses for the static Ukrainian call-site audit.

These tests use their own temporary roots; they NEVER rewrite project Lisp.
"""
from __future__ import annotations

import importlib.util
from collections import Counter
import hashlib
import json
import re
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
        self.put('mylisp-cml-export.lisp', '"unterminated')
        report = mod.measure(self.root)
        self.assertEqual(report['active_unclassified_files'], 0)
        self.assertEqual(report['unclassified_files'], [])
        self.assertEqual(report['metadata_files_excluded'], 4)

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
        self.assertIn("(як-є canon-law-result)", source)  # D3:001 українська проєкція; цитований тег, не виклик
        self.assertIn("(визначити канон-закон-результат", source)
        self.assertNotRegex(source, r"\(визначити canon-[a-z-]+\b")

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
        self.assertIn("(так", map_source)
        self.assertNotIn("#d1:0", life_source)
        self.assertIn("(нехай-послідовно ", life_source)
        self.assertIn("(так ні)", life_source)
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
        self.assertIn("(сполучити (як-є атом?) (першокласний-примітив (як-є атом?)))", first)
        self.assertIn("(тотожне? (перше форма) (як-є визначити))", mutual)
        # Джерело зберігає історичний #d1:1 у коментарі; заборона діє
        # лише для виконуваного SENS-коду, а не для provenance.
        active_first = "\n".join(
            line.split(";", 1)[0] for line in first.splitlines()
        )
        self.assertNotIn("#d1:1", active_first)
        self.assertNotIn("#d1:0", active_first)
        self.assertIn("(так ", active_first)
        # Поточна ратифікована D1 проєкція: D1:0 = «ні», D1:1 = «так».
        # Meta-mutual і first-class використовують повну ратифіковану D1-проєкцію.
        d1 = (root / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        self.assertIn("(0 (ук ні) (укр ні)", d1)
        self.assertIn("(1 (ук так) (укр так)", d1)
        self.assertIn("((атом? значення) ні)", mutual)
        self.assertIn("(так (тотожне? (перше значення) назва-замикання-рекурсивної-групи))", mutual)
        self.assertNotIn("#d1:0", mutual)
        self.assertIn("(визначити першокласне-знайти-в-середовищі", first)
        self.assertNotIn("(0011 першокласне-знайти-в-середовищі", first)
        self.assertIn("(визначити обчислити-вираз-групи", mutual)
        # Negative witness: numeric operator behind QUOTE remains data, not callable.
        sample = "(як-є (100 quoted)) (сполучити (як-є datum) (перше xs))"
        heads = [x.text for x in mod.candidate_heads(mod.parse(sample))]
        self.assertNotIn("100", heads)
        self.assertIn("сполучити", heads)
        self.assertIn("перше", heads)


    def test_first_class_source_is_current_ukrainian_not_historical_sid8(self):
        current_src = (Path(__file__).resolve().parents[1] / "lib/meta-eval-first-class.lisp").read_text(encoding="utf-8")
        self.assertTrue(current_src.startswith("; Першокласні функції: експериментальний метаобчислювач"))
        active = "\n".join(line.split(";", 1)[0] for line in current_src.splitlines())
        self.assertNotIn("#d1:", active)
        self.assertNotRegex(active, r"(?m)^\s*\([01]{3,9}\s")
        for head in ("визначити", "функція", "як-є", "за-умовою",
                     "першокласне-застосувати", "першокласне-обчислити"):
            self.assertIn(head, active)
        for old in ("my-fc-eval", "my-fc-apply", "my-eval-first-class", "SID8", "Sens8"):
            self.assertNotIn(old, active)


class NativeFirstUkrProjectionTests(unittest.TestCase):
    """Чинні українські джерела parity; жодного inverse до історичних SID8."""

    def test_exact_current_ukrainian_peers(self):
        root = Path(__file__).resolve().parents[1]
        for width, bits, spelling in (
            (4, "0011", "визначити"),
            (9, "110110101", "п'ятий"),
            (10, "0001100010", "входження-тотожність"),
        ):
            with self.subTest(domain=f"D{width}:{bits}"):
                data = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8")
                rows = [row for row in data.splitlines()
                        if row.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(укр {spelling})", rows[0])

    def test_parity_source_has_only_named_ukrainian_functions(self):
        root = Path(__file__).resolve().parents[1]
        parity = (root / "lib/machine/dispatch/native-first-parity.lisp").read_text(encoding="utf-8")
        heads = [token.text for token in mod.candidate_heads(mod.parse(parity))]
        for name in (
            "нативний-паритет-успіх",
            "нативний-паритет-невдача",
            "нативний-паритет-пятичленний?",
            "нативний-паритет-перевірити-випадок",
            "нативний-паритет-перевірити-корпус",
            "нативний-паритет-вердикт-успішний?",
            "нативний-паритет-усі-вердикти-успішні?",
        ):
            with self.subTest(name=name):
                self.assertIn(name, heads)
        for name in (
            "native-first-parity-pass", "native-first-parity-fail",
            "native-first-parity-case", "native-first-parity-run",
            "native-first-parity-verdict-pass?", "native-first-parity-all-pass?",
        ):
            self.assertNotIn("(визначити " + name, parity)
        self.assertNotRegex(parity, r"(?m)^\s*\([01]{3,9}\s")
        self.assertIn("(однакові? результат-обчислювача очікуване)", parity)
        self.assertIn("(однакові? результат-машини очікуваний-результат-машини)", parity)

    def test_coverage_ledger_is_still_quoted_data_with_six_rows(self):
        root = Path(__file__).resolve().parents[1]
        coverage = (root / "lib/machine/dispatch/native-first-coverage.lisp").read_text(encoding="utf-8")
        forms = mod.parse(coverage)
        self.assertEqual(len(forms), 1)
        definition = forms[0]
        self.assertEqual(mod.atom(definition.values[0]), "визначити")
        self.assertEqual(mod.atom(definition.values[1]), "журнал-нативного-покриття")
        quote_form = definition.values[2]
        self.assertEqual(mod.atom(quote_form.values[0]), "як-є")
        records = quote_form.values[1].values
        self.assertEqual(len(records), 6)
        self.assertTrue(all(mod.atom(record.values[0]) == "native-coverage" for record in records))
        statuses = []
        for record in records:
            fields = {mod.atom(field.values[0]): mod.atom(field.values[1]) for field in record.values[1:]}
            for field in ("representative", "reason", "evidence", "status"):
                self.assertIn(field, fields)
            statuses.append(fields["status"])
        self.assertCountEqual(statuses, [
            "native-supported", "fallback-required", "fallback-required",
            "blocked-runtime-prerequisite", "blocked-runtime-prerequisite",
            "blocked-runtime-prerequisite",
        ])
        self.assertIn('(representative (додати 2 3))', coverage)



class DomainLawScriptsUkrProjectionWitnessTests(unittest.TestCase):
    """Точний зворотний свідок D3/D4-проєкції, без виконання Lisp у Python."""

    PINNED = {
  "scripts/check-domain-bitness-laws.lisp": {
    "sha": "c74371a71cea008b313cdf8be85fae02d53b5705",
    "edits": [
      [
        959,
        "0011"
      ],
      [
        979,
        "0010"
      ],
      [
        1172,
        "0011"
      ],
      [
        1193,
        "0010"
      ],
      [
        1216,
        "110"
      ],
      [
        1228,
        "010"
      ],
      [
        1253,
        "010"
      ],
      [
        1258,
        "001"
      ],
      [
        1275,
        "111"
      ],
      [
        1280,
        "100"
      ],
      [
        1305,
        "011"
      ],
      [
        1329,
        "0011"
      ],
      [
        1352,
        "0010"
      ],
      [
        1515,
        "0011"
      ],
      [
        1537,
        "0010"
      ],
      [
        1560,
        "110"
      ],
      [
        1572,
        "010"
      ],
      [
        1583,
        "010"
      ],
      [
        1603,
        "010"
      ],
      [
        1615,
        "001"
      ],
      [
        1631,
        "010"
      ],
      [
        1636,
        "001"
      ],
      [
        1668,
        "011"
      ],
      [
        1679,
        "011"
      ],
      [
        1697,
        "0011"
      ],
      [
        1714,
        "0010"
      ],
      [
        1731,
        "110"
      ],
      [
        1743,
        "010"
      ],
      [
        1748,
        "011"
      ],
      [
        1760,
        "100"
      ],
      [
        1765,
        "100"
      ],
      [
        1785,
        "010"
      ],
      [
        1790,
        "001"
      ],
      [
        1810,
        "011"
      ],
      [
        1901,
        "0011"
      ],
      [
        1925,
        "0010"
      ],
      [
        1967,
        "110"
      ],
      [
        1979,
        "101"
      ],
      [
        2014,
        "001"
      ],
      [
        2030,
        "110"
      ],
      [
        2045,
        "101"
      ],
      [
        2050,
        "100"
      ],
      [
        2055,
        "100"
      ],
      [
        2084,
        "110"
      ],
      [
        2102,
        "101"
      ],
      [
        2129,
        "001"
      ],
      [
        2152,
        "010"
      ],
      [
        2157,
        "001"
      ],
      [
        2207,
        "010"
      ],
      [
        2212,
        "001"
      ],
      [
        2259,
        "010"
      ],
      [
        2264,
        "001"
      ],
      [
        2576,
        "0011"
      ],
      [
        2600,
        "0010"
      ],
      [
        2623,
        "110"
      ],
      [
        2635,
        "010"
      ],
      [
        2647,
        "010"
      ],
      [
        2652,
        "001"
      ],
      [
        2670,
        "101"
      ],
      [
        2680,
        "100"
      ],
      [
        2685,
        "100"
      ],
      [
        2699,
        "001"
      ],
      [
        2715,
        "010"
      ],
      [
        2720,
        "001"
      ],
      [
        2752,
        "011"
      ],
      [
        2770,
        "0011"
      ],
      [
        2798,
        "0010"
      ],
      [
        2816,
        "110"
      ],
      [
        2828,
        "010"
      ],
      [
        2840,
        "010"
      ],
      [
        2845,
        "001"
      ],
      [
        2880,
        "100"
      ],
      [
        2885,
        "100"
      ],
      [
        2898,
        "011"
      ],
      [
        2939,
        "011"
      ],
      [
        2960,
        "010"
      ],
      [
        2965,
        "001"
      ],
      [
        2975,
        "001"
      ],
      [
        2988,
        "0011"
      ],
      [
        3034,
        "0011"
      ],
      [
        3080,
        "0011"
      ],
      [
        3126,
        "0011"
      ],
      [
        3172,
        "0011"
      ],
      [
        3218,
        "0011"
      ],
      [
        3264,
        "0011"
      ],
      [
        3310,
        "0011"
      ],
      [
        3356,
        "0011"
      ],
      [
        3402,
        "0011"
      ],
      [
        3450,
        "0011"
      ],
      [
        3519,
        "0011"
      ],
      [
        3549,
        "0011"
      ],
      [
        3579,
        "0011"
      ],
      [
        3609,
        "0011"
      ],
      [
        3639,
        "0011"
      ],
      [
        3669,
        "0011"
      ],
      [
        3699,
        "0011"
      ],
      [
        3729,
        "0011"
      ],
      [
        3759,
        "0011"
      ],
      [
        3854,
        "0011"
      ],
      [
        3951,
        "001"
      ],
      [
        3966,
        "001"
      ],
      [
        3974,
        "001"
      ],
      [
        4000,
        "001"
      ],
      [
        4015,
        "001"
      ],
      [
        4024,
        "001"
      ],
      [
        4051,
        "001"
      ],
      [
        4066,
        "001"
      ],
      [
        4076,
        "001"
      ],
      [
        4104,
        "001"
      ],
      [
        4119,
        "001"
      ],
      [
        4130,
        "001"
      ],
      [
        4159,
        "001"
      ],
      [
        4174,
        "001"
      ],
      [
        4186,
        "001"
      ],
      [
        4216,
        "001"
      ],
      [
        4231,
        "001"
      ],
      [
        4244,
        "001"
      ],
      [
        4275,
        "001"
      ],
      [
        4290,
        "001"
      ],
      [
        4304,
        "001"
      ],
      [
        4336,
        "001"
      ],
      [
        4351,
        "001"
      ],
      [
        4366,
        "001"
      ],
      [
        4399,
        "001"
      ],
      [
        4415,
        "001"
      ],
      [
        4431,
        "001"
      ],
      [
        4448,
        "0011"
      ],
      [
        4502,
        "001"
      ],
      [
        4527,
        "001"
      ],
      [
        4544,
        "001"
      ],
      [
        4579,
        "001"
      ],
      [
        4608,
        "001"
      ],
      [
        4626,
        "001"
      ],
      [
        4826,
        "0011"
      ],
      [
        4853,
        "111"
      ],
      [
        4858,
        "100"
      ],
      [
        4871,
        "111"
      ],
      [
        4876,
        "100"
      ],
      [
        4881,
        "011"
      ],
      [
        4897,
        "111"
      ],
      [
        4902,
        "100"
      ],
      [
        4907,
        "011"
      ],
      [
        4912,
        "011"
      ],
      [
        4931,
        "111"
      ],
      [
        4936,
        "100"
      ],
      [
        4941,
        "011"
      ],
      [
        4961,
        "011"
      ],
      [
        4966,
        "011"
      ],
      [
        4971,
        "011"
      ],
      [
        4976,
        "011"
      ],
      [
        5055,
        "110"
      ],
      [
        5088,
        "001"
      ],
      [
        5101,
        "010"
      ],
      [
        5106,
        "001"
      ],
      [
        5219,
        "110"
      ],
      [
        5268,
        "110"
      ],
      [
        5279,
        "101"
      ],
      [
        5284,
        "100"
      ],
      [
        5289,
        "100"
      ],
      [
        5315,
        "001"
      ],
      [
        5332,
        "110"
      ],
      [
        5346,
        "101"
      ],
      [
        5381,
        "001"
      ],
      [
        5401,
        "110"
      ],
      [
        5418,
        "101"
      ],
      [
        5464,
        "001"
      ],
      [
        5485,
        "001"
      ],
      [
        5507,
        "010"
      ],
      [
        5512,
        "001"
      ],
      [
        5564,
        "010"
      ],
      [
        5569,
        "001"
      ],
      [
        5614,
        "010"
      ],
      [
        5619,
        "001"
      ],
      [
        5664,
        "010"
      ],
      [
        5669,
        "001"
      ],
      [
        5835,
        "110"
      ],
      [
        5843,
        "101"
      ],
      [
        5868,
        "111"
      ],
      [
        5873,
        "100"
      ],
      [
        5895,
        "001"
      ],
      [
        5907,
        "001"
      ],
      [
        5920,
        "010"
      ],
      [
        5925,
        "001"
      ]
    ],
    "changed": [
      20,
      21,
      26,
      27,
      28,
      29,
      30,
      31,
      33,
      34,
      39,
      40,
      41,
      42,
      43,
      44,
      45,
      47,
      48,
      49,
      50,
      51,
      54,
      55,
      56,
      57,
      58,
      59,
      60,
      61,
      62,
      63,
      64,
      70,
      71,
      72,
      73,
      74,
      75,
      77,
      78,
      79,
      80,
      81,
      82,
      83,
      85,
      86,
      87,
      88,
      89,
      90,
      91,
      92,
      93,
      94,
      95,
      98,
      99,
      100,
      101,
      102,
      103,
      104,
      105,
      106,
      108,
      111,
      112,
      113,
      114,
      115,
      116,
      117,
      118,
      119,
      120,
      121,
      122,
      123,
      124,
      129,
      130,
      131,
      132,
      133,
      134,
      137,
      138,
      139,
      142,
      144,
      145,
      146,
      147,
      148,
      149,
      150,
      151,
      152,
      153,
      154,
      158,
      159,
      160,
      161,
      162,
      163
    ]
  },
  "scripts/check-domain-logic-laws.lisp": {
    "sha": "7d957d241f83c89585405a5590cc7a6142eb24f5",
    "edits": [
      [
        826,
        "0011"
      ],
      [
        844,
        "0010"
      ],
      [
        864,
        "110"
      ],
      [
        879,
        "001"
      ],
      [
        932,
        "0011"
      ],
      [
        973,
        "001"
      ],
      [
        996,
        "101"
      ],
      [
        1001,
        "100"
      ],
      [
        1006,
        "111"
      ],
      [
        1011,
        "001"
      ],
      [
        1019,
        "001"
      ],
      [
        1029,
        "001"
      ],
      [
        1050,
        "001"
      ],
      [
        1073,
        "101"
      ],
      [
        1078,
        "011"
      ],
      [
        1083,
        "111"
      ],
      [
        1088,
        "001"
      ],
      [
        1096,
        "001"
      ],
      [
        1106,
        "001"
      ],
      [
        1127,
        "001"
      ],
      [
        1150,
        "010"
      ],
      [
        1155,
        "001"
      ],
      [
        1176,
        "001"
      ],
      [
        1199,
        "0100"
      ],
      [
        1205,
        "010"
      ],
      [
        1210,
        "111"
      ],
      [
        1215,
        "001"
      ],
      [
        1223,
        "001"
      ],
      [
        1246,
        "001"
      ],
      [
        1269,
        "101"
      ],
      [
        1274,
        "001"
      ],
      [
        1282,
        "001"
      ],
      [
        1303,
        "001"
      ],
      [
        1326,
        "0100"
      ],
      [
        1332,
        "101"
      ],
      [
        1337,
        "001"
      ],
      [
        1345,
        "001"
      ],
      [
        1367,
        "001"
      ],
      [
        1390,
        "0101"
      ],
      [
        1396,
        "001"
      ],
      [
        1418,
        "001"
      ],
      [
        1441,
        "101"
      ],
      [
        1446,
        "100"
      ],
      [
        1451,
        "1110"
      ],
      [
        1457,
        "001"
      ],
      [
        1465,
        "001"
      ],
      [
        1475,
        "001"
      ],
      [
        1888,
        "001"
      ],
      [
        1909,
        "101"
      ],
      [
        1914,
        "100"
      ],
      [
        1919,
        "1111"
      ],
      [
        1925,
        "001"
      ],
      [
        1934,
        "1110"
      ],
      [
        1940,
        "001"
      ],
      [
        1951,
        "001"
      ],
      [
        3107,
        "001"
      ]
    ],
    "changed": [
      18,
      19,
      20,
      21,
      24,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      34,
      45,
      46,
      70
    ]
  }
}
    ROW = __import__("re").compile(
        r"^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)"
    )

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.authority = {}
        for domain in (3, 4):
            table = (cls.root / f"lib/domains/d{domain}.lisp").read_text(encoding="utf-8")
            for line in table.splitlines():
                match = cls.ROW.match(line)
                if match and len(match[1]) == domain:
                    cls.authority[match[1]] = match[2]

    @staticmethod
    def _blob_sha(text):
        data = text.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

    @classmethod
    def _inverse(cls, current, edits):
        import re
        expected = [bits for _, bits in edits]
        masked = re.sub(
            r';[^\n]*|"(?:\\.|[^"\\])*"',
            lambda match: " " * len(match.group()),
            current,
        )
        heads = []
        cursor = 0
        for bits in expected:
            peer = cls.authority.get(bits)
            if peer is None or len(bits) not in (3, 4):
                raise AssertionError(f"Відсутня точна ратифікація {bits}")
            pattern = re.compile(r"\(\s*" + re.escape(peer) + r"(?=\s|\))")
            match = pattern.search(masked, cursor)
            if match is None:
                raise AssertionError(f"Втрачена українська проєкція {bits} після позиції {cursor}")
            pos = match.end() - len(peer)
            heads.append((pos, bits, peer))
            cursor = match.end()
        for pos, bits, peer in reversed(heads):
            if current[pos:pos + len(peer)] != peer:
                raise AssertionError(f"Неправильна проєкція {bits} at {pos}")
            current = current[:pos] + bits + current[pos + len(peer):]
        return current

    @staticmethod
    def _restore_prior_domain_logic_calls(path, source):
        """Preserve the pinned Git blob after separately verified D3/D9 and D8 migrations."""
        if path != "scripts/check-domain-logic-laws.lisp":
            return source
        new_schema = '  (тотожне? (перше (читати-всі (читати-файл "lib/domains/d1.lisp"))) (як-є domain-table/1)))'
        old_schema = '  (101 (100 (110101001 (110110111 "lib/domains/d1.lisp"))) (001 domain-table/1)))'
        if source.count(new_schema) != 1:
            raise AssertionError("Точна D3/D9 форма read-file-schema не збігається")
        source = source.replace(new_schema, old_schema, 1)
        current = '(друкувати "DOMAIN-LOGIC-LAWS: PASS'
        historical = '(11011011 "DOMAIN-LOGIC-LAWS: PASS'
        if source.count(current) != 1:
            raise AssertionError("Очікуваний точний D8-друк змінено або видалено")
        return source.replace(current, historical, 1)

    def test_source_inverse_matches_current_projection_checkpoints(self):
        for path, evidence in self.PINNED.items():
            with self.subTest(path=path):
                source = (self.root / path).read_text(encoding="utf-8")
                restored = self._inverse(source, evidence["edits"])
                restored = self._restore_prior_domain_logic_calls(path, restored)
                self.assertEqual(self._blob_sha(restored), evidence["sha"])
                mod.parse(source)
                mod.parse(restored)

    def test_changed_lines_keep_unproven_code_and_quote_data_untouched(self):
        import re
        raw_heads = re.compile(r"\(\s*[01]+(?=\s+\S)")
        for path, evidence in self.PINNED.items():
            with self.subTest(path=path):
                source = (self.root / path).read_text(encoding="utf-8")
                old = self._inverse(source, evidence["edits"])
                old = self._restore_prior_domain_logic_calls(path, old)
                before, after = old.splitlines(), source.splitlines()
                self.assertEqual(len(before), len(after))
                changed = [i + 1 for i, (a, b) in enumerate(zip(before, after)) if a != b]
                # The exact inverse hash pins every byte outside the projected heads;
                # fixed line-number lists became stale after Ukrainian comment edits.
                self.assertTrue(changed, f"{path}: projection witness must change source")
                for number in changed:
                    line = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"',
                                  lambda m: " " * len(m.group()), after[number - 1])
                    self.assertIsNone(raw_heads.search(line), f"{path}:{number}")
        capacity = (self.root / "scripts/check-domain-bitness-laws.lisp").read_text(encoding="utf-8")
        self.assertIn("(як-є 00000000000)", capacity)
        self.assertIn("(як-є 1111111111)", capacity)
        # D5/D6/D8/D9 operators are separately admitted; not inferred from width.
        logic = (self.root / "scripts/check-domain-logic-laws.lisp").read_text(encoding="utf-8")
        self.assertIn("(менше? 2 3)", logic)
        self.assertIn('(тотожне? (перше (читати-всі (читати-файл "lib/domains/d1.lisp")))', logic)
        self.assertNotIn('(101 (100 (110101001 (110110111 "lib/domains/d1.lisp")))', logic)
        self.assertIn('(друкувати "DOMAIN-LOGIC-LAWS:', logic)
        self.assertNotIn('(11011011 "DOMAIN-LOGIC-LAWS:', logic)

    def test_negative_wrong_ukrainian_peer_breaks_exact_witness(self):
        path = "scripts/check-domain-bitness-laws.lisp"
        source = (self.root / path).read_text(encoding="utf-8")
        bad = source.replace("(визначити завантажити-домен", "(функція завантажити-домен", 1)
        self.assertNotEqual(source, bad)
        with self.assertRaises(AssertionError):
            self._inverse(bad, self.PINNED[path]["edits"])



class ReaderTierUkrSourceMigrationTests(unittest.TestCase):
    """Source-only: точний обернений D3/D4 зріз; НЕ Python-SENS виконання."""

    PINNED = {
  "scripts/check-domain-table-readable.lisp": {
    "sha": "567e25a933c8ed29c5604470824b4a52f17cdc6e",
    "edits": [
      [
        186,
        "0011"
      ],
      [
        206,
        "0010"
      ],
      [
        223,
        "100"
      ],
      [
        275,
        "0011"
      ],
      [
        294,
        "0010"
      ],
      [
        311,
        "011"
      ],
      [
        325,
        "0011"
      ],
      [
        348,
        "0010"
      ],
      [
        381,
        "100"
      ],
      [
        428,
        "0011"
      ],
      [
        474,
        "0011"
      ],
      [
        520,
        "0011"
      ],
      [
        566,
        "0011"
      ],
      [
        612,
        "0011"
      ],
      [
        658,
        "0011"
      ],
      [
        704,
        "0011"
      ],
      [
        751,
        "110"
      ],
      [
        759,
        "101"
      ],
      [
        764,
        "100"
      ],
      [
        773,
        "001"
      ],
      [
        798,
        "110"
      ],
      [
        848,
        "110"
      ],
      [
        904,
        "110"
      ],
      [
        966,
        "110"
      ],
      [
        1035,
        "110"
      ],
      [
        1110,
        "110"
      ],
      [
        1191,
        "110"
      ],
      [
        1279,
        "110"
      ],
      [
        1308,
        "101"
      ],
      [
        1362,
        "110"
      ],
      [
        1394,
        "101"
      ],
      [
        1452,
        "110"
      ],
      [
        1487,
        "101"
      ],
      [
        1549,
        "110"
      ],
      [
        1587,
        "101"
      ],
      [
        1653,
        "110"
      ],
      [
        1694,
        "101"
      ],
      [
        1764,
        "110"
      ],
      [
        1808,
        "101"
      ],
      [
        1882,
        "110"
      ],
      [
        1929,
        "101"
      ]
    ],
    "changed": [
      5,
      6,
      7,
      11,
      12,
      13,
      15,
      16,
      18,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      29,
      30,
      31,
      33,
      35,
      37,
      39,
      41,
      43,
      45,
      46,
      47,
      48,
      49,
      50,
      51,
      52,
      53,
      54,
      55,
      56,
      57,
      58
    ]
  },
  "scripts/fixtures-for-tier.lisp": {
    "sha": "59f75d93e00419575070162e4c83b7c49c2dfc34",
    "edits": [
      [
        1179,
        "0011"
      ],
      [
        1199,
        "110"
      ],
      [
        1209,
        "010"
      ],
      [
        1793,
        "0011"
      ],
      [
        1814,
        "0010"
      ],
      [
        1870,
        "0011"
      ],
      [
        1893,
        "0010"
      ],
      [
        1915,
        "110"
      ],
      [
        1927,
        "010"
      ],
      [
        1943,
        "001"
      ],
      [
        1960,
        "010"
      ],
      [
        1965,
        "001"
      ],
      [
        1976,
        "0010"
      ],
      [
        1997,
        "110"
      ],
      [
        2017,
        "101"
      ],
      [
        2036,
        "100"
      ],
      [
        2124,
        "010"
      ],
      [
        2129,
        "001"
      ],
      [
        2139,
        "001"
      ],
      [
        2178,
        "011"
      ]
    ],
    "changed": [
      22,
      23,
      24,
      36,
      37,
      40,
      41,
      42,
      43,
      44,
      45,
      46,
      48,
      49
    ]
  }
}

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        import re
        row = re.compile(
            r"^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)"
        )
        cls.names = {}
        for width in (3, 4):
            contents = (cls.root / f"lib/domains/d{width}.lisp").read_text(
                encoding="utf-8"
            )
            for line in contents.splitlines():
                matched = row.match(line)
                if matched and len(matched[1]) == width:
                    cls.names[matched[1]] = matched[2]
        cls.assert_authority = (
            cls.names.get("0011") == "визначити"
            and cls.names.get("0010") == "функція"
            and cls.names.get("001") == "як-є"
            and cls.names.get("100") == "перше"
        )
        if not cls.assert_authority:
            raise AssertionError("Немає ратифікованих exact D3/D4 peers")

    @staticmethod
    def _pre_last_projection(path, source):
        # Окремий D1/D6/D8/D9 зріз проходить СВІЙ суворий inverse
        # перед старим незмінним D3/D4 Git-blob witness.
        if path == "scripts/check-domain-table-readable.lisp":
            return DomainTableReadableUkrMigrationTests._undo_exact_heads(source)
        if path == "scripts/fixtures-for-tier.lisp":
            # Separate D3/D5/D8/D9 executable heads, never infer old SID8
            # from byte equality. These three witnessed lines are reversible.
            exact_lines = (
                ("    (решта (знайти-за-ключем (як-є tier) приклад))))",
                 "    (011 (11100 (001 tier) приклад))))"),
                ("             (друкувати (перше залишок)))",
                 "             (11011011 (100 залишок)))"),
                ('(читати-всі (читати-файл "tests/fixtures/conformance.lisp"))',
                 '(110101001 (110110111 "tests/fixtures/conformance.lisp"))'),
            )
            for live, old in exact_lines:
                if source.count(live) != 1:
                    raise AssertionError("Втрачено однозначну ратифіковану укр-викличну голову")
                source = source.replace(live, old, 1)
            return source
        return source

    @classmethod
    def reverse(cls, text, edits):
        import re
        masked = re.sub(
            r';[^\n]*|"(?:\\.|[^"\\])*"',
            lambda match: " " * len(match.group()),
            text,
        )
        offsets = []
        cursor = 0
        for _original_offset, old in edits:
            peer = cls.names.get(old)
            if peer is None or len(old) not in (3, 4):
                raise AssertionError(f"Нератифікована координата {old}")
            pattern = re.compile(r"\(\s*" + re.escape(peer) + r"(?=\s|\))")
            match = pattern.search(masked, cursor)
            if match is None:
                raise AssertionError(f"Втрачена українська проєкція {old} після позиції {cursor}")
            offset = match.end() - len(peer)
            offsets.append((offset, old, peer))
            cursor = match.end()
        for offset, bits, peer in reversed(offsets):
            if text[offset:offset + len(peer)] != peer:
                raise AssertionError(f"Втрачена українська проєкція {bits} at {offset}")
            text = text[:offset] + bits + text[offset + len(peer):]
        return text

    @staticmethod
    def blob_sha(text):
        payload = text.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(payload)).encode() + b"\0" + payload
        ).hexdigest()

    def test_exact_inverse_matches_each_projection_checkpoint(self):
        for path, witness in self.PINNED.items():
            with self.subTest(path=path):
                current = (self.root / path).read_text(encoding="utf-8")
                restored = self.reverse(self._pre_last_projection(path, current), witness["edits"])
                self.assertEqual(self.blob_sha(restored), witness["sha"])
                mod.parse(restored)
                mod.parse(current)

    def test_only_verified_code_heads_changed_no_new_encoded_heads(self):
        import re
        encoded = re.compile(r"\(\s*[01]+(?=\s|\)|$)|#(?:d\d+:[01]+|b[01]+)")
        for path, witness in self.PINNED.items():
            with self.subTest(path=path):
                source = (self.root / path).read_text(encoding="utf-8")
                original = self.reverse(self._pre_last_projection(path, source), witness["edits"])
                before, after = original.splitlines(), self._pre_last_projection(path, source).splitlines()
                self.assertEqual(len(before), len(after))
                changed = [
                    i + 1 for i, (a, b) in enumerate(zip(before, after))
                    if a != b
                ]
                # The projection-checkpoint hash verifies all non-head bytes exactly.
                self.assertTrue(changed, f"{path}: projection witness must change source")
                for line in changed:
                    code = re.sub(
                        r';[^\n]*|"(?:\\.|[^"\\])*"',
                        lambda m: " " * len(m.group()),
                        after[line - 1],
                    )
                    self.assertIsNone(encoded.search(code), f"{path}:{line}")

    def test_quoted_data_other_domain_words_and_names_stay_unchanged(self):
        reader = (self.root / "scripts/check-domain-table-readable.lisp").read_text(
            encoding="utf-8"
        )
        tier = (self.root / "scripts/fixtures-for-tier.lisp").read_text(
            encoding="utf-8"
        )
        self.assertIn("(визначити завантажити-домен", reader)
        self.assertIn("(визначити д8", reader)
        self.assertIn('"00000000"', reader)
        self.assertIn("(читати-всі", reader)  # Чинний D9 peer; викличність незалежна від ширини
        self.assertIn("(визначити потрібний-рівень", tier)
        self.assertIn("(прочитати (перше *argv*))", tier)
        self.assertNotIn("(11101010 (100 *argv*))", tier)
        self.assertIn("(визначити надрукувати-відповідні", tier)
        self.assertIn("(решта (знайти-за-ключем (як-є tier) приклад))", tier)
        self.assertIn("(друкувати (перше залишок))", tier)
        self.assertIn('(читати-всі (читати-файл "tests/fixtures/conformance.lisp"))', tier)
        self.assertNotIn("(11100 (001 tier) fixture)", tier)
        self.assertNotIn("(11011011 (100 remaining))", tier)
        self.assertNotIn('(110101001 (110110111 "tests/fixtures/conformance.lisp"))', tier)
        self.assertNotIn("(0011 target-tier", tier)

    def test_negative_wrong_peer_cannot_pass_exact_inverse(self):
        path = "scripts/check-domain-table-readable.lisp"
        source = (self.root / path).read_text(encoding="utf-8")
        mutation = source.replace(
            "(визначити завантажити-домен", "(функція завантажити-домен", 1
        )
        self.assertNotEqual(source, mutation)
        with self.assertRaises(AssertionError):
            self.reverse(self._pre_last_projection(path, mutation), self.PINNED[path]["edits"])



class DomainTableReadableUkrMigrationTests(unittest.TestCase):
    """D1/D6/D8/D9 живі проєкції без W8 і підміни D24+ арифметики."""

    SOURCE = Path(__file__).resolve().parents[1] / "scripts/check-domain-table-readable.lisp"
    PROJECTION_CHECKPOINT_BLOB = "e183d5a8c08a88485930865a3ec7314691887822"
    PEERS = (
        (1, "1", "так", 15),
        (6, "000100", "елемент-списку-за-індексом", 1),
        (8, "11110100", "значення-у-текст", 1),
        (9, "110101001", "читати-всі", 1),
        (9, "110110111", "читати-файл", 1),
    )

    @classmethod
    def _undo_exact_heads(cls, source):
        import hashlib
        import re
        for width, bits, ukr, n in reversed(cls.PEERS):
            pat = re.compile(r"\(\s*" + re.escape(ukr) + r"(?=\s|\))")
            found = list(pat.finditer(source))
            if len(found) != n:
                raise AssertionError(f"PEER_COUNT D{width}:{bits} {ukr}: {len(found)} != {n}")
            source = pat.sub(lambda m: m.group().replace(ukr, bits), source)
        raw = source.encode("utf-8")
        digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if digest != cls.PROJECTION_CHECKPOINT_BLOB:
            raise AssertionError(
                f"INVERSE_CHECKPOINT expected={cls.PROJECTION_CHECKPOINT_BLOB} actual={digest}"
            )
        return source

    def test_ratified_peers_match_projection_checkpoint(self):
        root = Path(__file__).resolve().parents[1]
        source = self.SOURCE.read_text(encoding="utf-8")
        for width, bits, ukr, count in self.PEERS:
            with self.subTest(domain=f"D{width}", bits=bits):
                rows = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8").splitlines()
                matches = [line for line in rows if line.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(matches), 1)
                self.assertIn(f"(укр {ukr})", matches[0])
                import re
                found = re.findall(r"\(\s*" + re.escape(ukr) + r"(?=\s|\))", source)
                self.assertEqual(len(found), count)
        self.assertIn("(довжина (рядки-домену д1))", source)
        self.assertNotIn("(000000 (table-rows d1))", source)
        self._undo_exact_heads(source)

    def test_wrong_d9_peer_does_not_pass_projection_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        wrong = source.replace("(читати-всі", "(читати-файл", 1)
        self.assertNotEqual(wrong, source)
        with self.assertRaisesRegex(AssertionError, "PEER_COUNT"):
            self._undo_exact_heads(wrong)
        self.assertIn('"00000000"', source)
        self.assertIn("(довжина (рядки-домену д8))", source)



class ConstitutionAndRustGeneratorUkrProjectionTests(unittest.TestCase):
    """Exact ukr projection of live Lisp generators, pinned to inverse checkpoints."""
    ROOT = Path(__file__).resolve().parents[1]
    PROJECTIONS = {
        "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
        "0010": "функція", "0011": "визначити", "1001": "друге", "1110": "список",
        "10011": "третє", "11100": "знайти-за-ключем",
        "001000": "нехай", "001001": "нехай-послідовно", "101110": "згорнути",
        "11011011": "друкувати", "11110100": "значення-у-текст", "11110111": "однакові?",
        "110011101": "рядок-решта", "110011110": "рядок-додати", "110101001": "читати-всі",
        "110101010": "рядок-префікс?", "110101011": "рядок-перший", "110110111": "читати-файл",
        "110111001": "число-рядок", "110111100": "записати-файл",
    }
    INVERSE = {surface: bits for bits, surface in PROJECTIONS.items()}
    SPECS = {
        "scripts/build-constitution.lisp": {
            "blob": "9254674d0669c46a24ccd2630a419315efc2c3c5",
            "counts": {"110": 1, "111": 8, "1110": 19, "11011011": 27, "110101001": 1,
                       "110110111": 1, "0011": 3, "001": 52, "0010": 3, "010": 2,
                       "100": 1, "011": 1},
        },
        "scripts/generate-rust-evaluator-dispatch.lisp": {
            "blob": "489b46e8b5faa3e08344f7a3e9363eae8d0107b7",
            # Newly surfaced raw heads add four calls: two D1, one D3, one D8;
            # the inverse projection still restores the pinned source blob.
            "counts": {"100": 9, "110": 7, "111": 1, "1001": 4, "1110": 3, "11011011": 4,
                       "11110100": 1, "11110111": 4, "110011110": 1, "110101001": 1,
                       "110110111": 2, "110111100": 2, "11100": 2, "001000": 2, "101110": 1,
                       "0011": 12, "0010": 7, "001": 15, "011": 5, "010": 12},
        },
        "scripts/generate-rust-function-signatures.lisp": {
            "blob": "a64b16690225bcae6919c2f84fd6059551f2d62b",
            "counts": {"100": 10, "101": 4, "110": 10, "1001": 6, "1110": 3, "11011011": 4,
                       "11110100": 3, "11110111": 6, "110011101": 5, "110011110": 2,
                       "110101001": 1, "110101010": 1, "110101011": 2, "110110111": 3,
                       "110111001": 1, "110111100": 2, "10011": 1, "11100": 2,
                       "001000": 1, "101110": 1, "0011": 15, "0010": 11, "010": 12,
                       "001": 25, "011": 3},
        },
    }

    @classmethod
    def _head_edits(cls, source):
        offsets = [0]
        offsets.extend(match.end() for match in re.finditer("\\n", source))
        edits = []

        def walk(node, quasi=0):
            if isinstance(node, mod.Prefix):
                if node.marker in ("'", "#;"):
                    return
                if node.marker == chr(96):
                    walk(node.datum, quasi + 1)
                    return
                if node.marker in (",", ",@"):
                    walk(node.datum, max(0, quasi - 1))
                    return
                return
            if not isinstance(node, mod.Form) or not node.values:
                return
            head = mod.atom(node.values[0])
            if quasi:
                for child in node.values:
                    walk(child, quasi)
                return
            if head in cls.INVERSE:
                token = node.values[0]
                bits = cls.INVERSE[head]
                edits.append({
                    "bits": bits, "head": head,
                    "offset": offsets[token.line - 1] + token.column - 1,
                })
            # Only traverse code-bearing positions. QUOTE payloads and all
            # ordinary strings/comments remain data, never candidate calls.
            if head in ("001", "як-є", "quote"):
                return
            if head in ("0010", "функція", "lambda"):
                for child in node.values[2:]:
                    walk(child)
                return
            if head in ("0011", "визначити", "define", "defmacro", "визначити-макрос"):
                for child in node.values[2:]:
                    walk(child)
                return
            if head in ("110", "за-умовою", "cond"):
                for clause in node.values[1:]:
                    if isinstance(clause, mod.Form) and len(clause.values) >= 2:
                        walk(clause.values[0])
                        for result in clause.values[1:]:
                            walk(result)
                    else:
                        walk(clause)
                return
            # A few retained historical D6 LET forms enclose D9 calls. This
            # walk verifies those already-projected child heads only; it does
            # not ratify or enable the enclosing D6 mechanism.
            if head in ("001000", "001001", "нехай", "нехай-послідовно", "зв'язати", "звʼязати", "let", "let*"):
                if len(node.values) > 1 and isinstance(node.values[1], mod.Form):
                    for binding in node.values[1].values:
                        if isinstance(binding, mod.Form):
                            for expression in binding.values[1:]:
                                walk(expression)
                for child in node.values[2:]:
                    walk(child)
                return
            # A computed operator is executable code too. In particular,
            # ((функція (...) body) args) must visit the lambda form and its
            # body; skipping node.values[0] loses exact-domain evidence.
            if isinstance(node.values[0], mod.Form):
                walk(node.values[0])
            for child in node.values[1:]:
                walk(child)

        for form in mod.parse(source):
            walk(form)
        return edits

    @staticmethod
    def _blob_sha(source):
        payload = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(payload)).encode("ascii") + bytes([0]) + payload
        ).hexdigest()

    def _assert_source_is_exact_ukr_projection(self, path, source):
        spec = self.SPECS[path]
        for bits, surface in self.PROJECTIONS.items():
            table = (self.ROOT / "lib" / "domains" / f"d{len(bits)}.lisp").read_text(encoding="utf-8")
            rows = [line for line in table.splitlines() if line.strip().startswith(f"({bits} (ук ")]
            self.assertEqual(len(rows), 1, f"D{len(bits)}:{bits} owner row must be unique")
            self.assertIn(f"(укр {surface})", rows[0], f"D{len(bits)}:{bits} must match owner укр")
        edits = self._head_edits(source)
        actual = Counter(edit["bits"] for edit in edits)
        self.assertEqual(dict(actual), spec["counts"], f"{path}: exact-width head census differs")
        self.assertTrue(edits, f"{path}: expected projected call heads")
        for edit in edits:
            self.assertEqual(edit["head"], self.PROJECTIONS[edit["bits"]],
                             f"{path}: encoded or wrong peer remains")
        restored = source
        for edit in sorted(edits, key=lambda item: item["offset"], reverse=True):
            head, offset, bits = edit["head"], edit["offset"], edit["bits"]
            self.assertEqual(restored[offset:offset + len(head)], head, f"{path}: offset drift")
            restored = restored[:offset] + bits + restored[offset + len(head):]
        self.assertEqual(self._blob_sha(restored), spec["blob"],
                         f"{path}: reverse projection must restore original Git blob")
        mod.parse(source)
        mod.parse(restored)
        self.assertEqual(len(source.splitlines()), len(restored.splitlines()))

    def test_three_live_generators_use_exact_ukr_projection_and_inverse(self):
        for path in self.SPECS:
            with self.subTest(path=path):
                source = (self.ROOT / path).read_text(encoding="utf-8")
                self._assert_source_is_exact_ukr_projection(path, source)

    def test_wrong_peer_mutation_is_rejected(self):
        path = "scripts/build-constitution.lisp"
        source = (self.ROOT / path).read_text(encoding="utf-8")
        edits = self._head_edits(source)
        first = next(edit for edit in edits if edit["bits"] == "0011")
        wrong = self.PROJECTIONS["0010"]
        mutated = source[:first["offset"]] + wrong + source[first["offset"] + len(first["head"]):]
        with self.assertRaises(AssertionError):
            self._assert_source_is_exact_ukr_projection(path, mutated)

if __name__ == '__main__':
    unittest.main(verbosity=2)
