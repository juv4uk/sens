"""Pinned source-only D6 LET cutover and mixed-width collision regression."""
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = {
 "lib/forward.lisp": ("f94d602b9b40668ec1f17e3b51956eaf72af74d2", 19),
 "lib/knowledge.lisp": ("4f314e54da95ef9af8f51cc6b87b8d665cc65a8a", 25),
}
OLD = re.compile(r"\(10011100(?=[\s)])")
NEW = re.compile(r"\(001000(?=[\s)])")

class SourceLaw(unittest.TestCase):
 def test_let_coordinate_ratification_and_d8_collision(self):
  ds=json.loads((ROOT/"knowledge/d1-d9-foundation.json").read_text())["domains"]
  self.assertEqual(ds["D6"]["residents"]["001000"],"LET")
  self.assertEqual(ds["D8"]["residents"]["10011100"],"CADDDAAR")

 def test_exact_44_original_let_binder_sites(self):
  total=0
  for path,(blob,count) in BASE.items():
   with self.subTest(path=path):
    old=subprocess.run(["git","cat-file","blob",blob],cwd=ROOT,check=True,capture_output=True).stdout.decode()
    current=(ROOT/path).read_text(encoding="utf-8")
    places=list(OLD.finditer(old))
    self.assertEqual(len(places),count)
    for p in places:
     self.assertRegex(old[p.start():p.start()+75],r"^\(10011100\s+\(\(")
    self.assertEqual(current,OLD.sub("(001000",old))
    self.assertNotRegex(current,OLD)
    self.assertEqual(len(NEW.findall(current))-len(NEW.findall(old)),count)
    self.assertIn("(00001010",current)  # MACRO remains a semantic blocker
    total+=count
  self.assertEqual(total,44)

 def test_current_d8_mod_must_not_be_replaced_with_old_member(self):
  ds=json.loads((ROOT/"knowledge/d1-d9-foundation.json").read_text())["domains"]
  self.assertEqual(ds["D8"]["residents"]["00101100"],"MOD")
  for path,count in (("lib/time.lisp",3),("lib/core.lisp",2),("lib/core4.lisp",2)):
   with self.subTest(path=path):
    s=(ROOT/path).read_text(encoding="utf-8")
    self.assertEqual(len(re.findall(r"\(00101100(?=[\s)])",s)),count)

if __name__=="__main__":
 unittest.main()
