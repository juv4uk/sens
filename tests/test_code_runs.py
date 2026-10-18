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


class CodecRunsTests(unittest.TestCase):
    """Наш кодек має виконатись на реальних мовних файлах."""

    def test_sens_roundtrips_byte_for_byte(self):
        files = sorted((ROOT / "tests" / "semantic").glob("*.sens"))
        self.assertTrue(files, "немає жодного .sens для перевірки")
        for path in files[:40]:
            with self.subTest(sens=path.name):
                data = path.read_bytes()
                words = codec.decode_bytes(data)
                self.assertTrue(words)
                self.assertEqual(codec.encode_words(words), data,
                                 f"{path.name}: decode→encode не відтворив байти")

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
    """Migrate only the ratified D4 DEFINE surface, not SI arithmetic semantics."""

    SOURCE = ROOT / "lib" / "si-derived.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    ORIGINAL_BLOB = "0074e9266a09e24804fb0798723b02a863f5ac66"

    @staticmethod
    def git_blob_sha(data: bytes) -> str:
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_si_derived_uses_ratified_ukr_define_and_preserves_arithmetic(self):
        table = self.D4.read_text(encoding="utf-8")
        rows = [
            line for line in table.splitlines()
            if re.match(r"^\s*\(0011\s", line)
        ]
        self.assertEqual(len(rows), 1)
        self.assertIn("(укр визначити)", rows[0])
        self.assertIn("(en define)", rows[0])
        self.assertIn("(LISP DEFINE)", rows[0])

        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(source.count("(визначити "), 7)
        self.assertNotIn("(0011 ", source)
        self.assertEqual(len(re.findall(r"\(10110(?=\s)", source)), 7,
                         "D5 exact multiplication heads must be unchanged")
        self.assertEqual(len(re.findall(r"\(11110110(?=\s)", source)), 4,
                         "unresolved historical division heads must be unchanged")
        for name in (
            "si:faraday-constant", "si:molar-gas-constant",
            "si:josephson-constant", "si:von-klitzing-constant",
            "si:magnetic-flux-quantum", "si:conductance-quantum",
            "si:molar-planck-constant",
        ):
            self.assertIn(f"(визначити {name}", source)

    def test_inverse_define_projection_restores_all_original_bytes(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        restored = re.sub(r"\(визначити(?=\s)", "(0011", source).encode("utf-8")
        self.assertEqual(self.git_blob_sha(restored), self.ORIGINAL_BLOB)

    def test_wrong_define_surface_fails_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace("(визначити si:faraday-constant",
                                "(визначити si:invalid-faraday-constant", 1)
        self.assertNotEqual(mutant, source)
        restored = re.sub(r"\(визначити(?=\s)", "(0011", mutant).encode("utf-8")
        self.assertNotEqual(self.git_blob_sha(restored), self.ORIGINAL_BLOB)



if __name__ == "__main__":
    unittest.main(verbosity=2)
