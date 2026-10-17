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

import importlib.util
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
