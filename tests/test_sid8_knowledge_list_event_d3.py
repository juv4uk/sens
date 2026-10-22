"""Статична перевірка міграції подій знань до чинних українських D3 форм.

Семантику, порядок, кратність і порожній список доводить виключно
нативний SENS: crates/sens/tests/knowledge_exact_macro_migration.rs.
Жодної реконструкції Lisp-виконання у Python.
"""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/knowledge.lisp"


class KnowledgeCurrentD3Source(unittest.TestCase):
    def test_live_event_builder_has_ukrainian_law_and_no_old_map_head(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("(визначити перетворити-клаузи-на-події-повідомлення", source)
        self.assertIn("(список (як-є tell)", source)
        self.assertIn("(сполучити", source)
        self.assertIn("(решта клаузи)", source)
        self.assertNotIn("(визначити clauses->tell-events", source)
        self.assertNotIn("(101000", source)

    def test_no_old_binary_call_heads_are_resurrected(self):
        source = SOURCE.read_text(encoding="utf-8")
        # Це лише аудит джерельної проєкції, не SENS-оракул.
        self.assertIsNone(re.search(r"\(([01]{8})(?=\s|\))", source))
        self.assertIn("(визначити журнал-знань", source)
        self.assertNotIn("*knowledge-journal*", source)
        self.assertNotIn("*версія-пакета-знань*", source)


if __name__ == "__main__":
    unittest.main()
