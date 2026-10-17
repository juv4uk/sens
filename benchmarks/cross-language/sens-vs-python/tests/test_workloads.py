import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from workloads import ackermann, binary_trees, binary_trees_checks, fib, json_roundtrip  # noqa: E402


class WorkloadTests(unittest.TestCase):
    def test_ackermann_uses_nested_recursive_recurrence(self):
        self.assertEqual(ackermann(3, 3), 61)

    def test_fib_uses_recursive_recurrence_and_matches_fixed_answer(self):
        self.assertEqual(fib(16), 987)

    def test_binary_trees_n10_matches_pinned_clbg_output(self):
        expected = (ROOT.parent.parent / "standard" / "binary-trees" / "expected-n10.txt").read_text()
        self.assertEqual(binary_trees(10), expected)

    def test_binary_trees_checks_match_pinned_n10_counts(self):
        self.assertEqual(binary_trees_checks(10), [4095, 31744, 32512, 32704, 32752, 2047])

    def test_binary_trees_small_case_has_expected_work_counts(self):
        self.assertEqual(
            binary_trees(4),
            "stretch tree of depth 7\t check: 255\n"
            "64\t trees of depth 4\t check: 1984\n"
            "16\t trees of depth 6\t check: 2032\n"
            "long lived tree of depth 6\t check: 127\n",
        )

    def test_json_roundtrip_returns_canonical_compact_document(self):
        fixture = (ROOT / "fixtures" / "json-small.json").read_text()
        self.assertEqual(
            json_roundtrip(fixture),
            '{"items":[{"id":1,"name":"alpha"},{"id":2,"name":"beta"}],"title":"SENS"}',
        )


if __name__ == "__main__":
    unittest.main()
