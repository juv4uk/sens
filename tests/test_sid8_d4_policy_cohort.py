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


def _lower_parallel_let(source):
    """Six source-pinned W8 LET forms -> D4 LAMBDA applications.

    The existing S-expression parser provides exact source spans. Parallel
    arguments evaluate in the caller's lexical environment, as in LET;
    no D6:001000 execution claim is made. Never rewrite quoted data.
    """
    parser = _load("guard_fact_parallel_let_parser", "scripts/cond-modernize.py")
    roots = parser.parse(source)
    count = 0

    def emit(node):
        nonlocal count
        original = source[node.start:node.end]
        if node.opaque or not node.children:
            return original
        parts = node.children
        if parts[0].atom in ("001", "00000001", "QUOTE", "quote"):
            return original
        if parts[0].atom == "10011100":
            if len(parts) != 3 or not parts[1].children:
                raise AssertionError("unproved parallel LET structure")
            names, values = [], []
            for binding in parts[1].children:
                if len(binding.children) != 2 or binding.children[0].atom is None:
                    raise AssertionError("unproved parallel LET binding")
                names.append(binding.children[0].atom)
                values.append(emit(binding.children[1]))
            if len(set(names)) != len(names):
                raise AssertionError("duplicate LET variables")
            count += 1
            return (f"((0010 ({' '.join(names)}) {emit(parts[2])}) "
                    f"{' '.join(values)})")
        rendered = original
        for child in reversed(parts):
            converted = emit(child)
            if converted != source[child.start:child.end]:
                rendered = (rendered[:child.start - node.start]
                            + converted + rendered[child.end - node.start:])
        return rendered

    output = source
    for root in reversed(roots):
        converted = emit(root)
        if converted != source[root.start:root.end]:
            output = (output[:root.start] + converted + output[root.end:])
    return output, count


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
                    # Historical W8:10011100 LET overlaps current D8 CADDDAAR.
                    # D6 LET has no admitted runtime route, so express exactly
                    # the six pinned *parallel* bindings with D4 LAMBDA.
                    original_let_heads = expected.count("(10011100 ")
                    self.assertEqual(original_let_heads, 6)
                    expected, lowered = _lower_parallel_let(expected)
                    self.assertEqual(lowered, 6)
                    self.assertNotIn("(10011100 ", expected)
                    self.assertEqual(current.count(fallback), 0)
                    self.assertEqual(current.count("((010 (001 ())) (guard-unknown"), 4)
                    self.assertEqual(current, expected,
                                     "зміна поза 110 головами, 4 D1:YES та 6 parallel LET")
                    reasons = {x.rule for x in self.d3.scan_lisp(current, path)}
                    self.assertIn("COND_NOT_TWO_FIELDS", reasons)
                    self.assertIn("COND_HOST_TRUTH", reasons)
                    self.assertNotRegex(current, D3_LEGACY_COND)

                self.assertNotRegex(current, D4_HEAD)
        self.assertEqual(total_d4, 34)


    def test_parallel_let_lowering_keeps_quotes_and_refuses_duplicate_bindings(self):
        quoted = "(001 (10011100 ((a 1)) (100 a)))"
        text, count = _lower_parallel_let(quoted)
        self.assertEqual((text, count), (quoted, 0))
        bad = "(10011100 ((x 1) (x 2)) (111 x x))"
        with self.assertRaisesRegex(AssertionError, "duplicate LET variables"):
            _lower_parallel_let(bad)
        safe = "(10011100 ((x (100 source)) (y (011 source))) (111 x y))"
        text, count = _lower_parallel_let(safe)
        self.assertEqual(count, 1)
        self.assertEqual(
            text,
            "((0010 (x y) (111 x y)) (100 source) (011 source))",
        )


if __name__ == "__main__":
    unittest.main()
