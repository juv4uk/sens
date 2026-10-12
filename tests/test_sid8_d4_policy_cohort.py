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
GUARD_ENFORCE = "scripts/semantic-authority-guard-enforce.lisp"

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


def _migrate_semantic_authority_guard(original):
    """Pinned-only D3 source law; never touches D9 reader or authorizes runtime."""
    old_car = "(00000101 verdicts)"
    old_tag = """(0011 verdict-tag
  (00000111
    ((00000010 verdict) (1) verdict)
    ((00000010 verdict) (0) (00000101 verdict))
    ((00000010 verdict) () (00000001 empty-verdict))))"""
    new_tag = """(0011 verdict-tag
  (110
    ((010 verdict)
     (110
       ((101 verdict (001 ())) (001 empty-verdict))
       ((010 (001 ())) verdict)))
    ((010 (001 ())) (100 verdict))))"""
    old_final = """(00000111
  ((00000011 verdict-tag (00000001 semantic-authority-ok))
   (1)
   (00000001 semantic-authority-ok))
  ((00000011 verdict-tag (00000001 semantic-authority-violation))
   (1)
   (00000101 ()))
  (t
   (00000101 ())))"""
    new_final = """(110
  ((101 verdict-tag (001 semantic-authority-ok))
   (001 semantic-authority-ok))
  ((101 verdict-tag (001 semantic-authority-violation))
   (100 (001 ())))
  ((010 (001 ()))
   (100 (001 ()))))"""
    for needle in (old_car, old_tag, old_final):
        if original.count(needle) != 1:
            raise AssertionError("unproved historical authority-guard delta " + repr(needle))
    return (original.replace(old_car, "(100 verdicts)")
            .replace(old_tag, new_tag).replace(old_final, new_final))


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

                if path == GUARD_ENFORCE:
                    expected = _migrate_semantic_authority_guard(d4_only)
                    expected = expected.replace(
                        "(01001011 (10100110 ", "(110101001 (110110111 ", 1
                    )
                    self.assertEqual(current, expected,
                                     "semantic guard has unproved source changes")
                    self.assertEqual(self.d3.scan_lisp(current, path), [],
                                     "D3 must be exactly two-field with D1 controls")
                    self.assertIn("(110101001 (110110111", current,
                                  "Ratified D9 reader must stay exact-width")
                    self.assertNotRegex(current, D3_LEGACY_COND)
                elif path == "knowledge/guard-reference.lisp":
                    # A separate, immutable-original witness now owns six D3
                    # conversions after this earlier D4-only staging phase.
                    # Both exact states remain checked, not just the latest.
                    pinned_d4 = subprocess.run(
                        ["git", "cat-file", "blob",
                         "ca32234690b8d5062a81fc90c8eb11333c8901a8"],
                        cwd=ROOT, capture_output=True, check=True,
                    ).stdout.decode("utf-8")
                    pinned_d3 = subprocess.run(
                        ["git", "cat-file", "blob",
                         "a5485f83a242343508fc8bed11c77befc49d2d96"],
                        cwd=ROOT, capture_output=True, check=True,
                    ).stdout.decode("utf-8")
                    self.assertEqual(d4_only, pinned_d4,
                                     "historical D4-only stage drifted")
                    self.assertEqual(current, pinned_d3,
                                     "six Guard D3 definitions diverged from exact proof")
                    self.assertRegex(current, D3_LEGACY_COND,
                                     "remaining legacy Guard forms must stay visible")
                elif path != GUARD_FACT:
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
                    # Each helper contained two ATOM branches returning the
                    # SAME quoted empty value; exact D1 ATOM merges them.
                    old_cond = re.compile(
                        r"\(110\s+\(\(010 pair\) \(\) \(001 \(\)\)\)"
                        r"\s+\(\(010 pair\) \(1\) \(001 \(\)\)\)"
                        r"\s+\(t \(1001 pair\)\)\)"
                    )
                    self.assertEqual(len(old_cond.findall(expected)), 2)
                    expected = old_cond.sub(
                        "(110 ((010 pair) (001 ()))\n"
                        "       ((010 (001 ())) (1001 pair)))", expected
                    )
                    self.assertEqual(current.count(fallback), 0)
                    self.assertEqual(current.count("((010 (001 ())) (guard-unknown"), 4)
                    self.assertEqual(current, expected,
                                     "зміна поза 110 heads, 4 YES, 6 LET та 2 ATOM cases")
                    self.assertEqual(self.d3.scan_lisp(current, path), [],
                                     "exact two-field D3 source must stay free of legacy clauses")
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


    def test_semantic_authority_guard_negative_d3_controls(self):
        path = GUARD_ENFORCE
        current = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(self.d3.scan_lisp(current, path), [])
        # Wrong domain must never be treated as a host-Lisp truth value.
        host_true = current.replace(
            "((010 (001 ()))\n   (100 (001 ())))",
            "(t\n   (100 (001 ())))", 1)
        self.assertNotEqual(host_true, current)
        self.assertIn("COND_HOST_TRUTH",
                      {f.rule for f in self.d3.scan_lisp(host_true, path)})
        # The former three-field expected-result selector is forbidden.
        three_fields = current.replace(
            "((101 verdict-tag (001 semantic-authority-ok))\n   (001 semantic-authority-ok))",
            "((101 verdict-tag (001 semantic-authority-ok))\n   (1)\n   (001 semantic-authority-ok))", 1)
        self.assertNotEqual(three_fields, current)
        self.assertIn("COND_NOT_TWO_FIELDS",
                      {f.rule for f in self.d3.scan_lisp(three_fields, path)})
        # Reject changes that would turn a guard failure into a successful NIL.
        self.assertEqual(current.count("(100 (001 ()))"), 2)

    def test_semantic_authority_guard_bounded_exact_d3_oracle(self):
        """Execute real migrated D3 AST on a separate strict bounded oracle.

        Verdict reader stays outside this test: READ-ALL/READ-FILE D9
        mechanisms must be proved separately before full admission.
        """
        path = GUARD_ENFORCE
        program = self.d3.parse((ROOT / path).read_text(encoding="utf-8"))
        self.assertEqual(len(program), 4)
        helper = program[2]
        self.assertEqual([x.atom for x in helper.children[:2]],
                         ["0011", "verdict-tag"])
        root = program[3]

        def quote(node):
            if node.atom is not None:
                return node.atom
            return tuple(quote(child) for child in node.children)

        def atom(value):
            # Structural () is an atom; nonempty pairs are not.
            return not (isinstance(value, tuple) and len(value) > 0)

        def evaluate(node, env):
            if node.atom is not None:
                if node.atom not in env:
                    raise ValueError("unbound source atom " + node.atom)
                return env[node.atom]
            if not node.children:
                return ()
            head, *args = node.children
            operator = head.atom
            if operator == "001":
                if len(args) != 1:
                    raise ValueError("bad quote arity")
                return quote(args[0])
            if operator == "010":
                if len(args) != 1:
                    raise ValueError("bad atom arity")
                return atom(evaluate(args[0], env))
            if operator == "101":
                if len(args) != 2:
                    raise ValueError("bad eq arity")
                lhs, rhs = (evaluate(arg, env) for arg in args)
                if not atom(lhs) or not atom(rhs):
                    raise ValueError("EQ requires two atoms")
                return lhs == rhs
            if operator == "100":
                if len(args) != 1:
                    raise ValueError("bad car arity")
                value = evaluate(args[0], env)
                if not isinstance(value, tuple) or not value:
                    raise ValueError("CAR of empty/non-pair: intentional rejection")
                return value[0]
            if operator == "110":
                for clause in args:
                    if clause.atom is not None or len(clause.children) != 2:
                        raise ValueError("old three-field COND")
                    predicate = evaluate(clause.children[0], env)
                    if type(predicate) is not bool:
                        raise TypeError("COND requires exact D1 PredicateBit")
                    if predicate:
                        return evaluate(clause.children[1], env)
                return ()
            raise ValueError("unadmitted operator: " + repr(operator))

        cases = [
            ((), "reject"),
            ("semantic-authority-ok", "semantic-authority-ok"),
            ("semantic-authority-violation", "reject"),
            ("other", "reject"),
            (("semantic-authority-ok",), "semantic-authority-ok"),
            (("semantic-authority-violation", "reason"), "reject"),
            (("other",), "reject"),
            ((("nested-tag",),), "reject"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                env = {"verdict": value}
                tag = evaluate(helper.children[2], env)
                env["verdict-tag"] = tag
                if expected == "reject":
                    with self.assertRaises(ValueError):
                        evaluate(root, env)
                else:
                    self.assertEqual(evaluate(root, env), expected)
        # The oracle must independently reject host truth and 3-field COND.
        with self.assertRaises(TypeError):
            evaluate(self.d3.parse("(110 (t (001 yes)))")[0], {"t": 1})
        with self.assertRaises(ValueError):
            evaluate(self.d3.parse("(110 ((010 (001 ())) (1) (001 yes)))")[0], {})


if __name__ == "__main__":
    unittest.main()
