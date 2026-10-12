"""Two fail-closed policy scripts: old 3-field COND to current D1/D3."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
CASES={
 "scripts/enforce-function-table-mechanisms.lisp":("01417453ab32b3dda83459758661ffc3500501db","#d1"),
 "scripts/enforce-island-math-evidence.lisp":("a58072a4734e5d528ffeb422554381317fb6d779","1"),
}
spec=importlib.util.spec_from_file_location("d3_enforce_guard",ROOT/"scripts/check_d3_legacy_logic.py")
guard=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=guard
spec.loader.exec_module(guard)

def expected(original,scalar):
 substitutions=(
  ("(01001011 (10100110","(110101001 (110110111"),
  ("(00000101 verdicts)","(100 verdicts)"),
  ("(00000111\n","(110\n"),
  ("((00100010 verdict (00000001","((11110111 verdict (001"),
  ("\n   (00000001 ","\n   (001 "),
  ("\n   ("+scalar+")",""),
  ("\n  (t\n   (00000101 (00000001 ()))))","\n  ((010 (001 ()))\n   (100 (001 ()))))"),
 )
 for old,new in substitutions:
  if original.count(old)!=1:
   raise AssertionError("old source mismatch "+repr(old))
  original=original.replace(old,new)
 return original

class D3EnforcementCutover(unittest.TestCase):
 def test_pinned_original_only_two_field_predicate_proof(self):
  for path,(blob,scalar) in CASES.items():
   with self.subTest(path=path):
    original=subprocess.run(["git","cat-file","blob",blob],cwd=ROOT,check=True,capture_output=True).stdout.decode()
    after=(ROOT/path).read_text(encoding="utf-8")
    self.assertEqual(after,expected(original,scalar))
    self.assertEqual(guard.scan_lisp(after,path),[])
    self.assertIn("(110\n",after)
    self.assertIn("((010 (001 ()))\n   (100 (001 ())))",after)

 def test_negative_control_three_field_and_host_true(self):
  for path in CASES:
   source=(ROOT/path).read_text(encoding="utf-8")
   broken_three=source.replace("\n   (001 ","\n   (1)\n   (001 ",1)
   findings=guard.scan_lisp(broken_three,path)
   self.assertIn("COND_NOT_TWO_FIELDS",{f.rule for f in findings})
   broken_host=source.replace("((010 (001 ()))\n   (100 (001 ())))","(t\n   (100 (001 ())))",1)
   findings=guard.scan_lisp(broken_host,path)
   self.assertIn("COND_HOST_TRUTH",{f.rule for f in findings})

if __name__=="__main__":
 unittest.main()
