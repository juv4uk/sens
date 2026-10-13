#!/usr/bin/env python3
"""SENS Guard: 8 дозволених статусів, 2 точні D1:NO, 2046 width-proof cells."""
from pathlib import Path
import hashlib
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "lib/guard.lisp"
PREVIOUS_BLOB = "b2a99bd7899b18a14ec877faad98cb4402b787c2"
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
    yes = ["010", ["001", []]]
    no = ["0100", yes]
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
    def test_historical_full_source_is_only_two_control_replacements(self):
        after = SRC.read_text(encoding="utf-8")
        self.assertEqual(after.count(NEW), 2)
        self.assertEqual(after.count(OLD), 1)  # A third NIL is data, not predicate.
        before = after.replace(NEW, OLD)
        data = before.encode("utf-8")
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        self.assertEqual(digest, PREVIOUS_BLOB)
        print(f"GUARD-D1: source bytes {len(data)} -> {len(after.encode('utf-8'))}; "
              "2 true D1:NO outcomes; +14 function-head identity bits total "
              "(2 × [D4:0100=4 + D3:010=3]); no physical .sens claimed")

    def test_both_guards_accept_exactly_eight_rationalized_statuses(self):
        self.assertEqual(sum(predicate_branches(SRC.read_text(encoding="utf-8")).values()), 8)

    def test_current_domain_capacity_and_exact_widths(self):
        self.assertEqual(audit_cells(), 2046)

    def test_negative_mutations_do_not_inherit_false_truthiness(self):
        src = SRC.read_text(encoding="utf-8")
        for candidate in (src.replace(NEW, OLD, 1),
                          src.replace(NEW, "((010 (001 ())) 0)", 1),
                          src.replace(NEW, "((010 (001 ())) (0100 (001 ())))", 1)):
            with self.assertRaises(ValueError):
                predicate_branches(candidate)

    def test_no_unqualified_zero_is_substituted_for_d1(self):
        self.assertNotIn("((010 (001 ())) 0)", SRC.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
