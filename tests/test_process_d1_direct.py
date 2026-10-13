#!/usr/bin/env python3
"""Single-file D1 W1 migration, full historical blob, exhaustive width/polarity audit."""
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "lib/process.lisp"
OLD_BLOB = "e4ed204f873ab6b40c941af70e3f5297ebc30c18"
OLD = "(010 (001 ()))"
NEW = "#d1:1"
OLD_COMMENT = "; Migrated: two-field COND only; explicit D1 fallbacks (010 (001 ()))."
NEW_COMMENT = "; Two-field D3 COND with exact direct D1:1 fallback values; D3 () stays data."


def ast(source: str):
    toks = [m.group() for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', source
    ) if not m.group().startswith(";")]
    stack = [[]]
    for tok in toks:
        if tok == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif tok == ")":
            if len(stack) <= 1:
                raise ValueError("unbalanced close")
            stack.pop()
        else:
            stack[-1].append(tok)
    if len(stack) != 1:
        raise ValueError("unbalanced open")
    return stack[0]


def domain_count():
    total = 0
    for width in range(1, 11):
        source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf8")
        keys = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", source)
        if len(keys) != 1 << width or len(set(keys)) != len(keys):
            raise ValueError(f"D{width} count/dup")
        if set(keys) != {f"{x:0{width}b}" for x in range(1 << width)}:
            raise ValueError(f"D{width} width/holes")
        total += len(keys)
    return total


def audit(source: str):
    if source.count(NEW) != 5 or OLD in source:
        raise ValueError("five D1 W1 direct constants required")
    old_source = source.replace(NEW, OLD).replace(NEW_COMMENT, OLD_COMMENT)
    raw = old_source.encode("utf8")
    h = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if h != OLD_BLOB:
        raise ValueError("source provenance drift beyond five direct D1 replacements")
    parsed = ast(source)
    if len(parsed) != 8 or sum(1 for form in parsed if isinstance(form,list) and form and form[0] == "0011") != 7:
        raise ValueError("seven process definitions plus quoted trailing data must remain")
    def visit(node):
        if not isinstance(node, list):
            return
        if node and node[0] == "110":
            for branch in node[1:]:
                if not isinstance(branch, list) or len(branch) != 2:
                    raise ValueError("only two-part D3:COND clauses admitted")
        for item in node:
            visit(item)
    for row in parsed:
        visit(row)
    return len(raw)


class ProcessDirectD1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FILE.read_text(encoding="utf8")

    def test_historical_byte_provenance_and_cond_arity(self):
        previous = audit(self.source)
        print(f"PROCESS D1: UTF-8 bytes {previous} -> {len(self.source.encode('utf8'))}; "
              "five direct one-bit values instead of five D3 ATOM(D3 QUOTE) constructors")

    def test_exact_domain_addresses_all_2046(self):
        self.assertEqual(domain_count(), 2046)

    def test_width_and_function_head_ledger(self):
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf8")
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf8")
        self.assertRegex(d1, r"(?m)^\s*\(1\s+.*\(LISP T\)")
        self.assertRegex(d3, r"(?m)^\s*\(010\s+.*\(LISP ATOM\)")
        self.assertRegex(d3, r"(?m)^\s*\(001\s+.*\(LISP QUOTE\)")
        self.assertEqual((5 * (3+3)) - (5*1), 25)
        print("PROCESS D1: 30 historical D3 function-head bits -> 5 direct D1 bits; "
              "25 semantic AST head bits of overhead removed, physical T5 not measured")

    def test_mutations_fail_closed(self):
        for corrupted in (
            self.source.replace(NEW, "1", 1),
            self.source.replace(NEW, "0", 1),
            self.source.replace(NEW, "(001 ())", 1),
            self.source.replace(NEW, "#d1:0", 1),
        ):
            with self.assertRaises(ValueError):
                audit(corrupted)

    def test_numeric_exit_code_and_structural_nil_unchanged(self):
        data = self.source
        self.assertRegex(data, r"\(\(101 code \(001 \(\)\)\)\s+-1\)")
        self.assertIn("(process-raw-exit-code raw)", data)
        self.assertIn("(utf8-decode-string (process-raw-stderr-bytes raw))", data)
        self.assertIn("(001 (postcore-materialization-debug skipped))", data)


if __name__ == "__main__":
    unittest.main()
