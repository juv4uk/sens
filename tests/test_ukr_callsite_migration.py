"""Negative and positive witnesses for the static Ukrainian call-site audit.

These tests use their own temporary roots; they NEVER rewrite project Lisp.
"""
from __future__ import annotations

import importlib.util
import hashlib
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
        self.assertIn("(визначити canon-law-result", source)  # exact D4:0011 full укр, не нова identity
        self.assertNotIn("(0011 canon-law-result", source)  # колишня coded DEFINE більше не source

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
        self.assertIn("(сполучити (як-є atom) (my-fc-primitive (як-є atom)))", first)
        self.assertIn("(тотожне? (перше form) (як-є def))", mutual)
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
        self.assertIn("((атом? value) ні)", mutual)
        self.assertIn("(так (тотожне? (перше value) (як-є recursive-group-closure)))", mutual)
        self.assertNotIn("#d1:0", mutual)
        self.assertIn("(визначити my-fc-env-lookup", first)
        self.assertNotIn("(0011 my-fc-env-lookup", first)
        self.assertIn("(визначити my-group-eval", mutual)
        # Negative witness: numeric operator behind QUOTE remains data, not callable.
        sample = "(як-є (100 quoted)) (сполучити (як-є datum) (перше xs))"
        heads = [x.text for x in mod.candidate_heads(mod.parse(sample))]
        self.assertNotIn("100", heads)
        self.assertIn("сполучити", heads)
        self.assertIn("перше", heads)


    def test_first_class_exact_inverse_original_git_blob(self):
        """Перевірка точних D1/D3/D4 координат і збереження ВСІХ старих байтів."""
        current_src = (Path(__file__).resolve().parents[1] / "lib/meta-eval-first-class.lisp").read_text(encoding="utf-8")
        # Спершу строго відновлюємо 31 пізнішу поточну D3–D8 укр-проєкцію.
        # І лише тоді починає діяти старий незмінний D1/D3/D4 receipt нижче.
        # Таким чином pinned Git blob ніколи не послаблюється.
        from tests.test_meta_eval_fc_ukr_remaining import reconstruct as undo_latest_projection
        self.assertIn("(додати (перше args) (друге args))", current_src)
        src = undo_latest_projection(current_src)
        originals = (
        (634, "0011"),
        (712, "0011"),
        (1362, "0011"),
        (1517, "#d1:1"),
        (1547, "011"),
        (1563, "0011"),
        (1627, "010"),
        (1638, "#d1:0"),
        (1652, "#d1:1"),
        (1659, "101"),
        (1664, "100"),
        (1676, "001"),
        (1698, "0011"),
        (1760, "010"),
        (1771, "#d1:0"),
        (1785, "#d1:1"),
        (1792, "101"),
        (1797, "100"),
        (1809, "001"),
        (1829, "0011"),
        (1930, "#d1:1"),
        (2065, "0011"),
        (2163, "#d1:1"),
        (2273, "0011"),
        (2397, "#d1:1"),
        (2516, "0011"),
        (2715, "#d1:1"),
        (2739, "011"),
        (2837, "0011"),
        (2906, "010"),
        (2911, "011"),
        (2922, "#d1:1"),
        (3137, "#d1:1"),
        (3144, "001"),
        (3207, "#d1:1"),
        (3213, "#d1:0"),
        (3225, "0011"),
        (3992, "#d1:1"),
        (3999, "1110"),
        (4005, "001"),
        (4040, "0011"),
        (4363, "#d1:1"),
        (4370, "1110"),
        (4376, "001"),
        (4404, "0011"),
        (5142, "#d1:1"),
        (5271, "#d1:1"),
        (5603, "0011"),
        )
        ratified = {}
        import re as _re
        for domain in (1, 3, 4):
            table = (Path(__file__).resolve().parents[1] / f"lib/domains/d{domain}.lisp").read_text(encoding="utf-8")
            for match in _re.finditer(r"(?m)^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)", table):
                bits, peer = match.groups()
                if len(bits) == domain:
                    ratified[(domain, bits)] = peer

        def undo(source):
            coords = []
            delta = 0
            previous = -1
            for offset, literal in originals:
                self.assertGreater(offset, previous)
                previous = offset
                bits = literal.split(":")[-1] if literal.startswith("#d1:") else literal
                peer = ratified[(len(bits), bits)]
                coords.append((offset + delta, literal, peer))
                delta += len(peer) - len(literal)
            for pos, literal, peer in reversed(coords):
                self.assertEqual(source[pos:pos + len(peer)], peer)
                source = source[:pos] + literal + source[pos + len(peer):]
            return source

        def sha_blob(source):
            body = source.encode("utf-8")
            return hashlib.sha1(b"blob " + str(len(body)).encode() + b"\x00" + body).hexdigest()

        self.assertEqual(sha_blob(undo(src)), "67c2d9e0e41702ea37d229a8280d60d153dca99d")
        self.assertIn("(як-є atom)", src)  # цитовані дані лишаються даними
        self.assertIn("(01010 (100 args) (1001 args))", src)  # D5 без доказу викличності не чіпали

        broken = src.replace("(визначити my-fc-primitive", "(визначити-хибно my-fc-primitive", 1)
        self.assertNotEqual(broken, src)
        with self.assertRaises(AssertionError):
            undo(broken)



