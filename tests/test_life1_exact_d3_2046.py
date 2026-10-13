"""Точний свідок основного LIFE-1: 6 міграцій і вся драбина D1–D10."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import CURRENT_HUMAN_TABLES, read_domain_table

LIFE = ROOT / "lib" / "life-1-scheduler.lisp"


class ExactLifeOneTests(unittest.TestCase):
    def test_six_historical_equal_calls_migrated(self):
        source = LIFE.read_text(encoding="utf-8")
        code = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
        self.assertIsNone(re.search(r"\\(11110111(?=[\\s()])", code))
        # Шість справжніх замінених call sites, рекурсія та визначення окремо.
        self.assertEqual(
            len(re.findall(r"\\(життя--рівні\\?(?=[\\s()])", code)), 8
        )
        self.assertIn("(0011 життя--рівні?", code)
        for head in ("010", "101", "100", "011", "110"):
            self.assertRegex(code, r"\\(" + head + r"(?=[\\s()])")
        self.assertIn("(semantic-id 00001100)", source)  # дані, не call

    def test_all_exact_domain_residents_are_distinct(self):
        identities = set()
        bits_total = 0
        directed_neighbors = 0
        for width, path in enumerate(CURRENT_HUMAN_TABLES, 1):
            rows = read_domain_table(path)
            words = {r.bits for r in rows}
            self.assertEqual(len(rows), 1 << width)
            self.assertEqual(len(words), 1 << width)
            self.assertEqual(words, {f"{n:0{width}b}" for n in range(1 << width)})
            for word in words:
                identity = (width, word)
                self.assertNotIn(identity, identities)
                identities.add(identity)
                bits_total += width
                for i in range(width):
                    neighbor = word[:i] + ("1" if word[i] == "0" else "0") + word[i+1:]
                    self.assertIn(neighbor, words)
                    directed_neighbors += 1
        self.assertEqual(len(identities), 2046)
        self.assertEqual(bits_total, 18434)
        self.assertEqual(directed_neighbors, 18434)
        self.assertNotEqual((3, "001"), (4, "0001"))
        # Кодові позиції ≠ автоматично викличні механізми.


if __name__ == "__main__":
    unittest.main()
