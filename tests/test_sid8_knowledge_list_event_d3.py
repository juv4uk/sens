"""In-place Lisp-owned replacement of the uncallable D6 MAP at the knowledge boundary.

The old and new source Git blobs are compared exactly; semantic runtime parity
remains the separately required Rust content-store/world executable witness.
"""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "lib/knowledge.lisp"
OLD_SHA = "3517ea099d0217f2b82609bf16baa0dd6b7fdb63"
OLD = """(0011 clauses->tell-events
  (0010 (module-name clauses)
    (101000 (0010 (clause) (1110 (001 tell) module-name clause)) clauses)))"""
NEW = """(0011 clauses->tell-events
  (0010 (module-name clauses)
    (110
      ((010 clauses) (001 ()))
      ((010 (001 ()))
       (111
         (1110 (001 tell) module-name (100 clauses))
         (clauses->tell-events module-name (011 clauses)))))))"""
SPEC = importlib.util.spec_from_file_location(
    "knowledge_map_d3_checker", ROOT / "scripts/check_d3_legacy_logic.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class KnowledgeMapD3Cutover(unittest.TestCase):
    def test_original_source_changes_only_one_proven_function(self):
        before = subprocess.run(
            ["git", "cat-file", "blob", OLD_SHA], cwd=ROOT,
            capture_output=True, check=True, text=True
        ).stdout
        after = FILE.read_text(encoding="utf-8")
        self.assertEqual(before.count(OLD), 1)
        self.assertEqual(after, before.replace(OLD, NEW))
        self.assertNotIn("(101000", after)
        self.assertEqual(MODULE.scan_lisp(NEW, "clauses->tell-events"), [])

    def test_list_map_composition_preserves_order_and_multiplicity(self):
        # Independent small-list model of the recursive D3 law:
        # CONS(tell(head), recurse(tail)) == map(tell, clauses).
        for n in range(16):
            clauses = [("has-fur", str(i % 3)) for i in range(n)]
            mapped = [("tell", "zoo", x) for x in clauses]
            def derived(xs):
                return [] if not xs else [("tell", "zoo", xs[0])] + derived(xs[1:])
            self.assertEqual(derived(clauses), mapped)

    def test_host_truth_and_three_field_legacy_cond_rejected(self):
        invalid = NEW.replace("((010 clauses) (001 ()))",
                              "((010 clauses) () (001 ()))")
        findings = MODULE.scan_lisp(invalid, "negative")
        self.assertIn("COND_NOT_TWO_FIELDS", {f.rule for f in findings})
        invalid = NEW.replace("((010 (001 ()))", "(t")
        findings = MODULE.scan_lisp(invalid, "negative")
        self.assertIn("COND_HOST_TRUTH", {f.rule for f in findings})


if __name__ == "__main__":
    unittest.main()
