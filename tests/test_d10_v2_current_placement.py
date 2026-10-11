"""Regression: owner-directed D10 v2 canonical research placement."""
import importlib.util
import unittest
from pathlib import Path

source=Path(__file__).resolve().parents[1]/"scripts/check_d10_v2_current_placement.py"
spec=importlib.util.spec_from_file_location("d10_current",source)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class V2Current(unittest.TestCase):
    def test_canonical_675(self):
        result=module.verify(*module.load())
        self.assertEqual((675,675,419,256,349,0),
            (result["selected"],result["placed"],result["owner_gauge"],result["law_forced"],
             result["capacity_left"],result["ratified"]))

    def test_fail_closed_eight_mutations(self):
        self.assertEqual(8,module.negative_tests(*module.load()))

if __name__=="__main__":
    unittest.main()
