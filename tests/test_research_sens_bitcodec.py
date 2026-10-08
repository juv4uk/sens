"""Два оборотні нетекстові носії; НЕ тести семантики чи затвердженого .sens."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "research_sens_bitcodec", ROOT / "scripts/research_sens_bitcodec.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ExperimentalBitCodecTests(unittest.TestCase):
    def test_ratified_d7_space_and_number_ladder(self):
        widths = mod.ratified_widths()
        self.assertEqual(widths, set(range(1, 10)) | {24, 48, 96, 192})
        self.assertEqual(mod.D7_SPACE, "1100000")

    def test_vertical_source_exact_words(self):
        words = mod.source_words("10\n001\n00\n000\n01\n")
        self.assertEqual(words, ("10", "001", "00", "000", "01"))
        self.assertEqual(mod.render_vertical(words), "10\n001\n00\n000\n01\n")

    def test_disallow_unratified_width_and_blank_line(self):
        for text in ("", "101\n\n", "101 0\n", "0" * 10 + "\n", "01"):
            with self.subTest(text=text):
                with self.assertRaises(mod.CodecError):
                    mod.source_words(text)

    def test_example_has_12_semantic_bits_not_ascii_bytes(self):
        words = ("10", "001", "00", "000", "01")
        a = mod.physical_stats(words, "width4")
        b = mod.physical_stats(words, "d7-marker")
        self.assertEqual(a["semantic_bits"], 12)
        self.assertEqual(a["boundary_and_eos_bits"], 24)
        self.assertEqual(a["encoded_bits"], 36)
        self.assertEqual(a["physical_bytes"], 5)
        self.assertEqual(a["tail_unused_bits"], 4)
        self.assertTrue(a["roundtrip_exact_words"])
        self.assertEqual(b["semantic_bits"], 12)
        self.assertEqual(b["boundary_and_eos_bits"], 35)
        self.assertEqual(b["escaped_extra_bits"], 3)
        self.assertEqual(b["encoded_bits"], 50)
        self.assertEqual(b["physical_bytes"], 7)
        self.assertEqual(b["tail_unused_bits"], 6)
        self.assertTrue(b["roundtrip_exact_words"])

    def test_collision_that_naked_bits_cannot_distinguish(self):
        a = ("0", "00")
        b = ("000",)
        self.assertEqual("".join(a), "".join(b))
        for encoder, decoder in (
            (mod.encode_width4, mod.decode_width4),
            (mod.encode_d7_marker, mod.decode_d7_marker),
        ):
            with self.subTest(encoder=encoder.__name__):
                self.assertNotEqual(encoder(a), encoder(b))
                self.assertEqual(decoder(encoder(a)), a)
                self.assertEqual(decoder(encoder(b)), b)

    def test_d7_delimiter_occurs_as_prefix_and_inside_words(self):
        for raw in ("1100000", "11000001", "11111111", "0000000", "1100001"):
            with self.subTest(raw=raw):
                words = (raw, "10", raw)
                self.assertEqual(mod.decode_d7_marker(mod.encode_d7_marker(words)), words)

    def test_all_one_to_nine_bit_values_roundtrip(self):
        for width in range(1, 10):
            for value in range(1 << width):
                bits = f"{value:0{width}b}"
                for encoder, decoder in (
                    (mod.encode_width4, mod.decode_width4),
                    (mod.encode_d7_marker, mod.decode_d7_marker),
                ):
                    with self.subTest(width=width, value=value, algorithm=encoder.__name__):
                        self.assertEqual(decoder(encoder((bits,))), (bits,))

    def test_number_widths_preserved_but_number_meanings_not_invented(self):
        for width in (24, 48, 96, 192):
            word = ("0" * (width-1)) + "1"
            for enc, dec in (
                (mod.encode_width4, mod.decode_width4),
                (mod.encode_d7_marker, mod.decode_d7_marker),
            ):
                with self.subTest(width=width, enc=enc.__name__):
                    self.assertEqual(dec(enc((word,))), (word,))

    def test_random_mixed_widths_roundtrip_and_exact_accounting(self):
        rng = random.Random(4438)
        widths = tuple(sorted(mod.ratified_widths()))
        for _ in range(120):
            ws = tuple(
                "".join(rng.choice("01") for _ in range(rng.choice(widths)))
                for unused in range(rng.randint(1, 15))
            )
            for algo in ("width4", "d7-marker"):
                stats = mod.physical_stats(ws, algo)
                self.assertTrue(stats["roundtrip_exact_words"])
                self.assertEqual(stats["physical_bits"],
                                 stats["encoded_bits"] + stats["tail_unused_bits"])
                self.assertTrue(0 <= stats["tail_unused_bits"] < 8)

    def test_append_extra_zero_byte_is_not_free_padding(self):
        for encoder, decoder in (
            (mod.encode_width4, mod.decode_width4),
            (mod.encode_d7_marker, mod.decode_d7_marker),
        ):
            data = encoder(("10", "001", "00", "000", "01"))
            with self.subTest(encoder=encoder.__name__):
                with self.assertRaises(mod.CodecError):
                    decoder(data + b"\x00")

    def test_unrecognized_or_truncated_marker_rejected(self):
        for payload in (b"\xff", b"\x00", b"\x80"):
            with self.subTest(payload=payload):
                with self.assertRaises(mod.CodecError):
                    mod.decode_d7_marker(payload)

    def test_width4_eos_can_not_be_faked_by_a_truncated_word(self):
        with self.assertRaises(mod.CodecError):
            mod.decode_width4(bytes.fromhex("f0"))

    def test_d7_payload_is_always_free_of_reserved_11_flag(self):
        for bits in ("1100000", "111111111", "0" * 192, "10" * 24):
            safe = mod._safe_word(bits)
            self.assertNotIn("11", safe)
            self.assertEqual(safe[-1], "0")


if __name__ == "__main__":
    unittest.main()
