"""D10 v3 regression: retain 23 already researched candidates and reject drift."""
import importlib.util
import unittest
from pathlib import Path
script=Path(__file__).resolve().parents[1]/"scripts/check_d10_v3_archived_candidates.py"
spec=importlib.util.spec_from_file_location("d10_v3",script)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class V3(unittest.TestCase):
    def test_698_selected_research_candidates(self):
        r=mod.verify(*mod.load())
        self.assertEqual((698,23,326,0),
            (r["selected"],r["new_candidates"],r["missing"],r["ratified"]))

    def test_negative_changes_fail(self):
        a,b,c,d,e=mod.load()
        self.assertEqual(mod.self_test(a,b,c,d,e),8)
if __name__=="__main__":
    unittest.main()
