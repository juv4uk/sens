"""Quine 1952 / McCluskey 1956: D10 research-only prime cube family.

Two independent exact oracles. NOT an FPGA synthesis pass, minimum cover
algorithm, D10 selection, ratification, or executable binary SENS artifact.
"""
import itertools
import json
import unittest
from pathlib import Path


def _validate(width, on, dc):
    if type(width) is not int or not 0 <= width <= 4:
        raise ValueError("bounded oracle accepts 0<=n<=4 only")
    universe = set(range(1 << width))
    if any(type(v) is not int for v in on) or any(type(v) is not int for v in dc):
        raise ValueError("rank is not an integer")
    a, d = set(on), set(dc)
    if not a <= universe or not d <= universe or a & d:
        raise ValueError("invalid ON/DC partition")
    return universe, a, d


def _word(value, width):
    return format(value, f"0{width}b") if width else ""


def _covers(pattern, value, width):
    return all(p == "-" or p == b
               for p, b in zip(pattern, _word(value, width)))


def quine_merge_primes(width, on, dc=()):
    """Generate all maximal cubes by adjacency merges of ON+DC minterms."""
    universe, a, d = _validate(width, on, dc)
    current = {_word(v, width) for v in a | d}
    terminal = set()
    while current:
        absorbed, expanded = set(), set()
        for left, right in itertools.combinations(sorted(current), 2):
            mismatch = [i for i, (x, y) in enumerate(zip(left, right))
                        if x != y]
            if len(mismatch) != 1:
                continue
            i = mismatch[0]
            if {left[i], right[i]} != {"0", "1"}:
                continue
            absorbed.add(left)
            absorbed.add(right)
            expanded.add(left[:i] + "-" + left[i + 1:])
        terminal.update(current - absorbed)
        current = expanded
    return sorted(p for p in terminal
                  if any(_covers(p, v, width) for v in a))


def exhaustive_cube_primes(width, on, dc=()):
    """Independent reference: enumerate all 3**width cubes, test maximality."""
    universe, a, d = _validate(width, on, dc)
    off = universe - a - d
    primes = []
    for digits in itertools.product("-01", repeat=width):
        cube = "".join(digits)
        coverage = {v for v in universe if _covers(cube, v, width)}
        if not coverage & a or coverage & off:
            continue
        has_valid_relaxation = False
        for i, symbol in enumerate(cube):
            if symbol == "-":
                continue
            relaxation = cube[:i] + "-" + cube[i + 1:]
            if all(not _covers(relaxation, v, width) for v in off):
                has_valid_relaxation = True
                break
        if not has_valid_relaxation:
            primes.append(cube)
    return sorted(primes)


class QuinePrimeImplicantsD10Research(unittest.TestCase):
    def test_named_witnesses(self):
        cases = [
            (2, [1, 3], [], ["-1"]),
            (2, [1, 2], [], ["01", "10"]),
            (3, [1, 3, 5, 7], [], ["--1"]),
            (2, [0], [1], ["0-"]),
            (2, [0, 1, 2, 3], [], ["--"]),
            (2, [], [1, 2], []),
            (0, [0], [], [""]),
            (0, [], [0], []),
            (4, [0, 1, 4, 5], [], ["0-0-"]),
        ]
        for width, on, dc, want in cases:
            with self.subTest(n=width, on=on, dc=dc):
                self.assertEqual(quine_merge_primes(width, on, dc), want)
                self.assertEqual(exhaustive_cube_primes(width, on, dc), want)

    def test_complete_ternary_function_census_width_zero_to_three(self):
        total = 0
        for n in range(4):
            size = 1 << n
            for assignment in itertools.product("ODF", repeat=size):
                on = {v for v, state in enumerate(assignment) if state == "O"}
                dc = {v for v, state in enumerate(assignment) if state == "D"}
                derived = quine_merge_primes(n, on, dc)
                reference = exhaustive_cube_primes(n, on, dc)
                self.assertEqual(derived, reference,
                                 f"n={n}, ON={on}, DC={dc}")
                self.assertEqual(len(derived), len(set(derived)))
                self.assertTrue(all(any(_covers(p, v, n) for p in derived)
                                    for v in on))
                total += 1
        self.assertEqual(total, 6654)

    def test_bad_inputs_and_false_minimum_cover(self):
        cases = [
            (2, [1], [1]), (2, [4], []), (0, [1], []),
            (2, [-1], []), (2, [0.0], []), (True, [], []),
            (5, [], []),
        ]
        for n, on, dc in cases:
            with self.subTest(n=n, on=on, dc=dc):
                with self.assertRaises(ValueError):
                    quine_merge_primes(n, on, dc)
                with self.assertRaises(ValueError):
                    exhaustive_cube_primes(n, on, dc)
        self.assertNotEqual(quine_merge_primes(2, [1, 2]), ["--"])

    def test_research_only_guard(self):
        doc = Path(__file__).resolve().parents[1] / "knowledge" / "d10-quine-prime-implicants-20261009.json"
        spec = json.loads(doc.read_text(encoding="utf-8"))
        p = spec["proposal"]
        self.assertEqual(spec["status"], "RESEARCH-HOLD-CORE-VS-LIBRARY-NOT-SELECTED")
        self.assertFalse(p["status"] != "RESEARCH-UNSELECTED")
        self.assertFalse(p["ratified"])
        self.assertIsNone(p["coordinate"])
        self.assertFalse(p["physical_t5_authorized"])


if __name__ == "__main__":
    unittest.main()
