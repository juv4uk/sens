#!/usr/bin/env python3
"""Поточна українська Core1 FOURTH: точні слова, фізичний спадковий свідок і T5M.
Python перевіряє тільки транспорт; не імітує SENS-eval і не публікує .sens.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/migrate-three-pass.py"
FIXTURE = ROOT / "tests/fixtures/core1-fourth-domain-canary"
SOURCE = FIXTURE / "fourth.lisp"
PHYSICAL = FIXTURE / "fourth.sens"
VIEW = FIXTURE / "fourth"
EXPECTED_WORDS = "10 100 00 10 011 00 10 011 00 10 011 00 10 111 00 10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 111 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 00 10 001 00 000 01 01 01 01 01 01 01 01 01\n"
EXPECTED_BYTES = bytes.fromhex("663864896489648967896389068967896389068967896389068967896789638906896389068c15a7123b2eb18c2eb3")

spec = importlib.util.spec_from_file_location("core1_fourth_current_migration", SCRIPT)
assert spec and spec.loader
migration = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = migration
spec.loader.exec_module(migration)


class Core1FourthCurrentMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = ROOT
        foundation = migration.load_foundation(root / "knowledge/d1-d11-foundation.json")
        cls.my, cls.upper, cls.bridge = migration.build_three_pass_maps(
            foundation,
            root / "crates/sens/src/domain_surface_registry_generated.rs",
            root / "crates/sens/src/semantic_registry_generated.rs",
            root / "crates/sens/src/semantic_registry.rs",
            root / "crates/sens/src/eval/necessary_forms_generated.rs",
        )
        cls.keyboard = migration.build_text7(
            foundation, root / "knowledge/d7-keyboard-v2-ratified.json"
        )

    def resolver(self):
        return migration.Resolver(self.my, self.upper)

    def test_ukrainian_source_is_not_sid8_dump(self):
        readable = SOURCE.read_text(encoding="utf-8")
        self.assertTrue(readable.startswith("(перше (решта"), readable)
        for name in ("перше", "решта", "сполучити", "як-є"):
            self.assertIn(name, readable)
        self.assertNotIn("00000101", readable)
        self.assertNotIn("C1-FOURTH", readable)
        # Чинний четвертий елемент компонується з D5/D3, не із SID8.
        self.assertIn("(визначити ядро1-четвертий-елемент",
                      (ROOT / "lib/core1.lisp").read_text(encoding="utf-8"))
        self.assertIn("(третє (решта передане-значення))",
                      (ROOT / "lib/core1.lisp").read_text(encoding="utf-8"))
        self.assertEqual(self.bridge, {})

    def test_real_ukr_projection_exact_words_and_historical_physical(self):
        resolver = self.resolver()
        projection = migration.migrate_file(
            SOURCE.read_text(encoding="utf-8"), resolver, self.keyboard,
            codec="t5m", source_surface="укр",
        )
        self.assertEqual(projection, EXPECTED_WORDS)
        self.assertEqual(resolver.counts["passthrough-head"], 0)
        self.assertGreater(resolver.counts["pass2-my-lisp"], 0)
        self.assertEqual(VIEW.read_text(encoding="ascii"), EXPECTED_WORDS)
        self.assertEqual(PHYSICAL.read_bytes(), EXPECTED_BYTES)
        # Старий фізичний T5 лише для порівняння: це НЕ сучасний T5M admission.
        self.assertEqual(migration.decode_bytes(EXPECTED_BYTES), EXPECTED_WORDS.split())
        self.assertEqual(migration.encode_projection(EXPECTED_WORDS), EXPECTED_BYTES)

    def test_current_t5m_dry_run_without_python_minted_sens(self):
        with tempfile.TemporaryDirectory() as tmp:
            output, report = Path(tmp) / "physical", Path(tmp) / "receipt.json"
            run = subprocess.run(
                [sys.executable, str(SCRIPT), str(SOURCE), "--out", str(output),
                 "--report", str(report), "--dry-run", "--codec", "t5m",
                 "--source-surface", "укр"],
                cwd=ROOT, text=True, capture_output=True, timeout=45,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["files_would_write"], 1, data)
            self.assertEqual(data["summary"]["files_blocked"], 0, data)
            self.assertEqual(data["summary"]["files_written"], 0, data)
            self.assertFalse(output.exists())
            self.assertIs(data["files"][0]["semantic_admitted"], False)

    def test_historical_w8_is_not_modern_callable_d8(self):
        with self.assertRaisesRegex(migration.MigrationError, "ambiguous eight-bit"):
            migration.migrate_file(
                "(00000101 (як-є ()))", self.resolver(), self.keyboard,
                codec="t5m", source_surface="укр",
            )

    def test_corrupt_old_transport_fails_closed(self):
        for damaged in (EXPECTED_BYTES + b"\\xf2", bytes([243])):
            with self.subTest(damaged=damaged.hex()):
                with self.assertRaises(migration.SensT5Error):
                    migration.decode_bytes(damaged)


if __name__ == "__main__":
    unittest.main()
