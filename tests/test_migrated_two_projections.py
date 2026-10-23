"""Три проєкції чотирьох SENS-зразків: укр ↔ точні слова ↔ фізичний T5M."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_uk_t5_t5m_triplet import canonical_uk_from_words, project_current_uk
from sens_t5_t5m_codec import decode_t5m_bytes, encode_t5m_projection

NAMES = ("smoke-quote", "smoke-atom", "smoke-cond", "smoke-nested")


class ThreeProjectionMigrationTests(unittest.TestCase):
    def test_pinned_source_and_canonical_pairs(self):
        original = ROOT / "tests/fixtures/canonical-binary-smoke.bits"
        source_lines = original.read_text(encoding="ascii").splitlines()
        self.assertEqual(len(source_lines), 4)
        for name, source_line in zip(NAMES, source_lines):
            with self.subTest(name=name):
                root = ROOT / "examples/migrated"
                uk = (root / (name + ".lisp")).read_text(encoding="utf-8")
                view = (root / name).read_text(encoding="ascii")
                words = source_line.split()
                physical = (root / (name + ".sens")).read_bytes()
                self.assertEqual(physical, encode_t5m_projection(" ".join(words)))
                self.assertEqual(decode_t5m_bytes(physical), words)
                self.assertEqual(view, " ".join(words) + "\n")
                self.assertEqual(uk, canonical_uk_from_words(words))
                self.assertEqual(project_current_uk(uk), words)


if __name__ == "__main__":
    unittest.main()
