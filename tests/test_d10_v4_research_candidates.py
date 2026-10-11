"""D10 v4 canonical candidate addition must preserve 698 historical laws."""
import importlib.util
import unittest
from pathlib import Path
path=Path(__file__).resolve().parents[1]/"scripts/check_d10_v4_research_candidates.py"
spec=importlib.util.spec_from_file_location("d10_v4",path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class TestV4(unittest.TestCase):
    def test_seven_hundred_and_seven(self):
        x=mod.verify(*mod.load())
        self.assertEqual((707,9,317,0),(x["selected"],x["new"],x["missing"],x["ratified"]))
    def test_negative_mutations(self):
        self.assertEqual(mod.negatives(*mod.load()),8)
if __name__=="__main__":
    unittest.main()
