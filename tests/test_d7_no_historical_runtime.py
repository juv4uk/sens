"""Regression gate: no retired D7 v1 text/phonetic mapping in active runtime."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "knowledge/d7-keyboard-v2-ratified.json"


class NoHistoricD7InExecutablePaths(unittest.TestCase):
    def test_owner_has_exact_128_w7_data_words_not_phonetic_v1(self):
        doc = json.loads(CURRENT.read_text(encoding="utf-8"))
        self.assertEqual(
            (doc["schema"], doc["status"], doc["width"],
             doc["capacity"], doc["occupancy"]),
            ("sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128),
        )
        self.assertEqual([item["bits"] for item in doc["table"]],
                         [format(n, "07b") for n in range(128)])
        for field in ("ascii", "uk", "san"):
            self.assertEqual(len({item[field] for item in doc["table"]}), 128)
        self.assertEqual(doc["table"][33]["uk"], "!")
        self.assertEqual(doc["table"][42]["uk"], "*")

    def test_no_runtime_or_migration_code_imports_obsolete_d7_authority(self):
        active = (
            "scripts/d7_symbol_codec.py",
            "scripts/d7_source_projection.py",
            "scripts/check-d7-runtime-projection.py",
            "scripts/migrate-three-pass.py",
            "scripts/migrate-to-sens-codes.py",
            "scripts/migrate-selected-lisp.py",
            "scripts/admit-t5-migration.py",
            "scripts/migration-readiness-census.py",
            "scripts/report_machine_block_quote_data_frontier.py",
            "crates/sens/src/d7_keyboard.rs",
            "crates/sens/src/text7_projection.rs",
            "crates/sens/src/ternary_transport.rs",
            "crates/sens/src/domain_identity.rs",
            "crates/sens/src/domain_words.rs",
            "crates/sens/src/source_words.rs",
        )
        for name in active:
            with self.subTest(path=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                self.assertNotIn("knowledge/d7-ratified.json", source)
                self.assertNotIn("SoundD7", source)
                self.assertNotIn("text7_projection_generated.rs", source)

    def test_historical_projection_cannot_enter_active_rust_or_migrators(self):
        root = (ROOT / "crates/sens/src/lib.rs").read_text(encoding="utf-8")
        self.assertIn("pub mod d7_keyboard;", root)
        self.assertNotIn("mod text7_projection_generated;", root)
        for name in ("scripts/migrate-three-pass.py", "scripts/migrate-to-sens-codes.py"):
            code = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("HISTORICAL_D7_DISABLED", code)

    def test_current_foundation_delegates_to_128_cell_keyboard(self):
        foundation = json.loads(
            (ROOT / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
        )
        d7 = foundation["domains"]["D7"]
        self.assertEqual((d7["width"], d7["capacity"], d7["occupancy"]), (7, 128, 128))
        self.assertEqual(d7["normative_map"], "knowledge/d7-keyboard-v2-ratified.json")
        self.assertEqual(set(d7["residents"].values()), {"text-data"})
        self.assertEqual(len(d7["residents"]), 128)


if __name__ == "__main__":
    unittest.main()
