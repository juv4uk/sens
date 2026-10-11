from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("domain_altitude_economy", MODULE_PATH)
assert SPEC and SPEC.loader
dae = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dae
SPEC.loader.exec_module(dae)


def point(
    case: str,
    variant: str,
    digest: str,
    widths: tuple[int, ...],
    bits: int,
    *,
    pair: str | None = None,
    role: str | None = None,
):
    return dae.Point(
        case_id=case,
        variant_id=variant,
        observable_digest=digest,
        semantic_widths=widths,
        exact_bits=bits,
        residency_pair_id=pair,
        representation_role=role,
    )


class DomainAltitudeEconomyTests(unittest.TestCase):
    def test_strict_dominance_requires_both_axes_no_worse(self):
        low_small = point("c1", "low-small", "same", (3, 3), 20)
        high_large = point("c1", "high-large", "same", (3, 8), 30)
        report = dae.build_report([low_small, high_large])
        rows = {row["variant_id"]: row for row in report["cases"][0]["variants"]}
        self.assertTrue(rows["low-small"]["pareto_front"])
        self.assertFalse(rows["high-large"]["pareto_front"])
        self.assertEqual(rows["high-large"]["dominated_by"], ["low-small"])

    def test_tradeoff_keeps_both_variants_on_frontier(self):
        lower_larger = point("c1", "lower-larger", "same", (3,), 40)
        higher_smaller = point("c1", "higher-smaller", "same", (8,), 24)
        report = dae.build_report([lower_larger, higher_smaller])
        self.assertEqual(
            report["cases"][0]["frontier"],
            ["higher-smaller", "lower-larger"],
        )

    def test_digest_mismatch_is_not_comparable(self):
        a = point("c1", "a", "digest-a", (3,), 20)
        b = point("c1", "b", "digest-b", (4,), 18)
        with self.assertRaisesRegex(ValueError, "observable digest mismatch"):
            dae.build_report([a, b])

    def test_residency_dividend_is_expansion_minus_resident_bits(self):
        resident = point(
            "c1",
            "resident",
            "same",
            (8,),
            8,
            pair="D8:x/use-1",
            role="resident",
        )
        expanded = point(
            "c1",
            "expanded",
            "same",
            (3, 3, 3, 3),
            31,
            pair="D8:x/use-1",
            role="expanded",
        )
        report = dae.build_report([resident, expanded])
        dividend = report["residency_dividends"][0]
        self.assertEqual(dividend["bit_dividend"], 23)
        self.assertEqual(dividend["resident_altitude"], 8)
        self.assertEqual(dividend["expanded_altitude"], 3)


if __name__ == "__main__":
    unittest.main()
