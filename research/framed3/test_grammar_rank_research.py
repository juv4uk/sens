"""Вичерпні позитивні й негативні докази граматичного рангу; без assert-guard."""
import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grammar_rank_research as grammar
import research_codec as oracle


class GrammarProof(unittest.TestCase):
    def test_outer_words_already_fixed_in_original_frame(self):
        for n in range(4, oracle.MAX_TRITS + 1):
            self.assertEqual(oracle.capacity(n),
                             grammar.count_no_adjacent_22(n - 4))

    def test_exhaust_all_short_ternary_middles(self):
        for k in range(9):
            ranks = set()
            for digits in itertools.product("012", repeat=k):
                middle = "".join(digits)
                words = ("10", *(middle.split("2") if middle else ()), "01")
                try:
                    oracle.transport(words)
                except oracle.FrameError:
                    with self.assertRaises(grammar.GrammarError):
                        grammar.rank_inner(words)
                    continue
                rank = grammar.rank_inner(words)
                self.assertNotIn(rank, ranks)
                ranks.add(rank)
                self.assertEqual(grammar.unrank_inner(k, rank), words)
                blob = grammar.encode(words)
                self.assertEqual(grammar.decode(blob), words)
                self.assertLessEqual(len(blob), len(oracle.encode(words)))
            self.assertEqual(len(ranks), grammar.count_middle(k))
            self.assertEqual(ranks, set(range(grammar.count_middle(k))))

    def test_one_byte_entire_code_space(self):
        valid = 0
        for byte in range(256):
            blob = bytes((byte,))
            try:
                words = grammar.decode(blob)
            except grammar.GrammarError:
                continue
            self.assertEqual(grammar.encode(words), blob)
            valid += 1
        self.assertEqual(valid, 118)

    def test_exact_buckets_without_hidden_length(self):
        self.assertEqual(grammar.buckets()[:3],
                         ((1, 0, 5), (2, 6, 11), (3, 12, 17)))
        for width, first, last in grammar.buckets():
            used = sum(grammar.count_middle(k) for k in range(first, last + 1))
            self.assertLessEqual(used, 256 ** width)
            if last < grammar.MAX_TRITS - 4:
                self.assertGreater(used + grammar.count_middle(last + 1),
                                   256 ** width)

    def test_byte_savings_are_from_grammar_not_omitted_outer_bits(self):
        fixtures = (
            ("10", "01"),
            ("10", "001", "00", "000", "01"),
            tuple("10 100 00 10 111 00 1 00 0 01 01".split()),
            ("10", "11111", "01"),
            ("10", "0", "0", "0", "0", "0", "0", "01"),
        )
        for words in fixtures:
            self.assertTrue(grammar.fixed_frame_identity(words))
            self.assertEqual(grammar.decode(grammar.encode(words)), words)
        self.assertEqual(len(oracle.encode(("10", "11111", "01"))), 2)
        self.assertEqual(len(grammar.encode(("10", "11111", "01"))), 1)
        many = ("10", "0", "0", "0", "0", "0", "0", "01")
        self.assertEqual(len(oracle.encode(many)), 3)
        self.assertEqual(len(grammar.encode(many)), 2)

    def test_reject_unsupported_forms_bad_words_and_unused_codes(self):
        for words in ((), ("10",), ("01",),
                      ("10", "01", "10", "01"),
                      ("10", "01", "00"), ("10", "10", "01"),
                      ("10", "0"*10, "01"), ("10", "12", "01"),
                      ("10", "", "01"), ("10", "0", "2", "01")):
            with self.subTest(words=words):
                with self.assertRaises(grammar.GrammarError):
                    grammar.encode(words)
        for blob in (b"", b"\xff", b"\xf3", b"\xff\xff"):
            with self.subTest(blob=blob):
                with self.assertRaises(grammar.GrammarError):
                    grammar.decode(blob)
        for k in (0, 1, 5, 9, 12):
            with self.assertRaises(grammar.GrammarError):
                grammar.unrank_inner(k, grammar.count_middle(k))


if __name__ == "__main__":
    unittest.main()
