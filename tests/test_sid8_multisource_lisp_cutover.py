"""Fail-closed source-level regression for the 32-file 2026-10-11 SID8 cutover.

This checks Lisp *heads* only; quoted data and 8-bit values are not blindly
rewritten. Runtime equivalence remains a separate oracle obligation.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "benchmarks/arithmetic.lisp",
    "benchmarks/closures.lisp",
    "benchmarks/lists.lisp",
    "benchmarks/parser.lisp",
    "benchmarks/recursion.lisp",
    "experiments/core4-logic15-algebra.lisp",
    "experiments/core4-predicate-answer-carrier-matrix.lisp",
    "experiments/function-genealogy.lisp",
    "lib/bridge/prolog-to-datalog.lisp",
    "scripts/build-constitution.lisp",
    "scripts/build-inventory.lisp",
    "scripts/check-core1-compiler-sid-resolver.lisp",
    "scripts/check-core3-profile-contract.lisp",
    "scripts/check-domain-table-readable.lisp",
    "scripts/check-function-table-mechanisms.lisp",
    "scripts/check-island-math-evidence.lisp",
    "scripts/check-kernel-abi-transport-boundary.lisp",
    "scripts/check-repo-tooling-inventory.lisp",
    "scripts/fixtures-for-tier.lisp",
    "scripts/gen-functions.lisp",
    "scripts/generate-meta-semantic-registry.lisp",
    "scripts/generate-rust-evaluator-dispatch.lisp",
    "scripts/generate-rust-function-signatures.lisp",
    "scripts/generate-rust-profile-mechanism-routes.lisp",
    "scripts/generate-rust-semantic-registry.lisp",
    "scripts/machine-authority-guard.lisp",
    "scripts/oracle-batch.lisp",
    "scripts/program-symbol-table.lisp",
    "scripts/release.lisp",
    "scripts/semantic-authority-guard.lisp",
    "scripts/symbol-table.lisp",
    "scripts/перевірити-український-профіль.lisp",
)

def executable_heads(source):
    stack = []
    quoted_next = False
    i = 0
    while i < len(source):
        c = source[i]
        if source.startswith("#|", i):
            nesting = 1
            i += 2
            while nesting and i < len(source):
                if source.startswith("#|", i):
                    nesting += 1
                    i += 2
                elif source.startswith("|#", i):
                    nesting -= 1
                    i += 2
                else:
                    i += 1
            if nesting:
                raise AssertionError("unclosed block comment")
            continue
        if c == ";":
            while i < len(source) and source[i] != "\n":
                i += 1
            continue
        if c == '"':
            i += 1
            ended = False
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    ended = True
                    break
                else:
                    i += 1
            if not ended:
                raise AssertionError("unclosed string")
            continue
        if c in ("'", "`") or source.startswith("#'", i):
            quoted_next = True
            i += 2 if source.startswith("#'", i) else 1
            continue
        if c == "(":
            parent = stack[-1] if stack else None
            if parent and parent["first"]:
                parent["first"] = False
            quoted = quoted_next or bool(parent and (parent["quoted"] or parent["quote_children"]))
            stack.append({"first": True, "quoted": quoted, "quote_children": False})
            quoted_next = False
            i += 1
            continue
        if c == ")":
            if not stack:
                raise AssertionError("unexpected close")
            stack.pop()
            quoted_next = False
            i += 1
            continue
        if c.isspace():
            i += 1
            continue
        if c == ",":
            quoted_next = True
            i += 2 if source.startswith(",@", i) else 1
            continue
        start = i
        while (i < len(source) and not source[i].isspace()
               and source[i] not in "()'`\",;"
               and not source.startswith("#|", i)):
            i += 1
        if i == start:
            i += 1
            continue
        word = source[start:i]
        frame = stack[-1] if stack else None
        if frame and frame["first"]:
            frame["first"] = False
            if not frame["quoted"]:
                yield word
            if word in {"00000001", "001", "QUOTE", "quote", "як-є"}:
                frame["quote_children"] = True
        quoted_next = False
    if stack:
        raise AssertionError("unclosed list")

class MultisourceDomainCutover(unittest.TestCase):
    def test_no_legacy_eight_bit_callable_heads(self):
        self.assertEqual(len(FILES), 32)
        for rel in FILES:
            with self.subTest(path=rel):
                source = (ROOT / rel).read_text(encoding="utf-8")
                heads = list(executable_heads(source))
                self.assertGreater(len(heads), 0)
                self.assertFalse(
                    [h for h in heads if re.fullmatch(r"[01]{8}", h)],
                    f"{rel} contains unconverted or ambiguous 8-bit callable heads",
                )
                # D4:0011 та його ратифікована повна укр-назва є
                # рівноправними spelling одного виклику. Восьмибітні
                # історичні сід8-голови і далі заборонені.
                define_heads = {"0011", "визначити"}
                self.assertTrue(
                    define_heads.intersection(heads),
                    f"{rel} missing exact D4 DEFINE head",
                )
                if rel in {
                    "scripts/check-domain-table-readable.lisp",
                    "scripts/fixtures-for-tier.lisp",
                }:
                    self.assertIn("визначити", heads, f"{rel} not on full укр")
                    self.assertNotIn("0011", heads, f"{rel} stale D4 encoded call")

    def test_all_active_ukr_lisp_libraries_have_no_legacy_w8_heads(self):
        # Жоден новий живий .lisp з повною викличною поверхнею «укр»
        # не може нишком повернути плоскі SID8 / Sens8 call-heads.
        # Це лише перевірка source; виконання здійснює сам SENS.
        scanned = 0
        for path in sorted((ROOT / "lib").rglob("*.lisp")):
            rel = path.relative_to(ROOT)
            if {"domains", "generated", "staged-out"} & set(rel.parts):
                continue  # Таблиці й архіви — дані, а не виконавчі голови.
            source = path.read_text(encoding="utf-8")
            if not re.search(r"(?m)^\\s*\\(визначити\\s+", source):
                continue  # Декларативна таблиця, без виконуваних DEFINE.
            scanned += 1
            with self.subTest(path=str(rel)):
                heads = list(executable_heads(source))
                old = [head for head in heads if re.fullmatch(r"[01]{8}", head)]
                self.assertFalse(old, f"{rel} has historical W8 heads: {old[:8]}")
        self.assertGreaterEqual(scanned, 40, "Active Ukrainian Lisp inventory unexpectedly shrank")

    def test_domain_authority_is_unchanged(self):
        import json
        foundation = json.loads((ROOT / "knowledge/d1-d9-foundation.json").read_text())
        self.assertEqual(foundation["domains"]["D4"]["residents"]["0011"], "DEFINE")
        self.assertEqual(foundation["domains"]["D4"]["residents"]["0010"], "LAMBDA")
        self.assertEqual(foundation["domains"]["D3"]["residents"]["001"], "QUOTE")
        live_d4 = (ROOT / "lib/domains/d4.lisp").read_text(encoding="utf-8")
        self.assertIn("(0011 (ук визначити) (укр визначити)", live_d4)


if __name__ == "__main__":
    unittest.main()
