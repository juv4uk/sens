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


def assert_live_ukrainian_script(test, root, path, source):
    """Поточний доказ проєкції: D1–D10, не старий Git-blob-знімок."""
    forms = mod.parse(source)
    test.assertTrue(forms, f"{path}: порожня програма")
    admitted = set()
    for width in range(1, 11):
        table = root / "lib" / "domains" / f"d{width}.lisp"
        for line in table.read_text(encoding="utf-8").splitlines():
            if not re.match(r"^\s*\([01]+\s+\(ук\s", line):
                continue
            match = re.search(r"\(укр\s+([^()\s]+)\)", line)
            if match:
                admitted.add(match[1])
    definitions = set()
    for form in forms:
        if not isinstance(form, mod.Form) or not form.values:
            continue
        head = mod.atom(form.values[0])
        test.assertNotIn(head, ("функція", "lambda", "0010"),
                         f"{path}: самотня функція верхнього рівня замість визначення")
        if head == "визначити" and len(form.values) > 1:
            name = mod.atom(form.values[1])
            test.assertIsNotNone(name, f"{path}: визначення без імені")
            definitions.add(name)
    test.assertTrue(definitions, f"{path}: немає живих визначень")
    allowed = admitted | definitions
    # Єдиний явно очікуваний негативний шлях для відсутнього параметра CLI.
    if path == "scripts/fixtures-for-tier.lisp":
        allowed.add("бракує-аргументу-рівня")
    if path == "scripts/check-domain-bitness-laws.lisp":
        # Навмисно не визначені імена: негативні свідки повинні завершуватися помилкою.
        named_failures = {
            "помилка-ширини-домену",
            "помилка-д3-повтор-у-каноні",
            "помилка-д3-пропущений-дубль",
            "помилка-д3-крайній-ключ",
            "помилка-д3-початковий-ключ",
            "помилка-д3-ємність-мутанта",
            "помилка-ширини-домену-негативна",
        }
        test.assertFalse(named_failures & definitions,
                         "Негативні свідки не можна підміняти визначеними функціями")
        allowed.update(named_failures)
    heads = list(mod.candidate_heads(forms))
    test.assertTrue(heads, f"{path}: немає виконуваних голів")
    unknown = [(tok.text, tok.line) for tok in heads if tok.text not in allowed]
    test.assertFalse(unknown, f"{path}: невідомі або неукраїнські голови: {unknown[:8]}")

    # Голови у цитатах є ДАНИМИ; сирі машинні слова в коді — помилка.
    raw = []
    def check(node):
        if isinstance(node, mod.Prefix):
            if node.marker in ("'", "#;"):
                return
            check(node.datum)
            return
        if not isinstance(node, mod.Form) or not node.values:
            return
        head = mod.atom(node.values[0])
        if head in ("як-є", "quote", "001"):
            return
        if head is not None and re.fullmatch(r"[01]+", head):
            raw.append((head, node.pos.line))
        if head in ("визначити", "функція", "lambda", "define"):
            for child in node.values[2:]:
                check(child)
        elif head in ("нехай", "нехай-послідовно", "зв'язати", "звʼязати",
                      "let", "let*") and len(node.values) > 1:
            bindings = node.values[1]
            if isinstance(bindings, mod.Form):
                for binding in bindings.values:
                    if isinstance(binding, mod.Form):
                        for child in binding.values[1:]:
                            check(child)
            for child in node.values[2:]:
                check(child)
        else:
            for child in node.values:
                check(child)
    for form in forms:
        check(form)
    test.assertFalse(raw, f"{path}: сирі виконувані бітові голови: {raw[:8]}")


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

    def test_current_ukrainian_let_bindings_are_not_executable_calls(self):
        # Генератор справді використовує нехай з локальним
        # фізичний-запис: це ім'я параметра, а не мовний виклик.
        for binder in ("нехай", "нехай-послідовно"):
            with self.subTest(binder=binder):
                program = (
                    f"({binder} ((фізичний-запис (число-рядок число))) "
                    '(рядок-додати фізичний-запис "0b"))'
                )
                heads = [token.text for token in mod.candidate_heads(mod.parse(program))]
                self.assertIn(binder, heads)
                self.assertIn("число-рядок", heads)
                self.assertIn("рядок-додати", heads)
                self.assertNotIn("фізичний-запис", heads)

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
        self.put('sens-cml-export.contract', '"unterminated')
        report = mod.measure(self.root)
        self.assertEqual(report['active_unclassified_files'], 0)
        self.assertEqual(report['unclassified_files'], [])
        self.assertEqual(report['metadata_files_excluded'], 3)

    def test_machine_and_island_evidence_are_data_not_callable_lisp(self):
        # Historical executor labels and ABI keys belong to protocol data.
        # They must not become false Latin call-head failures or new D7 APIs.
        self.row(3, '101', 'коротко', 'повне', 'equal')
        self.put('lib/island-math-evidence.lisp',
                 '( (schema island-math-evidence/1) (rows (додати prolog proof)) )\n')
        self.put('lib/machine/authority-boundary.lisp',
                 '(machine-authority-boundary-1 (reverse-authority forbidden))\n')
        self.put('lib/active.lisp', '(foreign-live-call x)\n')
        report = mod.measure(self.root)
        self.assertEqual(report['metadata_files_excluded'], 2)
        self.assertEqual(report['active_latin_heads'], 1)
        self.assertEqual(
            [(site['file'], site['head']) for site in report['latin_sites']],
            [('lib/active.lisp', 'foreign-live-call')],
        )
        # The actual documents must remain declarative and readable;
        # no execution or remint is falsely claimed for metadata.
        repo = SCRIPT.resolve().parents[1]
        for path in ('lib/island-math-evidence.lisp',
                     'lib/machine/authority-boundary.lisp'):
            content = (repo / path).read_text(encoding='utf-8')
            self.assertTrue(mod.parse(content), path)
            self.assertNotIn('(визначити ', content)

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
        self.assertIn("(як-є канон-закон-результат)", source)  # Цитований український тег, не виклик
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
        # До вже виконуваних SENS-свідків LIFE-1 додається структурний
        # негатив: подвійний анонімний D5 value-call більше не дозволений.
        self.assertNotIn("((функція ", life_source)
        for helper in (
            "життя-поле-запису-продовжити",
            "життя-поле-запису-рядок",
            "життя-поле-запису-рядки",
        ):
            self.assertIn(f"(визначити {helper}", life_source)
        # Мапа вже перейшла на обчислювані D1 гілки, голого так немає.
        self.assertEqual(map_source.count("((атом? (як-є ()))"), 2)
        self.assertNotIn("(так", map_source)
        self.assertNotIn("#d1:0", life_source)
        self.assertIn("(нехай-послідовно ", life_source)
        # Чинний LIFE-1 виводить D1 без голих host-істин.
        # Керування перевіряє D3 ATOM, негативні гілки повертають D1 «ні».
        # Коментарі можуть містити історичний приклад (так ні);
        # перевіряємо лише виконуваний Lisp, зберігаючи рядки без змін.
        source_without_comments = []
        in_string = escaped = in_comment = False
        for char in life_source:
            if in_comment:
                if char == "\n":
                    source_without_comments.append(char)
                    in_comment = False
                else:
                    source_without_comments.append(" ")
                continue
            if in_string:
                source_without_comments.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == ";":
                source_without_comments.append(" ")
                in_comment = True
            else:
                source_without_comments.append(char)
                if char == '"':
                    in_string = True
        self.assertNotIn("(так ні)", "".join(source_without_comments))
        self.assertIn("(атом? (як-є ()))", life_source)
        # Чинні негативні гілки повертають точний D1 «ні» без
        # обхідного D3 ATOM від цитованої пари.
        self.assertIn("((атом? (як-є ())) ні)", life_source)
        self.assertNotIn("(атом? (як-є (()))", life_source)
        self.assertIn("(хибне? (атом? проєкції))", life_source)
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
        self.assertNotIn("(так ", active_first)
        self.assertNotIn(" так)", active_first)
        self.assertNotIn(" ні)", active_first)
        self.assertEqual(active_first.count("((атом? (як-є ()))"), 13)
        self.assertIn("(нехай-послідовно", active_first)
        self.assertNotIn("((функція ()", active_first)
        # Чинні D1-результати обчислює SENS через ATOM/QUOTE.
        # Meta-mutual має окремий маршрут міграції своїх голів.
        d1 = (root / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        self.assertIn("(0 (ук ні) (укр ні)", d1)
        self.assertIn("(1 (ук так) (укр так)", d1)
        self.assertIn("((атом? значення) (атом? (як-є (()))))", mutual)
        self.assertIn("((атом? (як-є ())) (тотожне? (перше значення) назва-замикання-рекурсивної-групи))", mutual)
        # Голі викличні «так»/«ні» — не D1-предикат самі по собі.
        active_mutual = "\n".join(line.split(";", 1)[0] for line in mutual.splitlines())
        self.assertNotRegex(active_mutual, r"\(\s*так(?=\s|\))")
        self.assertNotRegex(active_mutual, r"\(\s*ні(?=\s|\))")
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
  "scripts/check-domain-logic-laws.lisp": {
    # Відновлений зріз включає чинні українські описи законів у самому .lisp.
    # Після чинного D1-ремонту COND success не повертає історичне голе `так`.
    # Після перейменування схемного теґа domain-table/1 → domain-table-1.
    "sha": "ec069bfbf8e87bd6d3b2c2c79f8644d37d7fc649",
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
        """Відновити поточний schema-1 у бітовому inverse після окремих міграцій D3/D9 і D8."""
        if path != "scripts/check-domain-logic-laws.lisp":
            return source
        new_schema = '  (тотожне? (перше (читати-всі (читати-файл "lib/domains/d1.lisp"))) (як-є domain-table-1)))'
        old_schema = '  (101 (100 (110101001 (110110111 "lib/domains/d1.lisp"))) (001 domain-table-1)))'
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
                if path == "scripts/check-domain-bitness-laws.lisp":
                    assert_live_ukrainian_script(self, self.root, path, source)
                    self.assertIn("(як-є 00000000000)", source)
                    self.assertIn("(як-є 1111111111)", source)
                    self.assertIn("(ключі-без-повторів?", source)
                    self.assertNotRegex(source, r"\(\s*так(?=\s|\))")
                    self.assertNotIn("((атом? рядки) так)", source)
                    for width in range(1, 12):
                        # Точний D7 текстовий шлях замість недопущеного
                        # D8 SYMBOL->STRING у фізичному paired evaluator.
                        self.assertIn(
                            f'(визначити д{width} (завантажити-домен '
                            f'"lib/domains/d{width}.lisp"))',
                            source,
                        )
                        self.assertNotIn(
                            f"(символ-у-текст (як-є lib/domains/d{width}.lisp))",
                            source,
                        )
                    continue
                if path == "scripts/check-domain-logic-laws.lisp":
                    # Сучасний виконавчий D3-скрипт має власні виправлення
                    # COND/D9 і не повинен відновлювати SHA старого джерела.
                    # Однак законні парні клаузи та виконувані українські
                    # D3/D9/D8 голови мусять лишитися на місці.
                    mod.parse(source)
                    self.assertIn(
                        "(результат-перевірки (як-є ()))", source
                    )
                    self.assertIn(
                        "((атом? (як-є ())) (помилка-закону-доменної-логіки назва-закону))",
                        source,
                    )
                    self.assertIn(
                        '(читати-всі (читати-файл "lib/domains/d1.lisp"))',
                        source,
                    )
                    self.assertIn('(друкувати "DOMAIN-LOGIC-LAWS:', source)
                    self.assertNotIn("(110101001 (110110111", source)
                    continue
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
                if path == "scripts/check-domain-bitness-laws.lisp":
                    assert_live_ukrainian_script(self, self.root, path, source)
                    self.assertIn("(однакова-ємність?", source)
                    continue
                old = self._inverse(source, evidence["edits"])
                old = self._restore_prior_domain_logic_calls(path, old)
                before, after = old.splitlines(), source.splitlines()
                self.assertEqual(len(before), len(after))
                changed = [i + 1 for i, (a, b) in enumerate(zip(before, after)) if a != b]
                self.assertTrue(changed, f"{path}: потрібен свідок проєкції")
                for number in changed:
                    line = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"',
                                  lambda m: " " * len(m.group()), after[number - 1])
                    self.assertIsNone(raw_heads.search(line), f"{path}:{number}")
        capacity = (self.root / "scripts/check-domain-bitness-laws.lisp").read_text(encoding="utf-8")
        self.assertIn("(як-є 00000000000)", capacity)
        self.assertIn("(як-є 1111111111)", capacity)
        logic = (self.root / "scripts/check-domain-logic-laws.lisp").read_text(encoding="utf-8")
        self.assertIn("(менше? 2 3)", logic)
        self.assertIn('(тотожне? (перше (читати-всі (читати-файл "lib/domains/d1.lisp")))', logic)
        self.assertNotIn('(101 (100 (110101001 (110110111 "lib/domains/d1.lisp")))', logic)
        self.assertIn('(друкувати "DOMAIN-LOGIC-LAWS:', logic)
        self.assertNotIn('(11011011 "DOMAIN-LOGIC-LAWS:', logic)
    def test_negative_wrong_ukrainian_peer_breaks_exact_witness(self):
        path = "scripts/check-domain-bitness-laws.lisp"
        source = (self.root / path).read_text(encoding="utf-8")
        assert_live_ukrainian_script(self, self.root, path, source)
        bad = source.replace("(визначити завантажити-домен",
                             "(функція завантажити-домен", 1)
        self.assertNotEqual(source, bad)
        with self.assertRaises(AssertionError):
            assert_live_ukrainian_script(self, self.root, path, bad)

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
            # Separate D3/D5/D8/D9 executable heads, never infer old сід8
            # from byte equality. These three witnessed lines are reversible.
            exact_lines = (
                ("    (решта (знайти-за-ключем (як-є tier) приклад))))",
                 "    (011 (11100 (001 tier) приклад))))"),
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
                if path == "scripts/check-domain-table-readable.lisp":
                    mod.parse(current)
                    inverse = DomainTableReadableUkrMigrationTests._undo_exact_heads(current)
                    self.assertEqual(
                        DomainTableReadableUkrMigrationTests._redo_exact_heads(inverse),
                        current,
                    )
                    continue
                if path == "scripts/fixtures-for-tier.lisp":
                    assert_live_ukrainian_script(self, self.root, path, current)
                    self.assertIn("(решта (знайти-за-ключем (як-є tier) приклад))", current)
                    self.assertIn('(читати-всі (читати-файл "tests/fixtures/conformance.lisp"))', current)
                    continue
                if path == "scripts/check-domain-table-readable.lisp":
                    # Чинний виконавчий D24+/D1 закон замінив історичний
                    # git-blob попередника; перевіряємо поточну точну форму.
                    restored = self._pre_last_projection(path, current)
                    self.assertNotEqual(restored, current)
                    mod.parse(restored)
                    mod.parse(current)
                    self.assertIn("(однакова-кількість?", current)
                    continue
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
                if path == "scripts/check-domain-table-readable.lisp":
                    mod.parse(source)
                    inverse = DomainTableReadableUkrMigrationTests._undo_exact_heads(source)
                    self.assertEqual(
                        DomainTableReadableUkrMigrationTests._redo_exact_heads(inverse),
                        source,
                    )
                    self.assertNotIn("(тотожне? (довжина ", source)
                    self.assertNotIn("(тотожне? (текст-першого-ключа ", source)
                    continue
                if path == "scripts/fixtures-for-tier.lisp":
                    assert_live_ukrainian_script(self, self.root, path, source)
                    self.assertIn("(відібрати-приклади-за-рівнем", source)
                    self.assertNotIn("(надрукувати-відповідні", source)
                    self.assertNotIn("(друкувати (перше залишок))", source)
                    continue
                if path == "scripts/check-domain-table-readable.lisp":
                    # Старий знімок міграції більше не є еталоном чинного Lisp.
                    # Нових сирих машинних голів у виконуваному тексті немає.
                    self._pre_last_projection(path, source)
                    code = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"',
                                  lambda m: " " * len(m.group()), source)
                    self.assertFalse(encoded.search(code), f"{path}: сирі коди")
                    self.assertIn("(однакова-кількість?", source)
                    continue
                original = self.reverse(self._pre_last_projection(path, source), witness["edits"])
                before, after = original.splitlines(), self._pre_last_projection(path, source).splitlines()
                self.assertEqual(len(before), len(after))
                changed = [i + 1 for i, (a, b) in enumerate(zip(before, after)) if a != b]
                self.assertTrue(changed, f"{path}: потрібен свідок проєкції")
                for line in changed:
                    code = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"',
                                  lambda m: " " * len(m.group()), after[line - 1])
                    self.assertFalse(encoded.search(code), f"{path}:{line}: сирі коди")
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
        # Чинний CLI не має допущеного «прочитати»; допустимі
        # рівні конституційного корпусу явно зіставляються у SENS.
        for level in ("1", "2", "3"):
            self.assertIn(f'(тотожне? (перше *argv*) "{level}")', tier)
        self.assertNotIn("(прочитати (перше *argv*))", tier)
        self.assertNotIn("(11101010 (100 *argv*))", tier)
        self.assertIn("(визначити відібрати-приклади-за-рівнем", tier)
        self.assertNotIn("(визначити надрукувати-відповідні", tier)
        self.assertIn("(решта (знайти-за-ключем (як-є tier) приклад))", tier)
        self.assertNotIn("(друкувати (перше залишок))", tier)
        self.assertIn("(менше? (рівень-прикладу (перше залишок)) рівень)", tier)
        self.assertIn("(більше? (рівень-прикладу (перше залишок)) рівень)", tier)
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



