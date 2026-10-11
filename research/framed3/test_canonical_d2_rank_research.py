"""Independent bounded exhaustive D1–D9 word grammar oracle (no asserts)."""
from __future__ import annotations

from functools import lru_cache
import unittest

import canonical_d2_rank_research as ranker
from semantic_redundancy_research import Form, Word, definitely_impossible


class Rejected(ValueError):
    pass


def independent_reader(words: tuple[str, ...]) -> bool:
    """Separate recursive implementation of current Rust CanonicalReader D2."""
    if not all(ranker._word_valid(w) for w in words):
        return False
    pos = 0

    def separators():
        nonlocal pos
        while pos < len(words) and words[pos] == "00":
            pos += 1

    def expression():
        nonlocal pos
        if pos >= len(words):
            raise Rejected("missing expression")
        word = words[pos]
        if word == "10":
            list_expr()
        elif len(word) == 2:
            raise Rejected("unexpected structural token in expression")
        else:
            pos += 1

    def list_expr():
        nonlocal pos
        if pos >= len(words) or words[pos] != "10":
            raise Rejected("list must start with OPEN")
        pos += 1
        heads = 0
        while True:
            separators()
            if pos >= len(words):
                raise Rejected("unterminated list")
            if words[pos] == "01":
                pos += 1
                return
            if words[pos] == "11":
                if heads == 0:
                    raise Rejected("dot without head")
                pos += 1
                separators()
                expression()  # exactly one dotted tail
                separators()
                if pos >= len(words) or words[pos] != "01":
                    raise Rejected("dot must end immediately with CLOSE")
                pos += 1
                return
            expression()
            heads += 1

    try:
        list_expr()
        return pos == len(words)
    except Rejected:
        return False


@lru_cache(maxsize=None)
def all_bodies(bits: int) -> tuple[tuple[str, ...], ...]:
    """All exact widths 1..9, independently enumerated, including every D2."""
    if bits == 0:
        return ((),)
    result = []
    for width in range(1, min(9, bits) + 1):
        for value in range(1 << width):
            word = format(value, f"0{width}b")
            for suffix in all_bodies(bits - width):
                result.append((word, *suffix))
    return tuple(result)


class ExactD2GrammarProof(unittest.TestCase):
    def test_exhaustive_typed_D1_D9_streams_up_to_8_inner_bits(self):
        for bits in range(9):
            actual_ranks = set()
            independently_accepted = 0
            for body in all_bodies(bits):
                form = ("10", *body, "01")
                accepted = independent_reader(form)
                if not accepted:
                    with self.assertRaises(ranker.D2RankError):
                        ranker.rank(form)
                    continue
                independently_accepted += 1
                counted_bits, code = ranker.rank(form)
                self.assertEqual(counted_bits, bits)
                self.assertNotIn(code, actual_ranks)
                actual_ranks.add(code)
                self.assertEqual(ranker.unrank(bits, code), form)
            self.assertEqual(independently_accepted, ranker.count_inner(bits))
            self.assertEqual(actual_ranks, set(range(independently_accepted)))

    def test_D2_four_tokens_are_structural_not_payload(self):
        # Length 2: only W1+W1 (4 possibilities) and separator 00 (1).
        self.assertEqual(ranker.count_inner(2), 5)
        self.assertEqual(ranker.rank(("10", "00", "01")), (2, 4))
        for middle in ("01", "10", "11"):
            with self.subTest(middle=middle):
                with self.assertRaises(ranker.D2RankError):
                    ranker.rank(("10", middle, "01"))
        self.assertEqual(ranker.count_inner(0), 1)
        self.assertEqual(ranker.unrank(0, 0), ("10", "01"))
        self.assertEqual(ranker.rank(("10", "00", "00", "01"))[0], 4)

    def test_dotted_lists_and_quoted_nonexecutable_data_are_not_erased(self):
        accepted = (
            ("10", "0", "11", "1", "01"),
            ("10", "0", "11", "00", "1", "01"),
            ("10", "10", "010", "01", "01"),  # ((ATOM)) parseable, not executable
            ("10", "001", "10", "10", "010", "01", "01", "01"),
            ("10", "0", "11", "10", "1", "01", "01"),
            ("10", "10", "0", "11", "1", "01", "01"),
        )
        for form in accepted:
            with self.subTest(form=form):
                self.assertTrue(independent_reader(form))
                bits, value = ranker.rank(form)
                self.assertEqual(ranker.unrank(bits, value), form)
                body = ranker.rank_bytes_at_known_length(form)
                self.assertEqual(ranker.unrank_bytes_at_known_length(bits, body), form)
        dead_code = Form((Form((Word("010"),)),))
        quoted_data = Form((Word("001"), dead_code))
        self.assertTrue(definitely_impossible(dead_code))
        self.assertFalse(definitely_impossible(quoted_data))
        # Grammar count is a structural UPPER BOUND, never an executable count.

    def test_fail_closed_on_dot_truncation_bad_word_or_wrong_rank(self):
        rejected = (
            (), ("10",), ("10", "0", "11", "01"),
            ("10", "11", "0", "01"),
            ("10", "0", "11", "1", "0", "01"),
            ("10", "0", "11", "1"),
            ("10", "10", "01"),
            ("10", "0", "01", "01"),
            ("10", "010", "00", "1111111111", "01"),
        )
        for form in rejected:
            with self.subTest(form=form):
                with self.assertRaises(ranker.D2RankError):
                    ranker.rank(form)
        for count in (-1, 21, 2.1, True):
            with self.assertRaises(ranker.D2RankError):
                ranker.count_inner(count)
        for bits in range(8):
            with self.assertRaises(ranker.D2RankError):
                ranker.unrank(bits, ranker.count_inner(bits))
            with self.assertRaises(ranker.D2RankError):
                ranker.unrank(bits, -1)
        with self.assertRaises(ranker.D2RankError):
            ranker.unrank_bytes_at_known_length(2, b"\xff")
        with self.assertRaises(ranker.D2RankError):
            ranker.unrank_bytes_at_known_length(2, b"\x00\x00")

    def test_preserve_leading_zeros_and_exact_domain_width(self):
        for width in (1, 3, 4, 5, 6, 7, 8, 9):
            for value in (0, 1, (1 << width) - 1):
                form = ("10", format(value, f"0{width}b"), "01")
                bits, code = ranker.rank(form)
                self.assertEqual(bits, width)
                self.assertEqual(ranker.unrank(bits, code), form)
        self.assertNotEqual(ranker.rank(("10", "0", "01")),
                            ranker.rank(("10", "000", "01")))


if __name__ == "__main__":
    unittest.main()
