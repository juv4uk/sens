"""GF(2) linear complexity: research oracles, NOT executable SENS Core."""
import itertools
import unittest


def _validated_bits(word):
    if not isinstance(word, str) or any(c not in "01" for c in word):
        raise ValueError("Expected finite exact D1 word written with 0/1")
    return [int(c) for c in word]


def berlekamp_massey_complexity(word):
    """Berlekamp–Massey connection polynomial, GF(2), scalar length only."""
    bits = _validated_bits(word)
    n = len(bits)
    current = [1] + [0] * n
    previous = [1] + [0] * n
    length, previous_discrepancy_at = 0, -1
    for pos in range(n):
        discrepancy = bits[pos]
        for k in range(1, length + 1):
            discrepancy ^= current[k] & bits[pos - k]
        if not discrepancy:
            continue
        old_current = current.copy()
        shift = pos - previous_discrepancy_at
        for k in range(n + 1 - shift):
            current[k + shift] ^= previous[k]
        if 2 * length <= pos:
            length = pos + 1 - length
            previous, previous_discrepancy_at = old_current, pos
    return length


def exhaustive_complexity(word):
    """Independent witness search: every GF(2) recurrence, smallest order first."""
    bits = _validated_bits(word)
    n = len(bits)
    for length in range(n + 1):
        for coefficients in itertools.product((0, 1), repeat=length):
            if all(
                bits[t] == (sum(coefficients[j - 1] * bits[t - j]
                                for j in range(1, length + 1)) % 2)
                for t in range(length, n)
            ):
                return length
    raise AssertionError("order n is always an admissible finite prefix witness")


class ResearchD10GF2LinearComplexity(unittest.TestCase):
    def test_fixed_source_and_adversarial_witnesses(self):
        cases = {
            "": 0,
            "000": 0,
            "1111": 1,
            "1000": 1,
            "001": 3,
            "0001": 4,
            "010101": 2,
            "1101011110001": 4,
        }
        for word, expected in cases.items():
            with self.subTest(word=word):
                self.assertEqual(berlekamp_massey_complexity(word), expected)
                self.assertEqual(exhaustive_complexity(word), expected)

    def test_all_binary_words_of_lengths_zero_to_ten(self):
        checked = 0
        for n in range(11):
            for value in range(1 << n):
                word = format(value, f"0{n}b") if n else ""
                self.assertEqual(
                    berlekamp_massey_complexity(word),
                    exhaustive_complexity(word),
                    f"witness failed for exact word {word!r}",
                )
                checked += 1
        self.assertEqual(checked, 2047)

    def test_invalid_inputs_fail_closed(self):
        for item in ("102", "a", "0 1", "00\\n", None, 101):
            with self.subTest(value=item), self.assertRaises(ValueError):
                berlekamp_massey_complexity(item)
            with self.subTest(value=item), self.assertRaises(ValueError):
                exhaustive_complexity(item)

    def test_non_promotion(self):
        from pathlib import Path
        import json
        dossier = Path(__file__).resolve().parents[1] / "knowledge" / "d10-gf2-linear-complexity-research-20261009.json"
        obj = json.loads(dossier.read_text(encoding="utf-8"))
        self.assertEqual(obj["status"], "RESEARCH-PENDING-SEMANTIC-DEDUP-NOT-SELECTED")
        self.assertFalse(obj["candidate"]["selected"])
        self.assertFalse(obj["candidate"]["ratified"])
        self.assertIsNone(obj["candidate"]["coordinate"])
        self.assertFalse(obj["candidate"]["admitted_T5"])


if __name__ == "__main__":
    unittest.main()