class UnifyUkrDomainProjectionTests(unittest.TestCase):
    """Current domain spellings; source-only, not a Python semantics evaluator."""

    def test_unify_uses_ratified_d3_d4_ukr_calls(self):
        root = Path(__file__).resolve().parents[1]
        required = [
                  [
                            "атом?",
                            28
                  ],
                  [
                            "за-умовою",
                            20
                  ],
                  [
                            "перше",
                            11
                  ],
                  [
                            "порожній?",
                            3
                  ],
                  [
                            "приєднати",
                            1
                  ],
                  [
                            "решта",
                            10
                  ],
                  [
                            "список",
                            2
                  ],
                  [
                            "сполучити",
                            3
                  ],
                  [
                            "тотожне?",
                            4
                  ],
                  [
                            "функція",
                            17
                  ],
                  [
                            "як-є",
                            29
                  ]
        ]
        source = (root / "lib/unify.lisp").read_text(encoding="utf-8")
        heads = [node.text for node in mod.candidate_heads(mod.parse(source))]
        for name, minimum in required:
            with self.subTest(head=name):
                self.assertGreaterEqual(heads.count(name), minimum)
        for width, bits, ukr in (
            (3, "001", "як-є"), (3, "010", "атом?"),
            (3, "011", "решта"), (3, "100", "перше"),
            (3, "101", "тотожне?"), (3, "110", "за-умовою"),
            (3, "111", "сполучити"), (4, "0010", "функція"),
            (4, "0100", "хибне?"), (4, "0101", "порожній?"),
            (4, "1110", "список"), (4, "1111", "приєднати"),
        ):
            with self.subTest(domain=width, bits=bits):
                table = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8")
                rows = [line for line in table.splitlines()
                        if line.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(укр {ukr})", rows[0])

    def test_unify_preserves_quoted_data_and_d1_identity(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "lib/unify.lisp").read_text(encoding="utf-8")
        self.assertIn("(визначити unify\n", source)
        self.assertIn("(визначити unify-walked\n", source)
        self.assertIn("(так ні)", source)
        self.assertIn("(як-є (ні))", source)
        active_unify = "\n".join(line.split(";", 1)[0]
                                 for line in source.splitlines())
        self.assertNotIn("(0011 unify", active_unify)
        self.assertNotIn("#d1:1", active_unify)
        self.assertNotIn("#d1:0", active_unify)
        # Quoted forms carry data; numeric-looking heads inside them are not calls.
        sample = "(як-є (100 quoted)) (сполучити (як-є (0)) (перше xs))"
        heads = [x.text for x in mod.candidate_heads(mod.parse(sample))]
        self.assertNotIn("100", heads)
        self.assertNotIn("0", heads)
        self.assertIn("сполучити", heads)
        self.assertIn("перше", heads)


class UnderstandMapUkrSourceTests(unittest.TestCase):
    """Реальні джерела: ратифіковані голови, без приглушення негативів."""

    def test_both_active_modules_have_only_named_ukr_execution_heads(self):
        root = Path(__file__).resolve().parents[1]
        for file, required, definitions in (
            ("lib/understand.lisp", ("визначити", "функція", "атом?",
                                      "решта-решти", "третє", "четверте"), 15),
            ("lib/persistent-map.lisp", ("визначити", "функція",
                                         "за-умовою", "тотожне?", "так"), 14),
        ):
            with self.subTest(file=file):
                source = (root / file).read_text(encoding="utf-8")
                mod.parse(source)  # failure propagates; no synthetic SENS evaluator
                active = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
                self.assertEqual(active.count("(визначити "), definitions)
                for name in required:
                    self.assertIn(name, active)
                self.assertNotRegex(active, r"\(\s*[01]{3,6}(?=\s|\))")
                self.assertNotIn("#d1:1", active)

    def test_understand_historical_laws_remain_strict(self):
        from copy import deepcopy
        from tests import test_understand_exact_d3_2046 as witness
        current = witness.read_forms(witness.SOURCE.read_text(encoding="utf-8"))
        normalized = witness.normalize_current_source_forms(current)
        self.assertEqual(len(normalized), 8)
        self.assertEqual(witness.verify_unchanged_laws(normalized), normalized)
        wrong_peer = deepcopy(current)
        wrong_peer[0][2][2][1][0][0] = "тотожне?"
        with self.assertRaisesRegex(AssertionError, "непорожній CAR"):
            witness.verify_unchanged_laws(
                witness.normalize_current_source_forms(wrong_peer))

    def test_quoted_data_remains_data_and_d1_is_its_own_identity(self):
        root = Path(__file__).resolve().parents[1]
        understand = (root / "lib/understand.lisp").read_text(encoding="utf-8")
        mapped = (root / "lib/persistent-map.lisp").read_text(encoding="utf-8")
        self.assertIn("(як-є has)", understand)
        self.assertIn("(як-є var)", understand)
        self.assertIn("(визначити map-empty (як-є ()))", mapped)
        self.assertEqual(len([line for line in understand.splitlines()
                              if line.strip().startswith("(так")]), 3)
        self.assertIn("(1 (ук так) (укр так)", (root / "lib/domains/d1.lisp").read_text(encoding="utf-8"))
        sample = "(як-є (100 protected-data)) (сполучити (як-є a) (як-є ()))"
        observed = [t.text for t in mod.candidate_heads(mod.parse(sample))]
        self.assertNotIn("100", observed)
        self.assertIn("сполучити", observed)


class Core1D3D4UkrSourceProjectionTests(unittest.TestCase):
    """Exact Ukrainian spelling, not permission to execute a historical SID8 byte."""

    def test_core1_current_d3_d4_calls_follow_ratified_ukr(self):
        root = Path(__file__).resolve().parents[1]
        rows = (
            (3, "001", "як-є"), (3, "010", "атом?"),
            (3, "011", "решта"), (3, "100", "перше"),
            (3, "101", "тотожне?"), (3, "110", "за-умовою"),
            (3, "111", "сполучити"), (4, "0010", "функція"),
            (4, "0011", "визначити"), (4, "1001", "друге"),
        )
        for width, bits, ukr in rows:
            with self.subTest(width=width, bits=bits):
                source = (root / "lib/domains" / f"d{width}.lisp").read_text(encoding="utf-8")
                authority = [line for line in source.splitlines()
                             if line.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(authority), 1)
                self.assertIn(f"(укр {ukr})", authority[0])

        src = (root / "lib/core1.lisp").read_text(encoding="utf-8")
        heads = [token.text for token in mod.candidate_heads(mod.parse(src))]
        for ukr in ("визначити", "функція", "за-умовою", "тотожне?", "перше", "як-є"):
            self.assertIn(ukr, heads)
        self.assertIn("(визначити C1-SECOND", src)
        self.assertIn("(функція (X)", src)

    def test_core1_quotes_and_legacy_w8_are_not_assigned_new_identity(self):
        root = Path(__file__).resolve().parents[1]
        src = (root / "lib/core1.lisp").read_text(encoding="utf-8")
        self.assertIn("#d1:0", src)
        self.assertIn("#d1:1", src)
        # Under QUOTE, even a binary-looking list head remains inert data.
        sample = "(як-є (00000101 (100 datum))) (визначити answer (функція (x) (перше x)))"
        heads = [token.text for token in mod.candidate_heads(mod.parse(sample))]
        self.assertNotIn("00000101", heads)
        self.assertNotIn("100", heads)
        self.assertIn("перше", heads)
        # Wrong Ukrainian peer: D3 CAR != CDR, even if both have three bits.
        d3 = (root / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        self.assertNotEqual(
            next(s for s in d3.splitlines() if s.strip().startswith("(100 (ук ")),
            next(s for s in d3.splitlines() if s.strip().startswith("(011 (ук ")),
        )



class UkrainianGreetingFullSurfaceTests(unittest.TestCase):
    """Один повністю доведений D4-фрагмент активного українського прикладу."""

    def test_guest_list_definition_uses_ratified_full_ukr_d4_forms(self):
        import hashlib

        root = Path(__file__).resolve().parents[1]
        path = root / "examples/ukrainian-greeting.lisp"
        original_bytes = path.read_bytes()
        source = original_bytes.decode("utf-8")
        old_form = "(0011 гості (1110 'Олена 'Тарас 'Вова))"
        new_form = "(визначити гості (список 'Олена 'Тарас 'Вова))"

        self.assertEqual(source.count(new_form), 1)
        self.assertNotIn(old_form, source)
        self.assertIn("'Олена 'Тарас 'Вова", source)
        mod.parse(source)

        for bits, spelling in (("0011", "визначити"), ("1110", "список")):
            table = (root / "lib/domains/d4.lisp").read_text(encoding="utf-8")
            rows = [line for line in table.splitlines()
                    if line.strip().startswith(f"({bits} (ук ")]
            self.assertEqual(len(rows), 1)
            self.assertIn(f"(укр {spelling})", rows[0])

        restored = source.replace(new_form, old_form, 1).encode("utf-8")
        digest = hashlib.sha1(
            b"blob " + str(len(restored)).encode("ascii") + b"\0" + restored
        ).hexdigest()
        self.assertEqual(
            digest, "0c35ae861fdbed1edbe4fe932b8266dd4b51b869",
            "після зворотної заміни початковий Git blob має відновлюватися побайтно",
        )


class NativeFirstUkrProjectionTests(unittest.TestCase):
    """Reader-safe current D3/D4 projection; D9 identity does not grant admission."""

    @staticmethod
    def _git_blob(source: str) -> str:
        import hashlib
        data = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(data)).encode("ascii")
                            + b"\0" + data).hexdigest()

    def test_exact_current_ukrainian_peers_and_frozen_inverse(self):
        root = Path(__file__).resolve().parents[1]
        for width, bits, spelling in (
            (4, "0011", "визначити"),
            (9, "110110101", "п'ятий"),
        ):
            with self.subTest(domain=f"D{width}:{bits}"):
                data = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8")
                rows = [r for r in data.splitlines()
                        if r.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(укр {spelling})", rows[0])
        parity = (root / "lib/machine/dispatch/native-first-parity.lisp").read_text(encoding="utf-8")
        # Незмінні frozen-тести перевіряють оригінальний Git blob після
        # строгого зворотного α-перейменування (точно 59 входжень).
        from tests.test_ukr_machine_projection_parity import undo_current_lexical_binders
        parity = undo_current_lexical_binders("lib/machine/dispatch/native-first-parity.lisp", parity)
        coverage = (root / "lib/machine/dispatch/native-first-coverage.lisp").read_text(encoding="utf-8")
        new_p = "(error-class (перше (решта (решта (решта (решта row))))))"
        old_p = "(error-class (110110101 row))"
        new_c = "(визначити native-first-coverage-ledger"
        old_c = "(0011 native-first-coverage-ledger"
        self.assertEqual(parity.count(new_p), 1)
        self.assertEqual(coverage.count(new_c), 1)
        self.assertEqual(
            self._git_blob(parity.replace(new_p, old_p, 1)),
            "bc6a7e27a83192d667ba6791e4da4d867ed80971",
        )
        self.assertEqual(
            self._git_blob(coverage.replace(new_c, old_c, 1)),
            "7161b6c631d661b5a30d22acc4fd0331ec3e6379",
        )

    def test_wrong_peer_mutant_and_quoted_native_data(self):
        root = Path(__file__).resolve().parents[1]
        parity = (root / "lib/machine/dispatch/native-first-parity.lisp").read_text(encoding="utf-8")
        # Незмінні frozen-тести перевіряють оригінальний Git blob після
        # строгого зворотного α-перейменування (точно 59 входжень).
        from tests.test_ukr_machine_projection_parity import undo_current_lexical_binders
        parity = undo_current_lexical_binders("lib/machine/dispatch/native-first-parity.lisp", parity)
        coverage = (root / "lib/machine/dispatch/native-first-coverage.lisp").read_text(encoding="utf-8")
        heads = [t.text for t in mod.candidate_heads(mod.parse(parity))]
        self.assertIn("перше", heads)
        self.assertGreaterEqual(heads.count("решта"), 4)
        self.assertNotIn("п", heads)
        self.assertNotIn("110110101", heads)
        self.assertIn("(001\n    ((native-coverage", coverage)
        self.assertIn("(110 ((101 (001 000) (001 001)) 0)", coverage)
        mutant = parity.replace("(error-class (перше (решта (решта (решта (решта row))))))",
                                "(error-class (перше (решта (решта (решта row)))))", 1)
        restored = mutant.replace("(error-class (перше (решта (решта (решта (решта row))))))",
                                  "(error-class (110110101 row))", 1)
        self.assertNotEqual(self._git_blob(restored),
                            "bc6a7e27a83192d667ba6791e4da4d867ed80971")
        wrong_declaration = coverage.replace(
            "(визначити native-first-coverage-ledger",
            "(функція native-first-coverage-ledger", 1,
        )
        self.assertNotIn("(визначити native-first-coverage-ledger", wrong_declaration)



class DomainLawScriptsUkrProjectionWitnessTests(unittest.TestCase):
    """Зворотний exact Git-свідок SENS-скриптів, без Python-виконання Lisp."""

    PINNED = {
  "scripts/check-domain-bitness-laws.lisp": {
    "sha": "72ea77c9c997ddc92ccc263aa09c112ca2798497",
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
    "sha": "381b4dcbb1ff53a7dbf87a20586b12bc17537449",
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
        shifts, delta, previous = [], 0, -1
        for pos, bits in edits:
            if pos <= previous:
                raise AssertionError("Некоректний порядок точних координат")
            previous = pos
            peer = cls.authority.get(bits)
            if peer is None or len(bits) not in (3, 4):
                raise AssertionError(f"Відсутня точна ратифікація {bits}")
            shifts.append((pos + delta, bits, peer))
            delta += len(peer) - len(bits)
        for pos, bits, peer in reversed(shifts):
            if current[pos:pos + len(peer)] != peer:
                raise AssertionError(f"Неправильна проєкція {bits} at {pos}")
            current = current[:pos] + bits + current[pos + len(peer):]
        return current

    def test_source_inverse_restores_exact_pre_migration_git_blobs(self):
        for path, evidence in self.PINNED.items():
            with self.subTest(path=path):
                source = (self.root / path).read_text(encoding="utf-8")
                restored = self._inverse(source, evidence["edits"])
                self.assertEqual(self._blob_sha(restored), evidence["sha"])
                mod.parse(source)
                mod.parse(restored)

    def test_changed_lines_keep_unproven_code_and_quote_data_untouched(self):
        import re
        raw_heads = re.compile(r"\(\s*[01]+(?=\s|\)|$)")
        for path, evidence in self.PINNED.items():
            with self.subTest(path=path):
                source = (self.root / path).read_text(encoding="utf-8")
                old = self._inverse(source, evidence["edits"])
                before, after = old.splitlines(), source.splitlines()
                self.assertEqual(len(before), len(after))
                changed = [i + 1 for i, (a, b) in enumerate(zip(before, after)) if a != b]
                self.assertEqual(changed, evidence["changed"])
                for number in changed:
                    line = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"',
                                  lambda m: " " * len(m.group()), after[number - 1])
                    self.assertIsNone(raw_heads.search(line), f"{path}:{number}")
        capacity = (self.root / "scripts/check-domain-bitness-laws.lisp").read_text(encoding="utf-8")
        self.assertIn("(як-є 00000000000)", capacity)
        self.assertIn("(як-є 1111111111)", capacity)
        # D5/D6/D8/D9 operators are separately admitted; not inferred from width.
        logic = (self.root / "scripts/check-domain-logic-laws.lisp").read_text(encoding="utf-8")
        self.assertIn("(11010 2 3)", logic)
        self.assertIn('(11011011 "DOMAIN-LOGIC-LAWS:', logic)

    def test_negative_wrong_ukrainian_peer_breaks_exact_witness(self):
        path = "scripts/check-domain-bitness-laws.lisp"
        source = (self.root / path).read_text(encoding="utf-8")
        bad = source.replace("(визначити load-domain", "(функція load-domain", 1)
        self.assertNotEqual(source, bad)
        with self.assertRaises(AssertionError):
            self._inverse(bad, self.PINNED[path]["edits"])



class ReaderTierUkrSourceMigrationTests(unittest.TestCase):
    """Source-only: доменна identity і exact inverse, НЕ Python-SENS виконання."""

    PINNED = {
  "scripts/check-domain-table-readable.lisp": {
    "sha": "e1c9a89a7338bcd46df4d9a5227b191acb28119d",
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
    "sha": "189cc75ed4f2eaaaf40f58d1730b33ee39bfa179",
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
        return source

    @classmethod
    def reverse(cls, text, edits):
        offsets, delta, previous = [], 0, -1
        for original_offset, old in edits:
            if original_offset <= previous:
                raise AssertionError("Порушено порядок exact source offsets")
            previous = original_offset
            peer = cls.names.get(old)
            if peer is None or len(old) not in (3, 4):
                raise AssertionError(f"Нератифікована координата {old}")
            offsets.append((original_offset + delta, old, peer))
            delta += len(peer) - len(old)
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

    def test_exact_inverse_reconstructs_each_original_git_blob(self):
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
                self.assertEqual(changed, witness["changed"])
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
        self.assertIn("(визначити load-domain", reader)
        self.assertIn("(визначити d8", reader)
        self.assertIn('"00000000"', reader)
        self.assertIn("(читати-всі", reader)  # Чинний D9 peer; викличність незалежна від ширини
        self.assertIn("(визначити target-tier", tier)
        self.assertIn("(визначити print-matching", tier)
        self.assertIn("(11100 (001 tier) fixture)", tier)  # D5 і цитата незмінні
        self.assertNotIn("(0011 target-tier", tier)

    def test_negative_wrong_peer_cannot_pass_exact_inverse(self):
        path = "scripts/check-domain-table-readable.lisp"
        source = (self.root / path).read_text(encoding="utf-8")
        mutation = source.replace(
            "(визначити load-domain", "(функція load-domain", 1
        )
        self.assertNotEqual(source, mutation)
        with self.assertRaises(AssertionError):
            self.reverse(self._pre_last_projection(path, mutation), self.PINNED[path]["edits"])



class DomainTableReadableUkrMigrationTests(unittest.TestCase):
    """D1/D6/D8/D9 живі проєкції без W8 і без підміни D24+ арифметики."""

    SOURCE = Path(__file__).resolve().parents[1] / "scripts/check-domain-table-readable.lisp"
    ORIGINAL_BLOB = "081bd59f4b81c65e1219a079aa7e20863943f28d"
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
        if digest != cls.ORIGINAL_BLOB:
            raise AssertionError(f"INVERSE_GIT_BLOB expected={cls.ORIGINAL_BLOB} actual={digest}")
        return source

    def test_ratified_peers_preserve_original_git_blob(self):
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
        self.assertIn("(000000 (table-rows d1))", source)
        self.assertNotIn("(довжина (table-rows d1))", source)
        self._undo_exact_heads(source)

    def test_wrong_d9_peer_does_not_pass_original_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        wrong = source.replace("(читати-всі", "(читати-файл", 1)
        self.assertNotEqual(wrong, source)
        with self.assertRaisesRegex(AssertionError, "PEER_COUNT"):
            self._undo_exact_heads(wrong)
        self.assertIn('"00000000"', source)
        self.assertIn("(000000 (table-rows d8))", source)



class ConstitutionAndRustGeneratorUkrProjectionTests(unittest.TestCase):
    """Exact ukr projection of live Lisp generators, pinned to original blobs."""
    ROOT = Path(__file__).resolve().parents[1]
    PROJECTIONS = {
        "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
        "0010": "функція", "0011": "визначити", "1001": "друге", "1110": "список",
        "11011011": "друкувати", "11110100": "значення-у-текст", "11110111": "однакові?",
        "110011101": "рядок-решта", "110011110": "рядок-додати", "110101001": "читати-всі",
        "110101010": "рядок-префікс?", "110101011": "рядок-перший", "110110111": "читати-файл",
        "110111001": "число-рядок", "110111100": "записати-файл",
    }
    INVERSE = {surface: bits for bits, surface in PROJECTIONS.items()}
    SPECS = {
        "scripts/build-constitution.lisp": {
            "blob": "0bbfef8844b7921f7873203d4c976fed2dd72619",
            "counts": {"110": 1, "111": 8, "1110": 19, "11011011": 27, "110101001": 1,
                       "110110111": 1, "0011": 3, "001": 52, "0010": 2, "010": 2},
        },
        "scripts/generate-rust-evaluator-dispatch.lisp": {
            "blob": "10ba0c9b9a0bc7a0565a1c4b9b74fbea7cbe737d",
            "counts": {"100": 8, "110": 7, "111": 1, "1001": 4, "1110": 3, "11011011": 4,
                       "11110100": 1, "11110111": 3, "110011110": 1, "110101001": 1,
                       "110110111": 2, "110111100": 2, "0011": 12, "0010": 7, "001": 14,
                       "011": 5, "010": 11},
        },
        "scripts/generate-rust-function-signatures.lisp": {
            "blob": "9f13458da58e4bfb295488886b39fad9fcff98a0",
            "counts": {"100": 10, "101": 4, "110": 10, "1001": 6, "1110": 3, "11011011": 4,
                       "11110100": 3, "11110111": 6, "110011101": 5, "110011110": 2,
                       "110101001": 1, "110101010": 1, "110101011": 2, "110110111": 3,
                       "110111001": 1, "110111100": 2, "0011": 15, "0010": 11, "010": 12,
                       "001": 25, "011": 3},
        },
    }

    @classmethod
    def _head_edits(cls, source):
        offsets = [0]
        offsets.extend(match.end() for match in re.finditer("\n", source))
        edits = []
        for token in mod.candidate_heads(mod.parse(source)):
            bits = cls.INVERSE.get(token.text)
            if bits is not None:
                edits.append({
                    "bits": bits, "head": token.text,
                    "offset": offsets[token.line - 1] + token.column - 1,
                })
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
