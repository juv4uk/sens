"""Українські виклики D9/D10 у трьох активних бібліотеках; жодних SID8-семантик."""
from __future__ import annotations
from collections import Counter
import importlib.util
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS)) if str(SCRIPTS) not in sys.path else None
from domain_tables import read_domain_table
SPEC = importlib.util.spec_from_file_location("ukr_callsite_scan_for_batch", SCRIPTS / "check_ukr_callsite_migration.py")
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)

# Випадки закріплюють вихідний en-голів, exact domain/біти і мінімум викликів;
# українське ім'я завжди читаємо з чинної таблиці, не дублюємо реєстр.
EXPECTED = {
    "lib/translation.lisp": {
        "knowledge-clause-valid?": ("D10", "0010000000", 1),
        "knowledge-clauses-valid?": ("D10", "0010001000", 1),
        "knowledge-goal-valid?": ("D10", "0010010101", 1),
        "knowledge-proper-list?": ("D10", "0010001110", 4),
        "make-translation-review": ("D9", "000011010", 16),
        "translation-admittable?": ("D9", "000110111", 1),
        "translation-alternatives-valid?": ("D10", "0010101100", 2),
        "translation-ambiguity-valid?": ("D10", "0010011110", 1),
        "translation-batch-valid?": ("D10", "0010100111", 1),
        "translation-candidate-payload-valid?": ("D10", "0010100101", 2),
        "translation-envelope-valid?": ("D10", "0010011101", 2),
        "translation-evidence-entry": ("D9", "000000011", 1),
        "translation-evidence-next": ("D9", "000001110", 1),
        "translation-evidence-worthy?": ("D9", "000111011", 1),
        "translation-kind": ("D9", "000101100", 5),
        "translation-kind-valid?": ("D10", "0010111000", 1),
        "translation-payload": ("D9", "000101110", 8),
        "translation-review": ("D9", "000101000", 1),
        "translation-review-advice-decision": ("D10", "0010101001", 2),
        "translation-review-candidate": ("D10", "0010111010", 1),
        "translation-review-code": ("D9", "000100011", 1),
        "translation-review-proposal": ("D9", "000100101", 2),
        "translation-review-status": ("D9", "000111100", 4),
        "translation-review-status-valid?": ("D10", "0010111110", 1),
        "translation-review-valid?": ("D10", "0010100011", 2),
        "translation-source": ("D9", "000010100", 1),
        "translation-status": ("D9", "000000101", 5),
        "translation-status-valid?": ("D10", "0010110000", 1),
    },
    "lib/result-status.lisp": {
        "result-not-head?": ("D10", "0010001100", 2),
        "result-proper-list?": ("D10", "0010010110", 2),
    },
    "lib/bridge/prolog-to-datalog.lisp": {
        "prolog-values-to-datalog-facts": ("D10", "0010011100", 2),
    },
}

# Ідентичності двох D10 рішень перевіряємо за визначеннями та таблицею.
# Дійсні call-site перевіряються окремо; виконання — у SENS runtime.
RATIFIED_D10_DEFINITIONS = {
    "advice-all-decision": ("D10", "0001111010"),
    "advice-decision": ("D10", "0001111101"),
}

class UkrainianCorpusProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.by_en = {}
        for domain in (9, 10):
            for row in read_domain_table(ROOT / "lib" / "domains" / f"d{domain}.lisp"):
                if row.en:
                    cls.by_en.setdefault(row.en, []).append(row)

    def test_only_current_unique_domain_peers_are_called(self):
        for path, names in EXPECTED.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                calls = Counter(t.text for t in audit.candidate_heads(audit.parse(source)))
                for name, (domain, bits, minimum) in names.items():
                    with self.subTest(path=path, old_name=name):
                        rows = self.by_en.get(name, [])
                        self.assertEqual(len(rows), 1, f'ambiguous current peer: {name}')
                        row = rows[0]
                        self.assertEqual((row.domain, row.bits), (domain, bits))
                        self.assertTrue(row.ukr)
                        self.assertIsNone(re.search(r"[A-Za-z]", row.ukr))
                        self.assertEqual(calls[name], 0, f'old Latin executable head remains: {name}')
                        self.assertGreaterEqual(calls[row.ukr], minimum)

    def test_advice_is_decided_by_current_world_mechanism(self):
        # D10-координати залишаються ратифікованими даними, але самі
        # не доводять викличність. Справжній SENS-свідок — translation_boundary.rs.
        translation = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        calls = Counter(t.text for t in audit.candidate_heads(audit.parse(translation)))
        for name in ("порада-рішення-у-світ", "порада-всі-рішення-у-світ"):
            self.assertGreaterEqual(calls[name], 1, name)
        # Поточний журнал — жива Lisp-функція без кешованого знімка.
        # Перевірка поверхні не заміняє runtime-свідок SENS.
        knowledge = (ROOT / "lib/knowledge.lisp").read_text(encoding="utf-8")
        self.assertIn("(визначити поточний-журнал-знань", knowledge)
        self.assertIn("(функція () журнал-знань)", knowledge)
        self.assertEqual(translation.count(
            "(створити-світ (як-є ()) (поточний-журнал-знань) (як-є ()))"
        ), 2)
        self.assertNotIn(
            "(створити-світ (як-є ()) журнал-знань (як-є ()))",
            translation,
        )
        for old_en in ("advice-decision", "advice-all-decision"):
            self.assertEqual(calls[old_en], 0)
            rows = self.by_en.get(old_en, [])
            self.assertEqual(len(rows), 1)
            self.assertGreaterEqual(calls[rows[0].ukr], 1,
                                    "український D10 виклик у програмі має зберігатися; runtime перевіряє SENS")

    def test_d10_advice_ukrainian_definitions_preserve_exact_identity(self):
        source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        definitions = re.findall(r"(?m)^\s*\(визначити\s+([^\s()]+)", source)
        self.assertEqual(len(definitions), len(set(definitions)), "повторне визначення D10")
        for old_name, (domain, bits) in RATIFIED_D10_DEFINITIONS.items():
            with self.subTest(name=old_name):
                rows = self.by_en.get(old_name, [])
                self.assertEqual(len(rows), 1, "ратифіковане D10 ім'я має бути однозначним")
                row = rows[0]
                self.assertEqual((row.domain, row.bits), (domain, bits))
                self.assertIn(row.ukr, definitions, "відсутнє чинне українське DEFINE D10")
                self.assertNotIn(old_name, definitions, "не повертати англомовне DEFINE")

    def test_quoted_data_and_definition_names_remain_distinct(self):
        translation = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        bridge = (ROOT / "lib/bridge/prolog-to-datalog.lisp").read_text(encoding="utf-8")
        self.assertIn("(як-є candidate)", translation)
        self.assertIn("(як-є projection-result)", bridge)
        self.assertNotIn("(визначити translation-status переклад-стан)", translation)
        self.assertIn("(визначити переклад-стан", translation)
        self.assertIn("(як-є prolog-substitutions-to-datalog-facts)", bridge)
        sample = '(як-є (translation-status дані)) (як-є (translation-payload дані))'
        heads = [t.text for t in audit.candidate_heads(audit.parse(sample))]
        self.assertNotIn("translation-status", heads)
        self.assertNotIn("translation-payload", heads)

    def test_exact_identity_is_not_a_callability_or_carrier_proof(self):
        row = self.by_en["prolog-values-to-datalog-facts"][0]
        self.assertEqual((row.domain, row.width, row.bits), ("D10", 10, "0010011100"))
        # Це контроль identity; виконуваність/перенесення T5M ним не встановлюється.

if __name__ == "__main__":
    unittest.main()