class LiveDomainAndTierUkrProjectionTests(unittest.TestCase):
    """Чинні D1–D11 і відбір рівня: українські виклики, без відкату на SID8."""

    ROOT = Path(__file__).resolve().parents[1]

    @staticmethod
    def executable(source: str) -> str:
        # Не плутати рядки, коментарі та протокольні payload із викликами.
        return re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"',
                      lambda match: " " * len(match.group()), source)

    def test_domain_capacity_source_uses_current_ukrainian_laws(self):
        source = (self.ROOT / "scripts/check-domain-bitness-laws.lisp").read_text(encoding="utf-8")
        mod.parse(source)
        code = self.executable(source)
        for required in ("(визначити завантажити-домен",
                         "(визначити скопіювати-свідка",
                         "(визначити подвоїти-свідка",
                         "(читати-всі (читати-файл шлях))",
                         "(як-є 00000000000)", "(як-є 1111111111)",
                         "(друкувати "):
            self.assertIn(required, code)
        self.assertIn("(друкувати (як-є domain-bitness-laws-pass))", code)
        self.assertNotIn('(друкувати "', source)
        self.assertNotIn('"DOMAIN-BITNESS-LAWS: PASS', source)
        for obsolete in ("(load ", "(quote ", "(cond ", "(lambda ",
                         "(define ", "(0011 ", "(0010 "):
            self.assertNotIn(obsolete, code)
        # Два закони порожнього хвоста повертають справжній D1:1,
        # а не історичне текстове «так». Негативний mutant міняє біт на D1:0.
        істина = "((атом? рядки) (атом? (як-є ())))"
        хиба = "((атом? рядки) (атом? (як-є (()))))"
        self.assertEqual(code.count(істина), 2)
        self.assertNotIn("((атом? рядки) так)", code)
        mutated = code.replace(істина, хиба, 1)
        self.assertNotEqual(mutated, code)
        self.assertEqual(mutated.count(істина), 1)
        self.assertIn(хиба, mutated)
        # Два D1:1 та негативні гілки — справжні D3 ATOM,
        # не цитовані числові слова, які лише схожі на результати.
        d1_false = "(атом? (як-є (())))"
        d1_true = "(атом? (як-є ()))"
        self.assertIn("((атом? комірки) " + d1_false + ")", code)
        self.assertIn("(тотожне? (однакова-ємність? рядки ємність) " + d1_true + ")", code)
        self.assertIn("((тотожне? ключ (перше (перше рядки))) " + d1_false + ")", code)
        self.assertIn("(тотожне? (ключі-без-повторів? д3-дубль-усередині) " + d1_false + ")", code)
        self.assertNotIn("((атом? комірки) (як-є 0))", code)
        self.assertNotIn("(однакова-ємність? рядки ємність) (як-є 1)", code)
        # Негативний мутант повертає D1:YES при вичерпаній ємності.
        # Контроль структури не підміняє SENS runtime.
        wrong = code.replace("((атом? комірки) " + d1_false + ")",
                             "((атом? комірки) " + d1_true + ")", 1)
        self.assertNotEqual(wrong, code)
        self.assertNotIn("((атом? комірки) " + d1_false + ")", wrong)

    def test_domain_capacity_unary_seed_has_no_numeric_transport(self):
        # Статичний guard: реальне виконання законів лишається за SENS.
        source = (self.ROOT / "scripts/check-domain-bitness-laws.lisp").read_text(
            encoding="utf-8"
        )
        self.assertIn("(визначити свідок1 (як-є (())))", source)
        self.assertNotIn("(визначити свідок1 (як-є (0)))", source)

    def test_tier_selector_preserves_current_d3_d9_operators(self):
        source = (self.ROOT / "scripts/fixtures-for-tier.lisp").read_text(encoding="utf-8")
        mod.parse(source)
        code = self.executable(source)
        for required in ("(визначити потрібний-рівень",
                         "(визначити рівень-прикладу",
                         "(визначити відібрати-приклади-за-рівнем",
                         "(знайти-за-ключем (як-є tier) приклад)",
                         "(тотожне? (перше *argv*)",
                         "(читати-всі (читати-файл ",
                         "(за-умовою", "(менше? ", "(більше? "):
            self.assertIn(required, code)
        # CLI повертає структурне значення, а не викликає недопущений D9 друк.
        self.assertNotIn("(надрукувати-відповідні", code)
        self.assertNotIn("(друкувати ", code)
        # executable() стирає рядкові літерали; їх звіряємо з джерелом.
        for level in ("1", "2", "3"):
            self.assertIn(f'(тотожне? (перше *argv*) "{level}")', source)
        for obsolete in ("(load ", "(quote ", "(cond ", "(lambda ",
                         "(define ", "(0011 ", "(0010 ", "(11011011 "):
            self.assertNotIn(obsolete, code)

    def test_mutation_of_live_d4_definition_is_rejected(self):
        source = (self.ROOT / "scripts/check-domain-bitness-laws.lisp").read_text(encoding="utf-8")
        bad = source.replace("(визначити завантажити-домен",
                             "(функція завантажити-домен", 1)
        self.assertNotEqual(source, bad)
        self.assertNotIn("(визначити завантажити-домен", self.executable(bad))
        self.assertIn("(визначити завантажити-домен", self.executable(source))


