"""Тести, які перевіряють, що код СЕНСУ *справді запускається*.

На відміну від статичних перевірок (баланс дужок, заборона літералів), тут
код **виконується**:

  1. Кожен CI-entry-point запускається як окрема програма (`subprocess`) і має
     завершитись очікуваним кодом виходу — ловить зламаний `__main__`, імпорт
     чи argparse, чого не бачать in-process тести.
  2. Наш власний читач (`scripts/migrate-three-pass.py`) токенізує й розбирає
     реальні мовні джерела: `lib/core4.lisp` і всі `lib/domains/d*.lisp`.
  3. Наш власний кодек (`scripts/sens_t5_codec.py`) виконується на реальних
     мовних файлах: `.sens` має пережити decode → encode байт-у-байт, а
     extensionless-програма (нулі й одиниці через пропуск) — encode → decode.
  4. Кожне Python-джерело має компілюватися (`py_compile`).

Усе детерміноване, без мережі, без Rust/Zig.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import py_compile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"не вдалось завантажити {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


three_pass = _load("sens_three_pass_for_code_runs", SCRIPTS / "migrate-three-pass.py")
codec = _load("sens_t5_codec_for_code_runs", SCRIPTS / "sens_t5_codec.py")


def run_entrypoint(*args: str, timeout: int = 120):
    """Запустити entry-point як справжню програму й повернути CompletedProcess."""
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)


class PythonEntrypointsRunTests(unittest.TestCase):
    """Кожен крок CI має реально запускатись як програма."""

    def _assert_runs(self, *args, expected_rc=0):
        p = run_entrypoint(*args)
        combined = p.stdout + p.stderr
        self.assertNotIn("Traceback (most recent call last)", combined,
                         f"{args} впав із трейсбеком:\n{combined[-1500:]}")
        self.assertEqual(p.returncode, expected_rc,
                         f"{args}: rc={p.returncode} (чекали {expected_rc})\n{combined[-1500:]}")
        return p

    def test_definitions_check_runs(self):
        self._assert_runs("scripts/check-sens-definitions.py")

    def test_semantic_registry_check_runs(self):
        self._assert_runs("scripts/check_semantic_registry.py")

    def test_alias_identity_check_runs(self):
        self._assert_runs("scripts/check_alias_identity.py")

    def test_domain_projection_audit_runs(self):
        self._assert_runs("scripts/audit_ukrainian_domain_projections.py")

    def test_ukr_projection_report_runs(self):
        p = self._assert_runs("scripts/report_ukr_projection_progress.py", "--no-annotation")
        self.assertIn("УКР-ПРОЄКЦІЯ", p.stdout)

    def test_ukr_projection_report_hard_mode_is_red(self):
        # поріг 100 недосяжний зараз -> крок мусить бути червоним (rc=1)
        p = run_entrypoint("scripts/report_ukr_projection_progress.py",
                           "--min-pairs-pct", "100", "--no-annotation")
        self.assertEqual(p.returncode, 1)
        self.assertIn("НЕ ЗАВЕРШЕНА", p.stdout)

    def test_ukr_projection_report_bad_root_is_usage_error(self):
        p = run_entrypoint("scripts/report_ukr_projection_progress.py", "--root", "/no/such/dir")
        self.assertEqual(p.returncode, 2)


class ReaderRunsTests(unittest.TestCase):
    """Наш читач має розібрати реальні мовні джерела без помилок."""

    def _parse(self, path: Path):
        source = path.read_text(encoding="utf-8")
        tokens = three_pass.tokenize(three_pass.strip_comments(source))
        self.assertTrue(tokens, f"{path}: читач не побачив жодного токена")
        forms = three_pass.Parser(tokens).parse_program()
        self.assertTrue(forms, f"{path}: читач не побачив жодної форми")
        return forms

    def test_reads_live_core(self):
        core = ROOT / "lib" / "core4.lisp"
        self.assertTrue(core.is_file())
        self._parse(core)

    def test_reads_every_domain_table(self):
        tables = sorted((ROOT / "lib" / "domains").glob("d*.lisp"))
        self.assertGreaterEqual(len(tables), 11)
        for path in tables:
            with self.subTest(table=path.name):
                self._parse(path)

    def test_reader_rejects_unbalanced_source(self):
        tokens = three_pass.tokenize("(a (b)")
        with self.assertRaises(three_pass.MigrationError):
            three_pass.Parser(tokens).parse_program()


class TranslationSelectorsUkrProjectionTests(unittest.TestCase):
    """Ратифікована укр-проєкція шести дійсних селекторів перекладу."""

    ORIGINAL_BLOB = "c1edb3da644cffb86507d964c9f7474c685c1f76"
    SELECTORS = (
        ("translation-kind", "proposal", 5, "10011"),
        ("translation-source", "proposal", 6, "100111"),
        ("translation-payload", "proposal", 9, "110110101"),
        ("translation-review-code", "review", 5, "10011"),
        ("translation-review-proposal", "review", 6, "100111"),
        ("translation-review-detail", "review", 9, "110110101"),
    )

    def _restore_original(self, source):
        from domain_tables import read_domain_table
        surfaces = {
            width: {row.bits: row.ukr for row in read_domain_table(
                ROOT / "lib" / "domains" / f"d{width}.lisp"
            )}
            for width in (4, 5, 6, 9)
        }
        self.assertEqual(surfaces[4]["0010"], "функція")
        for name, argument, width, bits in self.SELECTORS:
            peer = surfaces[width][bits]
            new = f"(визначити {name}\n  (функція ({argument}) ({peer} {argument})))"
            old = f"(визначити {name}\n  (0010 ({argument}) ({bits} {argument})))"
            self.assertEqual(source.count(new), 1, f"хибна укр-проєкція {name}")
            self.assertNotIn(old, source)
            source = source.replace(new, old, 1)
        return source

    @staticmethod
    def _git_blob_sha(source):
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()

    def test_ratified_peers_and_exact_inverse_preserve_original(self):
        source = (ROOT / "lib" / "translation.lisp").read_text(encoding="utf-8")
        parsed = three_pass.Parser(
            three_pass.tokenize(three_pass.strip_comments(source))
        ).parse_program()
        self.assertTrue(parsed)
        self.assertEqual(
            self._git_blob_sha(self._restore_original(source)), self.ORIGINAL_BLOB
        )

    def test_wrong_selector_peer_is_rejected(self):
        source = (ROOT / "lib" / "translation.lisp").read_text(encoding="utf-8")
        self.assertIn("(третє proposal)", source)
        mutated = source.replace("(третє proposal)", "(четверте proposal)", 1)
        with self.assertRaises(AssertionError):
            self._restore_original(mutated)


class CodecRunsTests(unittest.TestCase):
    """Наш кодек має виконатись на реальних мовних файлах."""

    def test_sens_roundtrips_byte_for_byte(self):
        files = sorted((ROOT / "tests" / "semantic").glob("*.sens"))
        self.assertTrue(files, "немає жодного .sens для перевірки")
        # Explicit fixture routing: transport is not inferred from payload bytes.
        t5m_files = {"ukr-d24-existing-functions.sens"}
        self.assertTrue(t5m_files <= {path.name for path in files},
                        "втрачено фізичний T5M-свідок")
        for path in files[:40]:
            with self.subTest(sens=path.name):
                data = path.read_bytes()
                if path.name in t5m_files:
                    words = codec.decode_t5m_bytes(data)
                    view = path.with_suffix("").read_text(encoding="utf-8")
                    self.assertEqual(words, codec.parse_t5m_words(view),
                                     f"{path.name}: T5M не відповідає точному bit-view")
                    restored = codec.encode_t5m_projection(" ".join(words))
                else:
                    words = codec.decode_bytes(data)
                    restored = codec.encode_words(words)
                self.assertTrue(words)
                self.assertEqual(restored, data,
                                 f"{path.name}: decode→encode не відтворив байти")

    def test_t5m_fixture_rejects_truncated_group(self):
        path = ROOT / "tests" / "semantic" / "ukr-d24-existing-functions.sens"
        data = path.read_bytes()
        self.assertEqual(len(data) % 3, 0)
        with self.assertRaisesRegex(codec.SensT5Error, "multiple of three"):
            codec.decode_t5m_bytes(data[:-1])

    def test_extensionless_program_roundtrips(self):
        candidates = [
            ROOT / "tests" / "fixtures" / "core1-domain-canary" / "second",
            ROOT / "tests" / "fixtures" / "core1-third-domain-canary" / "third",
            ROOT / "tests" / "fixtures" / "core1-fourth-domain-canary" / "fourth",
        ]
        seen = 0
        for path in candidates:
            if not path.is_file():
                continue
            with self.subTest(program=path.name):
                src = path.read_text(encoding="utf-8")
                packed = codec.encode_projection(src)
                self.assertEqual(codec.decode_bytes(packed), codec.parse_words(src))
                seen += 1
        self.assertGreater(seen, 0, "не знайдено жодної extensionless-програми")

    def test_codec_fails_closed_on_non_binary(self):
        with self.assertRaises(codec.SensT5Error):
            codec.encode_projection("101 foo 11")

    def test_codec_fails_closed_on_empty(self):
        with self.assertRaises(codec.SensT5Error):
            codec.encode_projection("   ")


class PythonSourcesCompileTests(unittest.TestCase):
    """Кожне Python-джерело має компілюватися."""

    def test_scripts_and_tests_compile(self):
        broken = []
        for path in sorted(SCRIPTS.glob("*.py")) + sorted((ROOT / "tests").glob("*.py")):
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                broken.append(f"{path.name}: {exc.msg}")
        self.assertEqual(broken, [], f"не компілюються: {broken}")


class CodecUkrProjectionTests(unittest.TestCase):
    """The D2 codec uses ratified Ukrainian call heads without changing its data."""

    SOURCE = ROOT / "lib" / "codec-d2.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    ORIGINAL_BLOB = "79d49cd2e89e657e431872bd1e4c9e85174404c9"
    HEADS = {
        "0011": "визначити", "0010": "функція", "001": "як-є",
        "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
    }
    RESTORE = {surface: bits for bits, surface in HEADS.items()}
    RESTORE_RE = re.compile(
        r"[(](" + "|".join(re.escape(surface) for surface in HEADS.values()) + r")(?=\s)"
    )
    RAW_RE = re.compile(r"[(](" + "|".join(HEADS.keys()) + r")(?=\s)")

    @staticmethod
    def git_blob_sha(data: bytes) -> str:
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def restore_heads(self, source: str) -> str:
        return self.RESTORE_RE.sub(lambda match: "(" + self.RESTORE[match.group(1)], source)

    def assert_ratified(self, table_path: Path, bits: str,
                        surface: str, english: str, lisp_name: str):
        table = table_path.read_text(encoding="utf-8")
        rows = [
            line for line in table.splitlines()
            if re.match(rf"^\s*\({re.escape(bits)}\s", line)
        ]
        self.assertEqual(len(rows), 1, f"{bits}: expected one exact-width row")
        self.assertIn(f"(укр {surface})", rows[0])
        self.assertIn(f"(en {english})", rows[0])
        self.assertIn(f"(LISP {lisp_name})", rows[0])

    def test_codec_d2_uses_exact_ukr_operator_heads(self):
        for bits, surface, english, name in (
            ("001", "як-є", "quote", "QUOTE"),
            ("010", "атом?", "atom?", "ATOM"),
            ("011", "решта", "cdr", "CDR"),
            ("100", "перше", "car", "CAR"),
            ("101", "тотожне?", "eq?", "EQ"),
            ("110", "за-умовою", "cond", "COND"),
            ("111", "сполучити", "cons", "CONS"),
        ):
            self.assert_ratified(self.D3, bits, surface, english, name)
        for bits, surface, english, name in (
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0011", "визначити", "define", "DEFINE"),
        ):
            self.assert_ratified(self.D4, bits, surface, english, name)

        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertIsNone(self.RAW_RE.search(source), "raw D3/D4 operator heads remain")
        for surface, count in (
            ("визначити", 14), ("функція", 11), ("як-є", 21),
            ("атом?", 5), ("решта", 12), ("перше", 11),
            ("тотожне?", 13), ("за-умовою", 8), ("сполучити", 11),
        ):
            pattern = re.compile(r"[(]" + re.escape(surface) + r"(?=\s)")
            self.assertEqual(len(pattern.findall(source)), count, surface)

        # Marker labels are D11-projected data and must remain unchanged.
        for marker in ("d2-open", "d2-close", "d2-sep", "d2-dot"):
            self.assertIn(marker, source)
        for alias in ("A", "B", "C", "D", "E", "F", "G", "R", "Q", "S", "U", "P"):
            self.assertIn(f"(визначити {alias} ", source)

    def test_inverse_projection_restores_every_original_source_byte(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        restored = self.restore_heads(source).encode("utf-8")
        self.assertEqual(
            self.git_blob_sha(restored), self.ORIGINAL_BLOB,
            "inverse head substitution must reconstruct the exact parent Git blob",
        )

    def test_wrong_ukr_peer_fails_the_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace("(тотожне? (як-є t)", "(порожнє? (як-є t)", 1)
        self.assertNotEqual(mutant, source)
        restored = self.restore_heads(mutant).encode("utf-8")
        self.assertNotEqual(
            self.git_blob_sha(restored), self.ORIGINAL_BLOB,
            "unratified or wrong surface must not pass the inverse witness",
        )



class SiDerivedUkrProjectionTests(unittest.TestCase):
    """Migrate exact D4/D5/D8 call heads without changing SI arithmetic data."""

    SOURCE = ROOT / "lib" / "si-derived.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    D5 = ROOT / "lib" / "domains" / "d5.lisp"
    D8 = ROOT / "lib" / "domains" / "d8.lisp"
    ORIGINAL_BLOB = "0074e9266a09e24804fb0798723b02a863f5ac66"

    @staticmethod
    def git_blob_sha(data: bytes) -> str:
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def assert_ratified(self, table_path: Path, bits: str,
                        surface: str, english: str, lisp_name: str):
        table = table_path.read_text(encoding="utf-8")
        rows = [
            line for line in table.splitlines()
            if re.match(rf"^\s*\({re.escape(bits)}\s", line)
        ]
        self.assertEqual(len(rows), 1, f"{bits}: expected one exact-width row")
        self.assertIn(f"(укр {surface})", rows[0])
        self.assertIn(f"(en {english})", rows[0])
        self.assertIn(f"(LISP {lisp_name})", rows[0])

    @staticmethod
    def restore_heads(source: str) -> str:
        # Exact inverse for executable list heads only. Comments, strings,
        # numeric values and quoted SI records otherwise remain unchanged.
        inverse = {
            "визначити": "0011",
            "помножити": "10110",
            "поділити": "11110110",
        }
        pattern = re.compile(
            r"[(](" + "|".join(re.escape(name) for name in inverse) + r")(?=\s)"
        )
        return pattern.sub(lambda match: "(" + inverse[match.group(1)], source)

    def test_si_derived_uses_ratified_ukr_heads_and_preserves_arithmetic(self):
        self.assert_ratified(self.D4, "0011", "визначити", "define", "DEFINE")
        self.assert_ratified(self.D5, "10110", "помножити", "times", "TIMES")
        self.assert_ratified(self.D8, "11110110", "поділити", "divide", "DIVIDE")

        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\(визначити(?=\s)", source)), 7)
        self.assertEqual(len(re.findall(r"\(помножити(?=\s)", source)), 7)
        self.assertEqual(len(re.findall(r"\(поділити(?=\s)", source)), 4)
        self.assertIsNone(
            re.search(r"\((?:0011|10110|11110110)(?=\s)", source),
            "ratified call heads must use their exact Ukrainian projection",
        )

        for name in (
            "si:faraday-constant", "si:molar-gas-constant",
            "si:josephson-constant", "si:von-klitzing-constant",
            "si:magnetic-flux-quantum", "si:conductance-quantum",
            "si:molar-planck-constant",
        ):
            self.assertIn(f"(визначити {name}", source)
        restored = self.restore_heads(source)
        self.assertEqual(
            re.findall(r"(?<![\w])\d+\s*/\s*\d+", restored),
            re.findall(r"(?<![\w])\d+\s*/\s*\d+", source),
            "SI exact rational values must not change during surface migration",
        )

    def test_inverse_projection_restores_all_original_bytes(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        restored = self.restore_heads(source).encode("utf-8")
        self.assertEqual(self.git_blob_sha(restored), self.ORIGINAL_BLOB)

    def test_wrong_ukr_peer_fails_the_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace(
            "(помножити si:avogadro-constant",
            "(множити-нечинне si:avogadro-constant",
            1,
        )
        self.assertNotEqual(mutant, source)
        restored = self.restore_heads(mutant).encode("utf-8")
        self.assertNotEqual(
            self.git_blob_sha(restored), self.ORIGINAL_BLOB,
            "wrong/unratified Ukrainian peer must fail the inverse witness",
        )




class Life1RemainingUkrProjectionTests(unittest.TestCase):
    """Перевіряє чинні D3/D4 surface, не робить із Python семантичний SENS."""

    SOURCE = ROOT / "lib" / "life-1-scheduler.lisp"
    D1 = ROOT / "lib" / "domains" / "d1.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    ORIGINAL_BLOB = "a287485556480390e25e80492fdeb4cd933aab54"

    @staticmethod
    def restore(source: str) -> str:
        # 12 верхніх D4 DEFINE і одна точно локалізована гілка D3 ATOM.
        # Другий, раніше вже український ATOM(праве) не зачіпати.
        source = re.sub(r"(?m)^\(визначити(?=\s)", "(0011", source)
        return source.replace(
            "((атом? праве) ні)", "((010 праве) #d1:0)"
        )

    @staticmethod
    def blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_exact_ratified_ukr_and_thirteen_current_heads(self):
        d3 = self.D3.read_text(encoding="utf-8").splitlines()
        d4 = self.D4.read_text(encoding="utf-8").splitlines()
        atom = [line for line in d3 if re.match(r"^\s*\(010\s", line)]
        define = [line for line in d4 if re.match(r"^\s*\(0011\s", line)]
        self.assertEqual(len(atom), 1)
        self.assertEqual(len(define), 1)
        self.assertIn("(укр атом?)", atom[0])
        self.assertIn("(LISP ATOM)", atom[0])
        self.assertIn("(укр визначити)", define[0])
        self.assertIn("(LISP DEFINE)", define[0])
        self.assertIn("(0 (ук ні) (укр ні)", self.D1.read_text(encoding="utf-8"))

        src = self.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^\(визначити(?=\s)", src)), 12)
        self.assertEqual(src.count("((атом? праве) ні)"), 1)
        self.assertNotRegex(src, r"(?m)^\(0011(?=\s)")
        self.assertNotIn("((010 праве) #d1:0)", src)
        self.assertEqual(src.count("(001001 "), 2)  # D6 LET* untouched
        for original_data in ("#d1:0", "#d1:1",
                              "(як-є (scheduler-selection none))",
                              "(як-є producer)"):
            self.assertIn(original_data, src)

    def test_inverse_projection_recovers_original_git_blob(self):
        src = self.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(self.blob_sha(self.restore(src)), self.ORIGINAL_BLOB)

    def test_wrong_domain_or_wrong_peer_is_rejected(self):
        src = self.SOURCE.read_text(encoding="utf-8")
        for mutant in (
            src.replace("((атом? праве) ні)",
                        "((сполучити праве) ні)", 1),
            src.replace("(визначити життя--рівні?",
                        "(функція життя--рівні?", 1),
        ):
            self.assertNotEqual(mutant, src)
            self.assertNotEqual(
                self.blob_sha(self.restore(mutant)), self.ORIGINAL_BLOB
            )


class CompilerNucleusUkrDomainProjectionTests(unittest.TestCase):
    """Exact-width D3/D4 operators use current Ukrainian peers; quoted data stays data."""

    SOURCE = ROOT / "lib" / "compiler-nucleus.lisp"
    D1 = ROOT / "lib" / "domains" / "d1.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    ORIGINAL_BLOB = "a7000108be4ca2a3a2b9961b7f8d70e9dfccdea0"
    BINARY_TO_UKR = {
        "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
        "0010": "функція", "0011": "визначити",
    }
    EXPECTED_INVERSE_COUNTS = {
        "як-є": 40, "атом?": 25, "решта": 41, "перше": 34,
        "тотожне?": 24, "за-умовою": 35, "сполучити": 25,
        "функція": 57, "визначити": 57,
    }

    @staticmethod
    def _rewrite_heads(source: str, mapping: dict[str, str]):
        tokens = []
        i = 0
        while i < len(source):
            ch = source[i]
            if ch.isspace():
                i += 1
                continue
            if ch == ";":
                while i < len(source) and source[i] != "\n":
                    i += 1
                continue
            if ch == '"':
                start = i
                i += 1
                escaped = False
                while i < len(source):
                    current = source[i]
                    i += 1
                    if escaped:
                        escaped = False
                    elif current == "\\":
                        escaped = True
                    elif current == '"':
                        break
                else:
                    raise ValueError(f"unclosed string at {start}")
                tokens.append({"kind": "string", "text": source[start:i],
                               "start": start, "end": i})
                continue
            if ch in "()":
                tokens.append({"kind": "open" if ch == "(" else "close",
                               "text": ch, "start": i, "end": i + 1})
                i += 1
                continue
            start = i
            while (i < len(source) and not source[i].isspace()
                   and source[i] not in '();"'):
                i += 1
            if i == start:
                i += 1
                continue
            tokens.append({"kind": "atom", "text": source[start:i],
                           "start": start, "end": i})

        cursor = 0

        def parse_expr():
            nonlocal cursor
            if cursor >= len(tokens):
                raise ValueError("unexpected end of source")
            token = tokens[cursor]
            if token["kind"] == "close":
                raise ValueError(f"unexpected close at {token['start']}")
            if token["kind"] != "open":
                cursor += 1
                return {"kind": "atom", "token": token, "items": None}
            open_token = token
            cursor += 1
            items = []
            while cursor < len(tokens) and tokens[cursor]["kind"] != "close":
                items.append(parse_expr())
            if cursor >= len(tokens):
                raise ValueError(f"unclosed list at {open_token['start']}")
            cursor += 1
            return {"kind": "list", "items": items}

        roots = []
        while cursor < len(tokens):
            roots.append(parse_expr())
        edits = []
        counts = {}
        unexpected = []

        def visit(node, quoted=False):
            if node["kind"] != "list":
                return
            items = node["items"]
            head = items[0] if items else None
            token = head["token"] if head and head["kind"] == "atom" else None
            head_text = token["text"] if token and token["kind"] == "atom" else None
            if not quoted and head_text and re.fullmatch(r"[01]{3,4}", head_text):
                if head_text not in mapping:
                    unexpected.append(head_text)
                else:
                    edits.append((token["start"], token["end"], mapping[head_text]))
                    counts[head_text] = counts.get(head_text, 0) + 1
            elif not quoted and head_text in mapping:
                edits.append((token["start"], token["end"], mapping[head_text]))
                counts[head_text] = counts.get(head_text, 0) + 1
            in_quote = head_text in {"001", "як-є"}
            start_child = 1 if head and head["kind"] == "atom" else 0
            for child in items[start_child:]:
                visit(child, quoted or in_quote)

        for root in roots:
            visit(root)
        rewritten = source
        for start, end, replacement in sorted(edits, reverse=True):
            rewritten = rewritten[:start] + replacement + rewritten[end:]
        return rewritten, counts, unexpected, len(roots)

    @staticmethod
    def _git_blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_no_active_binary_heads_and_all_peers_are_ratified(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        projected, rewrites, unexpected, _ = self._rewrite_heads(source, self.BINARY_TO_UKR)
        self.assertEqual(rewrites, {}, "active numeric operator heads remain")
        self.assertEqual(unexpected, [], "unknown numeric D3/D4 operator head")
        self.assertEqual(projected, source)

        for bits, peer, en, lisp in (
            ("001", "як-є", "quote", "QUOTE"),
            ("010", "атом?", "atom?", "ATOM"),
            ("011", "решта", "cdr", "CDR"),
            ("100", "перше", "car", "CAR"),
            ("101", "тотожне?", "eq?", "EQ"),
            ("110", "за-умовою", "cond", "COND"),
            ("111", "сполучити", "cons", "CONS"),
        ):
            row = [line for line in self.D3.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*\(" + bits + r"\s", line)]
            self.assertEqual(len(row), 1, f"D3:{bits} must have one current row")
            self.assertIn(f"(укр {peer})", row[0])
            self.assertIn(f"(en {en})", row[0])
            self.assertIn(f"(LISP {lisp})", row[0])
        for bits, peer, en, lisp in (
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0011", "визначити", "define", "DEFINE"),
        ):
            row = [line for line in self.D4.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*\(" + bits + r"\s", line)]
            self.assertEqual(len(row), 1, f"D4:{bits} must have one current row")
            self.assertIn(f"(укр {peer})", row[0])
            self.assertIn(f"(en {en})", row[0])
            self.assertIn(f"(LISP {lisp})", row[0])

        # D1:1 is rendered by its ratified Ukrainian peer; D1:0 is unchanged.
        self.assertEqual(source.count("#d1:1"), 2)
        self.assertEqual(source.count("(так "), 3)
        self.assertIn("#d1:0", source)
        self.assertIn('(1 (ук так) (укр так)', self.D1.read_text(encoding="utf-8"))
        self.assertIn("decompose", source)

    def test_inverse_projection_recovers_exact_parent_blob_and_head_census(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        reverse = {peer: bits for bits, peer in self.BINARY_TO_UKR.items()}
        reverse["так"] = "#d1:1"
        restored, counts, unexpected, forms = self._rewrite_heads(source, reverse)
        self.assertEqual(counts, {**self.EXPECTED_INVERSE_COUNTS, "так": 3})
        self.assertEqual(unexpected, [])
        self.assertEqual(self._git_blob_sha(restored), self.ORIGINAL_BLOB)
        self.assertEqual(forms, 57)
        tokens = three_pass.tokenize(three_pass.strip_comments(source))
        parsed = three_pass.Parser(tokens).parse_program()
        self.assertEqual(len(parsed), 57)

    def test_wrong_peer_fails_exact_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace("(за-умовою", "(тотожне?", 1)
        self.assertNotEqual(mutant, source)
        reverse = {peer: bits for bits, peer in self.BINARY_TO_UKR.items()}
        reverse["так"] = "#d1:1"
        restored, _, _, _ = self._rewrite_heads(mutant, reverse)
        self.assertNotEqual(self._git_blob_sha(restored), self.ORIGINAL_BLOB)



class MinimalRuntimeProfileUkrProjectionTests(unittest.TestCase):
    """Exact D3/D4/D6 callheads use ratified укр peers; profile data stays inert."""

    SOURCE = ROOT / "lib" / "machine" / "profile" / "minimal-runtime-x86-64.lisp"
    ORIGINAL_BLOB = "6ec6e73e7b32c4f3f2c49f0464d191c606d2e1a2"
    EXPECTED_OLD_HEAD_COUNTS = {
        "100": 7, "101": 1, "110": 5, "111": 2, "1110": 23, "1111": 1,
        "0011": 24, "001": 37, "0010": 21, "010": 9, "011": 8, "001000": 1,
    }

    def _projection(self):
        mapping = {}
        for bits in self.EXPECTED_OLD_HEAD_COUNTS:
            width = len(bits)
            self.assertIn(width, (3, 4, 6), f"unexpected exact domain width for {bits}")
            table = ROOT / "lib" / "domains" / f"d{width}.lisp"
            rows = [
                line for line in table.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(rows), 1, f"exact resident row must be unique: D{width}:{bits}")
            peer = re.search(r"\(укр\s+([^\s()]+)\)", rows[0])
            self.assertIsNotNone(peer, f"D{width}:{bits} has no named укр projection")
            mapping[bits] = peer.group(1)
        self.assertEqual(
            len(mapping), len(set(mapping.values())),
            "this source slice must remain exactly reversible by domain-qualified identities",
        )
        return mapping

    @staticmethod
    def _git_blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_profile_has_no_active_binary_callheads_and_uses_ratified_ukr(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        projected, counts, unexpected, forms = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            source, mapping
        )
        self.assertEqual(counts, {}, "active exact D3/D4/D6 numeric callheads remain")
        self.assertEqual(unexpected, [], "unmapped active domain callhead")
        self.assertEqual(projected, source, "profile is not on the ratified укр projection")
        self.assertEqual(forms, 24)
        self.assertNotIn("(001000", source, "D6:001000 must use its exact укр peer")
        for bits, peer in mapping.items():
            row = [
                line for line in (ROOT / "lib" / "domains" / f"d{len(bits)}.lisp")
                .read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(row), 1)
            self.assertIn(f"(укр {peer})", row[0])

    def test_inverse_projection_restores_exact_original_blob_and_all_139_heads(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        reverse = {peer: bits for bits, peer in mapping.items()}
        self.assertEqual(len(reverse), len(mapping))
        restored, counts, unexpected, forms = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            source, reverse
        )
        self.assertEqual(
            counts,
            {mapping[bits]: n for bits, n in self.EXPECTED_OLD_HEAD_COUNTS.items()},
        )
        self.assertEqual(unexpected, [])
        self.assertEqual(forms, 24)
        self.assertEqual(self._git_blob_sha(restored), self.ORIGINAL_BLOB)

    def test_wrong_domain_peer_fails_the_exact_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        reverse = {peer: bits for bits, peer in mapping.items()}
        mutant = source.replace("(за-умовою", "(тотожне?", 1)
        self.assertNotEqual(mutant, source)
        restored, _, _, _ = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            mutant, reverse
        )
        self.assertNotEqual(self._git_blob_sha(restored), self.ORIGINAL_BLOB)


if __name__ == "__main__":
    unittest.main(verbosity=2)
