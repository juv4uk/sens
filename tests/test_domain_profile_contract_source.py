"""Regression guards for exact D3 profile and retired eight-bit bootstrap."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DomainProfileContractSourceTests(unittest.TestCase):
    def test_profile_follows_owner_ratified_d3(self):
        domain = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        profile = (ROOT / "contracts/core-profile-contract.lisp").read_text(encoding="utf-8")
        rows = re.findall(
            r"(?m)^\s*\(([01]{3})\s+.*?\(LISP\s+(ATOM|EQ|COND)\)",
            domain,
        )
        expected = {name.lower(): bits for bits, name in rows}
        self.assertEqual(set(expected), {"atom", "eq", "cond"})
        for name, bits in expected.items():
            with self.subTest(name=name):
                pattern = rf'\({name}-object\s*\.\s*\(Core\.D3\s+"{bits}"\)\)'
                self.assertRegex(profile, pattern)

    def test_retired_sid8_overlay_does_not_reenter_runtime(self):
        profile = (ROOT / "contracts/core-profile-contract.lisp").read_text(encoding="utf-8")
        self.assertNotIn("core1-sid8-bootstrap-overlay.lisp", profile)
        self.assertFalse((ROOT / "lib/core1-sid8-bootstrap-overlay.lisp").exists())


if __name__ == "__main__":
    unittest.main()
