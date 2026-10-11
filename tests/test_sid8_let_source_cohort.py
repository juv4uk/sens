"""Fail-closed D6 LET admission blocker: keep runnable source stable.

Ratified identity != callable runtime mechanism. The earlier mechanically
rewritten D6 LET made the independent forward/knowledge oracle fail. Keep
historical LET heads unchanged until the domain call-head runtime is admitted.
"""
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE={
 "lib/forward.lisp":("f94d602b9b40668ec1f17e3b51956eaf72af74d2",19),
 "lib/knowledge.lisp":("4f314e54da95ef9af8f51cc6b87b8d665cc65a8a",25),
}
OLD=re.compile(r"\(10011100(?=[\s)])")
NEW=re.compile(r"\(001000(?=[\s)])")

class LetAdmissionBoundary(unittest.TestCase):
 def test_ratified_d6_let_is_not_d8_selector(self):
  x=json.loads((ROOT/"knowledge/d1-d9-foundation.json").read_text())["domains"]
  self.assertEqual(x["D6"]["residents"]["001000"],"LET")
  self.assertEqual(x["D8"]["residents"]["10011100"],"CADDDAAR")

 def test_old_let_is_kept_until_real_runtime_callability_exists(self):
  seen=0
  for path,(sha,n) in BASE.items():
   with self.subTest(path=path):
    original=subprocess.run(["git","cat-file","blob",sha],cwd=ROOT,capture_output=True,check=True).stdout.decode()
    current=(ROOT/path).read_text(encoding="utf-8")
    self.assertEqual(current,original)
    self.assertEqual(len(OLD.findall(current)),n)
    self.assertEqual(len(NEW.findall(current)),0)
    self.assertIn("(00001010",current)  # composite macro remains blocked
    seen+=n
  self.assertEqual(seen,44)

 def test_current_d8_mod_does_not_alias_historic_member(self):
  x=json.loads((ROOT/"knowledge/d1-d9-foundation.json").read_text())["domains"]
  self.assertEqual(x["D8"]["residents"]["00101100"],"MOD")
  for p,n in (("lib/time.lisp",3),("lib/core.lisp",2),("lib/core4.lisp",2)):
   with self.subTest(path=p):
    self.assertEqual(len(re.findall(r"\(00101100(?=[\s)])",(ROOT/p).read_text())),n)

if __name__=="__main__":
 unittest.main()
