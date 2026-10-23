"""Історичні Git blobs і чинні українські Lisp-сервісні програми.

Старі W8 вихідники зберігаються тільки як provenance. Ця перевірка
не оголошує повне семантичне чи фізичне T5M відтворення історії.
"""
import runpy
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = runpy.run_path(str(ROOT / "scripts/migrate-domain-ladder-source-batch.py"))
CASES = (
    ("scripts/generate-functions-md.lisp", "478f608a7d5a3032b8138dc995b744fbefb3ccf4"),
    ("scripts/benchmark-semantic-registry-read.lisp", "37e91a09af154a33b46b88aa1c24b0abecdb04ab"),
)


def old_blob(sha):
    return subprocess.run(
        ["git", "cat-file", "-p", sha],
        cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout


class HistoricalScriptSourceDelta(unittest.TestCase):
    def test_current_ukrainian_mapping_retains_unresolved_historical_cells(self):
        mapping, blocked = MIGRATION["authority"](ROOT)
        self.assertEqual((len(mapping), len(blocked)), (171, 85))
        self.assertEqual(mapping["00001001"], "визначити")
        self.assertEqual(mapping["00001000"], "функція")
        self.assertEqual(blocked["01011010"], "D10-RECOVERY-CANDIDATE")
        self.assertEqual(blocked["01000111"], "INTERNAL-NO-SEMANTIC-SLOT")

    def test_original_git_blobs_are_distinct_from_live_ukr_sources(self):
        guard = MIGRATION["guard_module"](ROOT)
        for path, historical_sha in CASES:
            with self.subTest(path=path):
                original = old_blob(historical_sha)
                current = (ROOT / path).read_text(encoding="utf-8")
                self.assertNotEqual(current, original)
                self.assertIn("(000010", original,
                              "історичний пін повинен вести на старий source")
                heads = MIGRATION["executable_call_heads"](current, guard)
                self.assertIn("визначити", heads)
                if path.endswith("generate-functions-md.lisp"):
                    self.assertIn("функція", heads)
                self.assertFalse(
                    any(MIGRATION["BITS"].fullmatch(head) for head in heads),
                    f"{path}: лишився сирий 8-бітний виклик",
                )
                self.assertEqual(guard.scan_lisp(current, path), [])
                row = MIGRATION["run"](ROOT, False, {path})["files"][0]
                self.assertEqual(row["status"], "unchanged", row)
                self.assertEqual(row["reasons"], [])


if __name__ == "__main__":
    unittest.main()
