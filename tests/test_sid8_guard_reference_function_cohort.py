"""Syntactic, immutable-old-blob witness for six Guard Lisp function cutovers.

Only the admitted six definitions are allowed to differ; no claims about
the remaining historical Guard catalogue or total runtime parity.
"""
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "knowledge/guard-reference.lisp"
OLD_SHA = "ca32234690b8d5062a81fc90c8eb11333c8901a8"
NAMES = (
    "guard-script-find",
    "guard-scripts",
    "guard-evidence-status-strength",
    "guard-reference-all",
    "guard-reference-find-strongest",
    "guard-reference-find",
)
COUNTS = (11, 10, 10, 13, 10, 2)
SPEC = importlib.util.spec_from_file_location(
    "d3_guard_cutover_scanner", ROOT / "scripts/check_d3_legacy_logic.py"
)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)


def body(src, name):
    pattern = r"\((?:00001011|0011)\s+" + re.escape(name) + r"(?=\s)"
    found = list(re.finditer(pattern, src))
    if len(found) != 1:
        raise AssertionError(f"{name}: expected one real definition, got {len(found)}")
    begin = found[0].start()
    depth, quoted, escaped, comment = 0, False, False, False
    for pos in range(begin, len(src)):
        c = src[pos]
        if comment:
            if c == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c == ";":
            comment = True
        elif c == '"':
            quoted = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return begin, pos + 1, src[begin:pos + 1]
    raise AssertionError(f"{name}: incomplete source")


class GuardD3Cutover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = subprocess.run(
            ["git", "cat-file", "blob", OLD_SHA], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout
        cls.new = FILE.read_text(encoding="utf-8")

    def test_only_six_executable_definitions_changed(self):
        old, new = self.old, self.new
        for name, count in zip(NAMES, COUNTS):
            oldstart, oldend, oldbody = body(old, name)
            newstart, newend, newbody = body(new, name)
            self.assertTrue(oldbody.startswith("(00001011 " + name))
            self.assertTrue(newbody.startswith("(0011 " + name))
            self.assertEqual(len(re.findall(r"\(\s*[01]{8}(?=\s|\))", oldbody)), count)
            self.assertNotRegex(newbody, r"\(\s*[01]{8}(?=\s|\))")
            # Internal two-field D3 clause semantics, not textual equivalence.
            self.assertEqual(GUARD.scan_lisp(newbody, "guard/" + name), [])
            old = old[:oldstart] + "__GUARD_" + name + "__" + old[oldend:]
            new = new[:newstart] + "__GUARD_" + name + "__" + new[newend:]
        self.assertEqual(old, new, "Historical catalogue or held functions were touched")

    def test_four_identical_atom_polarities_are_folded(self):
        for name in ("guard-script-find", "guard-scripts",
                     "guard-reference-all", "guard-reference-find-strongest"):
            src = body(self.new, name)[2]
            self.assertNotIn("((010 tools) ()", src)
            self.assertNotIn("((010 references) ()", src)
            self.assertIn("(010 (001 ()))", src)
        strength = body(self.new, "guard-evidence-status-strength")[2]
        self.assertIn("((101 status (001 confirmed)) 4)", strength)
        self.assertIn("((010 (001 ())) 0)", strength)

    def test_malformed_cond_negative_controls_are_rejected(self):
        value = body(self.new, "guard-script-find")[2]
        changed = value.replace("((010 tools) (001 ()))",
                                "((010 tools) () (001 ()))", 1)
        self.assertNotEqual(changed, value)
        self.assertIn("COND_NOT_TWO_FIELDS",
                      {r.rule for r in GUARD.scan_lisp(changed, "negative")})
        changed = value.replace("((010 (001 ()))", "(t", 1)
        self.assertIn("COND_HOST_TRUTH",
                      {r.rule for r in GUARD.scan_lisp(changed, "negative")})


if __name__ == "__main__":
    unittest.main()
