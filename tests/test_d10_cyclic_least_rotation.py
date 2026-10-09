"""Research-only oracle for a finite binary word's canonical cyclic rotation.

No SENS runtime, binary coordinate, or physical .sens admission is tested here.
"""
import unittest


def least_rotation(word):
    if any(bit not in "01" for bit in word):
        raise ValueError("finite D1 word must contain only 0/1")
    if not word:
        return "", 0
    candidates = [(word[k:] + word[:k], k) for k in range(len(word))]
    return min(candidates)


def independent_rotation_oracle(word):
    # Independent brute-force reference via doubled-word indexing.
    n = len(word)
    if n == 0:
        return "", 0
    doubled = word + word
    smallest = min(doubled[k:k + n] for k in range(n))
    first = next(k for k in range(n) if doubled[k:k + n] == smallest)
    return smallest, first


class CyclicLeastRotationResearch(unittest.TestCase):
    def test_witnesses(self):
        cases = {"": ("", 0), "1100": ("0011", 2),
                 "1010": ("0101", 1), "0101": ("0101", 0),
                 "000": ("000", 0), "10100": ("00101", 3)}
        for word, expected in cases.items():
            with self.subTest(word=word):
                self.assertEqual(least_rotation(word), expected)

    def test_all_words_through_length_12(self):
        checks = 0
        for n in range(13):
            for val in range(1 << n):
                word = format(val, f"0{n}b") if n else ""
                actual = least_rotation(word)
                self.assertEqual(actual, independent_rotation_oracle(word))
                self.assertEqual(len(actual[0]), n)
                self.assertEqual(least_rotation(actual[0]), (actual[0], 0))
                checks += 1
        self.assertEqual(checks, 8191)

    def test_negative_controls(self):
        self.assertNotEqual(least_rotation("1010")[0], "01")
        self.assertNotEqual(least_rotation("1010")[1], 3)
        with self.assertRaises(ValueError):
            least_rotation("102")


if __name__ == "__main__":
    unittest.main()
