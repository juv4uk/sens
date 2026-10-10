"""Незалежні негативні й позитивні свідки потокового досліду Tb-33."""

import itertools
import unittest

from tb33_tail_research import (
    BLOCK_BYTES,
    BLOCK_TRITS,
    SLOT_COUNT,
    TAIL_CAPACITY,
    TailError,
    decode,
    encode,
    final_rank,
    final_unrank,
    rank,
    tail_count,
    unrank,
    ways,
)


class Tb33TailWitness(unittest.TestCase):
    def test_tail_capacity_fits_in_46_bits(self) -> None:
        self.assertEqual(BLOCK_BYTES, 6)
        self.assertEqual(BLOCK_TRITS, 33)
        self.assertEqual(TAIL_CAPACITY, 57734709947051)
        self.assertLess(TAIL_CAPACITY, 1 << 46)
        self.assertLess(ways(33), SLOT_COUNT)

    def test_last_rank_separates_old_collision(self) -> None:
        short, long = (0, 1), (0, 0, 1)
        self.assertEqual(rank(short), rank(long))
        self.assertNotEqual(final_rank(short), final_rank(long))
        self.assertEqual(decode(encode(short)), short)
        self.assertEqual(decode(encode(long)), long)

    def test_exhaustive_terminal_lengths_to_eight(self) -> None:
        for length in range(2, 9):
            accepted = [
                prefix + (0, 1)
                for prefix in itertools.product((0, 1, 2), repeat=length - 2)
                if all(a != b or a != 2 for a, b in zip(prefix, prefix[1:]))
            ]
            self.assertEqual(len(accepted), tail_count(length))
            for item in accepted:
                packed = encode(item)
                self.assertEqual(len(packed), BLOCK_BYTES)
                self.assertEqual(decode(packed), item)
                self.assertEqual(final_unrank(final_rank(item)), item)

    def test_full_boundary_lengths_and_sole_one_tail(self) -> None:
        for length in (2, 3, 32, 33, 34, 35, 65, 66, 67, 68, 99, 100, 101, 132, 133, 134):
            stream = (0,) * (length - 2) + (0, 1)
            encoded = encode(stream)
            self.assertEqual(len(encoded), ((length - 1) // 33 + 1) * 6)
            self.assertEqual(decode(encoded), stream)

    def test_long_mixed_streams(self) -> None:
        for length in (45, 64, 70, 98, 131, 200):
            prefix = tuple((0, 1, 2)[i % 3] for i in range(length - 2))
            stream = prefix + (0, 1)
            self.assertEqual(decode(encode(stream)), stream)

    def test_rejects_22_at_block_boundary(self) -> None:
        first = (0,) * 32 + (2,)
        suffix = (2, 0, 1)
        with self.assertRaises(TailError):
            encode(first + suffix)
        wire = rank(first).to_bytes(6, "big") + final_rank(suffix).to_bytes(6, "big")
        with self.assertRaises(TailError):
            decode(wire)

    def test_final_single_trit_requires_previous_zero(self) -> None:
        first = (0,) * 32 + (2,)
        wire = rank(first).to_bytes(6, "big") + final_rank((1,)).to_bytes(6, "big")
        with self.assertRaises(TailError):
            decode(wire)

    def test_invalid_rank_and_incomplete_bytes_fail_closed(self) -> None:
        with self.assertRaises(TailError):
            decode(b"")
        with self.assertRaises(TailError):
            decode(bytes((0,)))
        with self.assertRaises(TailError):
            decode(TAIL_CAPACITY.to_bytes(6, "big"))
        with self.assertRaises(TailError):
            decode(ways(33).to_bytes(6, "big") + final_rank((0, 1)).to_bytes(6, "big"))
        with self.assertRaises(TailError):
            unrank(33, ways(33))

    def test_actual_framed3_syntax_stays_a_separate_layer(self) -> None:
        from research_codec import transport

        source = transport(("10", "001", "00", "000", "01"))
        self.assertEqual(decode(encode(source)), source)
        # Tb-33 не має права сам оголошувати семантичну правильність D2.


if __name__ == "__main__":
    unittest.main()
