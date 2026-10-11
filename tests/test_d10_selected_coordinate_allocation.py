"""D10 419-coordinate injectivity, source trace, fail-closed tests."""
import importlib.util
import unittest
from pathlib import Path

f=Path(__file__).resolve().parents[1]/"scripts/check_d10_selected_coordinate_allocation.py"
spec=importlib.util.spec_from_file_location("d10_alloc",f)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Tests(unittest.TestCase):
    def test_all_selected_have_unique_research_gauge(self):
        a,b,c,hi,hs=module.load()
        result=module.verify(a,b,c,hi,hs)
        self.assertEqual((419,675,349,0),(result["allocated"],result["mapped"],result["free"],result["ratified"]))
    def test_mutations_fail_closed(self):
        a,b,c,hi,hs=module.load()
        self.assertEqual(module.reject_mutations(a,b,c,hi,hs),8)

if __name__ == "__main__":
    unittest.main()