class DomainTableReadableUkrMigrationTests(unittest.TestCase):
    """Чинна зворотна проєкція D5/D6/D8/D9; D1 відповіді генерує SENS."""

    SOURCE = Path(__file__).resolve().parents[1] / "scripts/check-domain-table-readable.lisp"
    # Ратифіковані координати перевіряються за поточними таблицями, а не
    # за історичним числом появ у незмінному source checkpoint.
    PEERS = (
        (5, "11010", "менше?", 1),
        (5, "11011", "більше?", 1),
        (6, "000100", "елемент-списку-за-індексом", 1),
        (8, "11110100", "значення-у-текст", 1),
        (8, "11110111", "однакові?", 8),
        (9, "110101001", "читати-всі", 1),
        (9, "110110111", "читати-файл", 1),
    )

    @classmethod
    def _undo_exact_heads(cls, source):
        import re
        for width, bits, ukr, count in reversed(cls.PEERS):
            pattern = re.compile(r"\(\s*" + re.escape(ukr) + r"(?=\s|\))")
            found = list(pattern.finditer(source))
            if len(found) != count:
                raise AssertionError(f"PEER_COUNT D{width}:{bits} {ukr}: {len(found)} != {count}")
            source = pattern.sub(lambda match: match.group().replace(ukr, bits), source)
        return source

    @classmethod
    def _redo_exact_heads(cls, source):
        import re
        for width, bits, ukr, count in cls.PEERS:
            pattern = re.compile(r"\(\s*" + re.escape(bits) + r"(?=\s|\))")
            found = list(pattern.finditer(source))
            if len(found) != count:
                raise AssertionError(f"WORD_COUNT D{width}:{bits}: {len(found)} != {count}")
            source = pattern.sub(lambda match: match.group().replace(bits, ukr), source)
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
        self.assertIn("(однакова-кількість? (довжина (рядки-домену д1))", source)
        self.assertNotIn("(тотожне? (довжина ", source)
        self.assertNotIn("(тотожне? (текст-першого-ключа ", source)
        # Немає незв'язаних D1 поверхонь «так»/«ні»: обидва результати
        # породжують точні живі D3 предикати без host-істини.
        self.assertNotIn("(так ", source)
        self.assertNotIn("(так)", source)
        self.assertNotIn(") ні)", source)
        self.assertIn("(менше? ліва права) (атом? (сполучити", source)
        self.assertIn("(більше? ліва права) (атом? (сполучити", source)
        inverse = self._undo_exact_heads(source)
        self.assertEqual(self._redo_exact_heads(inverse), source)
        mod.parse(source)
        mod.parse(inverse)

    def test_wrong_d9_peer_does_not_pass_projection_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        wrong = source.replace("(читати-всі", "(читати-файл", 1)
        self.assertNotEqual(wrong, source)
        with self.assertRaisesRegex(AssertionError, "PEER_COUNT"):
            self._undo_exact_heads(wrong)
        self.assertIn('"00000000"', source)
        self.assertIn("(довжина (рядки-домену д8))", source)
        # Фізичні шляхи ВСІХ десяти таблиць — точні цитовані D7 дані.
        # Сирий String у читачі T5M не має допущеної проєкції;
        # структурна перевірка доповнює (але не заміняє) реальний SENS runtime.
        for width in range(1, 11):
            with self.subTest(path_domain=f"D{width}"):
                self.assertIn(
                    f'(визначити д{width} (завантажити-домен (символ-у-текст (як-є lib/domains/d{width}.lisp))))',
                    source,
                )
                self.assertNotIn(f'"lib/domains/d{width}.lisp"', source)
        # Нові шляхи D7 — цитовані символи, не недопущені рядкові літерали.
        # Перевірку завантаження всіх десяти доменів виконано вище.
        # Не дублюємо історичний (завантажити-домен "lib/domains/…"),
        # бо він суперечить фактичному SENS Text7 ingress.
        for width, count in ((7, 128), (9, 512), (10, 1024)):
            with self.subTest(domain=f"D{width}", assertion="точна таблиця"):
                expected_key = "0" * width
                self.assertIn(
                    f'(перевірити-розширений-домен? д{width} {count} "{expected_key}")',
                    source,
                )
        self.assertIn("PASS files=10 rows=2046 widths=1..10", source)
        self.assertNotIn("PASS files=7 rows=382", source)


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
    # Точні зворотні SHA оновлено після українізації повідомлень;
    # ратифіковані коди та кількість виконуваних голів не змінено.
    # Тільки справжній живий генератор лишається в зворотній проєкції.
    # Два старі Rust-генератори — явні неперевірені якорі, не програми.
    SPECS = {
        "scripts/generate-rust-function-signatures.lisp": {},
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
            self.assertEqual(len(rows), 1, f"D{len(bits)}:{bits}: один власник")
            self.assertIn(f"(укр {surface})", rows[0], f"D{len(bits)}:{bits}: неузгоджена проєкція")
        if path == "scripts/generate-rust-function-signatures.lisp":
            # Працює повний новий генератор: історичний blob короткого
            # макета не можна вважати каноном виконуваного SENS.
            assert_live_ukrainian_script(self, self.ROOT, path, source)
            self.assertIn("(визначити подати-рядок-сигнатури", source)
            self.assertIn("(визначити згенерований-вміст", source)
            self.assertIn("(читати-файл шлях-джерела)", source)
            self.assertIn("(записати-файл шлях-результату згенерований-вміст)", source)
            self.assertIn(
                "(однакові? (читати-файл шлях-результату) згенерований-вміст)",
                source,
            )
            # Зворотний код кожної відомої голови відповідає ратифікації.
            edits = self._head_edits(source)
            self.assertTrue(edits)
            for edit in edits:
                self.assertEqual(edit["head"], self.PROJECTIONS[edit["bits"]])
            return
        edits = self._head_edits(source)
        actual = Counter(edit["bits"] for edit in edits)
        self.assertEqual(dict(actual), spec["counts"], f"{path}: відмінний точний перелік голів")
        self.assertTrue(edits, f"{path}: немає викличних голів")
        for edit in edits:
            self.assertEqual(edit["head"], self.PROJECTIONS[edit["bits"]])
        restored = source
        for edit in sorted(edits, key=lambda item: item["offset"], reverse=True):
            head, offset, bits = edit["head"], edit["offset"], edit["bits"]
            self.assertEqual(restored[offset:offset + len(head)], head)
            restored = restored[:offset] + bits + restored[offset + len(head):]
        self.assertEqual(self._blob_sha(restored), spec["blob"])
        mod.parse(source)
        mod.parse(restored)
        self.assertEqual(len(source.splitlines()), len(restored.splitlines()))
    def test_live_function_signature_generator_uses_exact_ukr_projection_and_inverse(self):
        for path in self.SPECS:
            with self.subTest(path=path):
                source = (self.ROOT / path).read_text(encoding="utf-8")
                self._assert_source_is_exact_ukr_projection(path, source)

    def test_retired_rust_generators_are_not_executable_or_fake_witnesses(self):
        # Виведений з ужитку генератор не повинен містити бутафорний
        # «якір» або вигадану готовність. Це не новий SENS-свідок.
        for path in (
            "scripts/build-constitution.lisp",
            "scripts/generate-rust-evaluator-dispatch.lisp",
            "scripts/generate-rust-semantic-registry.lisp",
        ):
            with self.subTest(path=path):
                source = (self.ROOT / path).read_text(encoding="utf-8")
                lines = [line.strip() for line in source.splitlines() if line.strip()]
                self.assertTrue(lines, f"{path}: відсутня позначка виведення")
                self.assertIn("ФАЙЛ ВИВЕДЕНО З УЖИТКУ", source)
                self.assertIn("Не виконуваний SENS-програма", source)
                self.assertTrue(all(line.startswith(";") for line in lines),
                                f"{path}: архівний файл знову має живий Lisp-код")
                self.assertNotIn("(визначити якір", source)
                self.assertNotIn("(status pass)", source)
                self.assertNotIn("(визначити надрукувати-приклад", source)
                self.assertNotIn("(класифікувати-рядкове-значення", source)

    def test_wrong_peer_mutation_is_rejected(self):
        path = "scripts/generate-rust-function-signatures.lisp"
        source = (self.ROOT / path).read_text(encoding="utf-8")
        edits = self._head_edits(source)
        first = next(edit for edit in edits if edit["bits"] == "0011")
        wrong = self.PROJECTIONS["0010"]
        mutated = source[:first["offset"]] + wrong + source[first["offset"] + len(first["head"]):]
        with self.assertRaises(AssertionError):
            self._assert_source_is_exact_ukr_projection(path, mutated)

if __name__ == '__main__':
    unittest.main(verbosity=2)
