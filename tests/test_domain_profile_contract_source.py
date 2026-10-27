"""Механічний контроль відсутності застарілого SID8 накладання у runtime."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DomainProfileContractSourceTests(unittest.TestCase):
    def test_retired_sid8_overlay_does_not_reenter_runtime(self):
        profile = (ROOT / "contracts/core-profile-contract.lisp").read_text(encoding="utf-8")
        self.assertNotIn("core1-sid8-bootstrap-overlay.lisp", profile)
        self.assertFalse((ROOT / "lib/core1-sid8-bootstrap-overlay.lisp").exists())


if __name__ == "__main__":
    unittest.main()
