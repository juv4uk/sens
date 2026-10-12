"""Доказ точних замін голів виклику у трьох політиках.

Тільки лексична / доменна відповідність. Трипольовий D3 COND в
guard-fact-policy залишається BLOCKED до незалежного семантичного оракула.
"""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Незмінні Git blobs оригіналів — не довільні очікувані тексти тесту.
SOURCES = {
    "knowledge/guard-reference.lisp": ("f97371fd503075caec9344062847fb7c0e7642e7", 25),
    "knowledge/guard-fact-policy.lisp": ("d137f1b92a060980e0a2696300469ac0e9ec1b90", 6),
    "scripts/semantic-authority-guard-enforce.lisp": ("8e744541cb225f06f47a998204e7fc3d91f9082b", 3),
}

D4_HEAD = re.compile(r"\((\s*)(00001001|00001000)(?=[\s)])")
D3_LEGACY_COND = re.compile(r"\(\s*00000111(?=[\s)])")
CALL_HEAD = re.compile(r"\((\s*)([01]{8})(?=[\s)])")
GUARD_FACT = "knowledge/guard-fact-policy.lisp"

# Точно перевірена повна зміна поточного guard-fact-policy:
# 110 тільки як заміна коду, а НЕ свідчення двопольового COND.
GUARD_FACT_HEADS = {
    "00001001": "0011",   # DEFINE D4
    "00001000": "0010",   # LAMBDA D4
    "00101101": "11100",  # ASSOC D5
    "00000110": "011",    # CDR D3
    "00000111": "110",    # COND D3: ЗАБЛОКОВАНО семантично
    "00000010": "010",    # ATOM D3
    "00000001": "001",    # QUOTE D3
    "00101111": "1001",   # CADR D4
    "00000011": "101",    # EQ D3
    "00100111": "1110",   # LIST D4
}

# Обидва імпорти використовують чинні розбирачі репозиторію.
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PolicyD4PartialCutover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = _load("policy_d4_lexical_audit", "scripts/audit_lisp_migration_edits.py")
        cls.d3 = _load("policy_d4_d3_guard", "scripts/check_d3_legacy_logic.py")
        cls.coverage = {
            row["legacy_code"]: row
            for row in json.loads(
                (ROOT / "knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8")
            )["rows"]
        }

    def test_pinned_originals_change_only_reviewed_domain_call_heads(self):
        self.assertEqual(len(SOURCES), 3)
        total_d4 = 0
        for path, (blob, expected_d4) in SOURCES.items():
            with self.subTest(path=path):
                original = subprocess.run(
                    ["git", "cat-file", "blob", blob],
                    cwd=ROOT, capture_output=True, check=True,
                ).stdout.decode("utf-8")
                current = (ROOT / path).read_text(encoding="utf-8")
                count_d4 = 0
                def replace_d4(match):
                    nonlocal count_d4
                    count_d4 += 1
                    return "(" + match.group(1) + (
                        "0011" if match.group(2) == "00001001" else "0010"
                    )
                d4_only = D4_HEAD.sub(replace_d4, original)
                self.assertEqual(count_d4, expected_d4)
                total_d4 += count_d4

                if path != GUARD_FACT:
                    self.assertEqual(current, d4_only,
                                     "додаткові заміни поза доказом D4-only")
                    self.assertRegex(current, D3_LEGACY_COND)
                else:
                    self.assertEqual(
                        sum(1 for _ in CALL_HEAD.finditer(original)
                            if _.group(2) in GUARD_FACT_HEADS), 110
                    )
                    for old, new in GUARD_FACT_HEADS.items():
                        donor = self.coverage[old]
                        self.assertIn(
                            donor["classification"],
                            {"DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED"},
                        )
                        self.assertRegex(
                            donor["current_target"], rf"\bD[1-9]:{new}(?![01])\b"
                        )
                    expected = CALL_HEAD.sub(
                        lambda m: "(" + m.group(1) + GUARD_FACT_HEADS[m.group(2)]
                        if m.group(2) in GUARD_FACT_HEADS else m.group(0),
                        original,
                    )
                    # Existing lexical audit proves only call-head edits;
                    # the subsequent four fallback rewrites have a separate
                    # exact pinned-source equality witness below.
                    report = self.audit.audit_edit(original, expected)
                    self.assertEqual(report["status"], "LEXICAL_CONTEXT_ONLY")
                    self.assertEqual(report["semantic_parity"], "NOT_CHECKED")
                    # Four independent two-field COND fallbacks replace host
                    # T with the exact D1:YES witness ATOM(QUOTE EMPTY).
                    # This is not authority to rewrite obsolete 3-field COND.
                    fallback = "(t (guard-unknown"
                    self.assertEqual(expected.count(fallback), 4)
                    expected = expected.replace(
                        fallback, "((010 (001 ())) (guard-unknown"
                    )
                    self.assertEqual(current.count(fallback), 0)
                    self.assertEqual(current.count("((010 (001 ())) (guard-unknown"), 4)
                    self.assertEqual(current, expected,
                                     "зміна поза 110 головами та 4 D1:YES fallback")
                    reasons = {x.rule for x in self.d3.scan_lisp(current, path)}
                    self.assertIn("COND_NOT_TWO_FIELDS", reasons)
                    self.assertIn("COND_HOST_TRUTH", reasons)
                    self.assertNotRegex(current, D3_LEGACY_COND)

                self.assertNotRegex(current, D4_HEAD)
        self.assertEqual(total_d4, 34)


if __name__ == "__main__":
    unittest.main()
