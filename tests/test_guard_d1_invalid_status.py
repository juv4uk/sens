#!/usr/bin/env python3
"""SENS Guard: 8 дозволених статусів, 2 точні D1:NO, 2046 width-proof cells."""
from pathlib import Path
import hashlib
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "lib/guard.lisp"
PREVIOUS_BLOB = "4447f58dc304d7c6dbcc69506a6b49986d90b7a8"
PREVIOUS_GENERATION = "b2a99bd7899b18a14ec877faad98cb4402b787c2"
YES_OLD = "(010 (001 ()))"
NO_OLD = "(0100 (010 (001 ())))"
YES = "#d1:1"
NO = "#d1:0"
PREVIOUS_COMMENT = "; Migrated: bare host truthiness t → exact D1:1 form (010 (001 ()))."
CURRENT_COMMENT = "; Predicate results now use direct typed D1 W1 projections #d1:1 / #d1:0."
OLD = "((010 (001 ())) (001 ())))"
NEW = "((010 (001 ())) (0100 (010 (001 ())))))"
EXPECTED = {
    "guard-decision?": ("allow", "warn", "reject", "unknown"),
    "guard-evidence-status?": ("confirmed", "partial", "unresolved", "broken"),
}


def tokens(source):
    scanner = r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+'
    return [m.group(0) for m in re.finditer(scanner, source)
            if not m.group(0).startswith(";")]


def parse(source):
    stack = [[]]
    for tok in tokens(source):
        if tok == "(":
            part = []
            stack[-1].append(part)
            stack.append(part)
        elif tok == ")":
            if len(stack) == 1:
                raise ValueError("unbalanced close")
            stack.pop()
        else:
            stack[-1].append(tok)
    if len(stack) != 1:
        raise ValueError("unbalanced source")
    return stack[0]


def predicate_branches(source):
    funcs = {row[1]: row for row in parse(source)
             if isinstance(row, list) and len(row) >= 3 and row[0] == "0011"}
    yes = YES
    no = NO
    results = {}
    for name, statuses in EXPECTED.items():
        root = funcs[name]
        clauses = root[2][2][1:]
        if len(clauses) != 5:
            raise ValueError(f"{name}: missing two-field COND branches")
        for n, status in enumerate(statuses):
            test, value = clauses[n]
            if test != ["101", "decision" if name == "guard-decision?" else "status", ["001", status]]:
                raise ValueError(f"{name}: D3 EQ branch {n} changed")
            if value != yes:
                raise ValueError(f"{name}: accepted branch is not strict D1:YES")
        fallback, value = clauses[4]
        if fallback != yes or value != no:
            raise ValueError(f"{name}: invalid status does not return strict D1:NO")
        results[name] = len(statuses)
    return results


def audit_cells():
    total = 0
    for width in range(1, 11):
        source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        keys = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", source)
        if len(keys) != (1 << width):
            raise ValueError(f"D{width}: incomplete table")
        if any(len(key) != width for key in keys):
            raise ValueError(f"D{width}: wrong-width resident")
        if len(set(keys)) != len(keys):
            raise ValueError(f"D{width}: duplicate")
        if set(keys) != {format(i, f"0{width}b") for i in range(1 << width)}:
            raise ValueError(f"D{width}: missing coordinate")
        total += len(keys)
    return total


class GuardInvalidStatus(unittest.TestCase):
    def test_historical_full_source_is_exactly_17_direct_d1_replacements(self):
        after = SRC.read_text(encoding="utf-8")
        self.assertEqual((after.count(YES), after.count(NO)), (15, 2))
        self.assertNotIn(YES_OLD, after)
        self.assertNotIn(NO_OLD, after)
        self.assertNotIn("((#d1:1) 0)", after)
        before = (after.replace(NO, NO_OLD).replace(YES, YES_OLD)
                  .replace(CURRENT_COMMENT, PREVIOUS_COMMENT))
        data = before.encode("utf-8")
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        self.assertEqual(digest, PREVIOUS_BLOB)
        # Check the prior migration, too: NIL must remain data, never D1 NO.
        before_two = before.replace(NEW, OLD)
        older = before_two.encode("utf-8")
        older_digest = hashlib.sha1(
            b"blob " + str(len(older)).encode() + b"\0" + older
        ).hexdigest()
        self.assertEqual(older_digest, PREVIOUS_GENERATION)
        head_bits = 15 * (3 + 3) + 2 * (4 + 3 + 3)
        self.assertEqual(head_bits, 110)
        self.assertEqual(head_bits - 17, 93)
        print(f"GUARD-D1: UTF8 bytes {len(data)} -> {len(after.encode('utf-8'))}; "
              "17 direct D1 bits replace 110 function-head bits; "
              "93 bits of AST call-head overhead removed, physical T5 NOT measured")

    def test_both_guards_accept_exactly_eight_rationalized_statuses(self):
        self.assertEqual(sum(predicate_branches(SRC.read_text(encoding="utf-8")).values()), 8)

    def test_current_domain_capacity_and_exact_widths(self):
        self.assertEqual(audit_cells(), 2046)

    def test_negative_mutations_do_not_inherit_false_truthiness(self):
        src = SRC.read_text(encoding="utf-8")
        for candidate in (src.replace("((#d1:1 #d1:0))", "((#d1:1 0))", 1),
                          src.replace(NO, "0", 1),
                          src.replace(NO, "(001 ())", 1),
                          src.replace(NO, YES, 1),
                          src.replace(YES, "(0100 (001 ()))", 1)):
            with self.assertRaises(ValueError):
                predicate_branches(candidate)

    def test_no_unqualified_zero_is_substituted_for_d1(self):
        src = SRC.read_text(encoding="utf-8")
        self.assertNotIn("((#d1:1) 0)", src)
        self.assertNotIn("((#d1:1) 1)", src)
        self.assertEqual(src.count(NO), 2)
        self.assertEqual(src.count(YES), 15)


if __name__ == "__main__":
    unittest.main()
