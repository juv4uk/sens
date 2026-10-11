"""Negative/positive methodology witnesses. SYNTHETIC timings, not SENS data."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "sens_paired_effect", Path(__file__).with_name("paired_effect.py")
)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

H = "a" * 64
SHA = "f" * 40
ENV = {
    "cpu_model": "SYNTHETIC CPU", "rustc": "rustc SYNTHETIC",
    "profile": "release", "cpu_governor": "performance",
    "turbo_state": "disabled", "affinity": "2",
}


def data(builds=3, rounds=12, effect=True):
    return {
        "schema": p.SCHEMA, "metric": "wall_ns", "sha": SHA,
        "input_sha256": H, "output_sha256": H,
        "builds": [
            {
                "build_id": f"b-{b}", "binary_sha256": H,
                "environment": dict(ENV),
                "rounds": [
                    {
                        "order": "ABBA" if k % 2 == 0 else "BAAB",
                        "samples_ns": (
                            ([100 + b, 60 + b, 60 + b, 100 + b] if k % 2 == 0
                             else [60 + b, 100 + b, 100 + b, 60 + b])
                            if effect else [100 + b] * 4
                        ),
                        "outputs_sha256": [H] * 4,
                    }
                    for k in range(rounds)
                ],
            }
            for b in range(builds)
        ],
    }


class PairedVerdictTests(unittest.TestCase):
    def test_multibuild_clear_win(self):
        r = p.evaluate(data(), 1000)
        self.assertEqual(r["verdict"], "FASTER_ON_MATCHED_WALL_WORKLOAD")
        self.assertGreater(r["confidence_95_ratio"][0], 1)

    def test_one_build_is_unverified_even_when_fast(self):
        self.assertEqual(p.evaluate(data(builds=1), 1000)["verdict"], "UNVERIFIED_MULTIBUILD")

    def test_few_rounds_unverified(self):
        self.assertEqual(p.evaluate(data(rounds=2), 1000)["verdict"], "UNVERIFIED_MULTIBUILD")

    def test_equal_timing_inconclusive(self):
        self.assertEqual(p.evaluate(data(effect=False), 1000)["verdict"], "INCONCLUSIVE")

    def test_output_mismatch_blocked(self):
        x = data()
        x["builds"][1]["rounds"][2]["outputs_sha256"][0] = "b" * 64
        with self.assertRaisesRegex(p.EvidenceError, "parity"):
            p.evaluate(x, 1000)

    def test_missing_position_blocked(self):
        x = data()
        x["builds"][0]["rounds"][0]["samples_ns"] = [100, 60, 100]
        with self.assertRaisesRegex(p.EvidenceError, "four"):
            p.evaluate(x, 1000)

    def test_nonpositive_times_blocked(self):
        x = data()
        x["builds"][1]["rounds"][1]["samples_ns"][1] = 0
        with self.assertRaisesRegex(p.EvidenceError, "finite positive"):
            p.evaluate(x, 1000)

    def test_mixed_cpu_blocked(self):
        x = data()
        x["builds"][2]["environment"]["cpu_model"] = "Different CPU"
        with self.assertRaisesRegex(p.EvidenceError, "mixed CPU"):
            p.evaluate(x, 1000)

    def test_instruction_metric_rejected(self):
        x = data()
        x["metric"] = "callgrind_irefs"
        with self.assertRaisesRegex(p.EvidenceError, "wall_ns"):
            p.evaluate(x, 1000)

    def test_uncontrolled_environment_unverified(self):
        x = data()
        for build in x["builds"]:
            build["environment"]["turbo_state"] = "unknown"
        self.assertEqual(p.evaluate(x, 1000)["verdict"], "UNVERIFIED_ENVIRONMENT")

    def test_duplicate_build_rejected(self):
        x = data()
        x["builds"][2]["build_id"] = x["builds"][1]["build_id"]
        with self.assertRaisesRegex(p.EvidenceError, "duplicate"):
            p.evaluate(x, 1000)

    def test_bootstrap_seed_reproducible(self):
        a, b = p.evaluate(data(), 1000), p.evaluate(data(), 1000)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
