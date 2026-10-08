#!/usr/bin/env python3
"""Executable regression suite for multi-program keyed T5 timing/EOF stream."""
import copy
import math
import random
import unittest

from t5_stream import (
    ChannelError, Receiver, identity_sha256, make_stream, parse_program,
    receive, summary, t5_pack, t5_unpack,
)


class T5HumanAirStreamTests(unittest.TestCase):
    def test_three_program_stream_including_atom_and_nested_form(self):
        programs = [
            parse_program("10 001 01"),
            parse_program("10 000 10 001 01 01"),
            parse_program("000"),
        ]
        events = make_stream(programs)
        self.assertEqual(receive(events), programs)
        self.assertEqual(sum(x["kind"] == "gap" and x["units"] == 21 for x in events), 3)
        s = summary(receive(events), events, unit_ms=60, source=programs)
        self.assertEqual(s["program_count"], 3)
        self.assertTrue(s["matches_expected_words"])
        self.assertEqual(s["frame_gap_events"], 3)
        self.assertEqual(s["semantic_bits"], 7 + 14 + 3)
        self.assertGreater(s["net_semantic_bits_per_second"], 0)

    def test_jitter_20_percent_preserves_multiple_programs(self):
        programs = [
            parse_program("10 001 01"),
            parse_program("10 000 01"),
            parse_program("000"),
        ]
        for seed in (1, 7, 42, 73, 999):
            with self.subTest(seed=seed):
                self.assertEqual(
                    receive(make_stream(programs, jitter=0.20, seed=seed)),
                    programs,
                )

    def test_one_continuous_terminal_silence_not_two_consecutive_twos(self):
        programs = [parse_program("10 01"), parse_program("10 001 01")]
        events = make_stream(programs)
        for i, event in enumerate(events):
            if event["kind"] == "gap" and event["units"] == 21:
                self.assertEqual(events[i - 1]["kind"], "mark")
                if i != len(events) - 1:
                    self.assertEqual(events[i + 1]["kind"], "mark")
        self.assertEqual(receive(events), programs)
        self.assertEqual(sum(x["kind"] == "gap" and x["units"] == 21 for x in events), 2)

    def test_word_width_collision_0_00_vs_000_is_not_lost(self):
        a, b = parse_program("0 00"), parse_program("000")
        self.assertEqual("".join(a), "".join(b))
        self.assertNotEqual(identity_sha256(a), identity_sha256(b))
        self.assertNotEqual(t5_pack(a), t5_pack(b))
        self.assertEqual(receive(make_stream([a, b])), [a, b])

    def test_no_terminal_gap_is_not_a_complete_program(self):
        events = make_stream([parse_program("10 001 01")])
        with self.assertRaisesRegex(ChannelError, "terminal|completed"):
            receive(events[:-1])
        with self.assertRaisesRegex(ChannelError, "terminal|completed"):
            receive(events[:-2])

    def test_bad_gap_durations_fail_without_guessing(self):
        baseline = make_stream([parse_program("10 001 01")])
        for value in (2.0, 4.5, 10.0, 13.0):
            events = copy.deepcopy(baseline)
            next(x for x in events if x["kind"] == "gap")["units"] = value
            with self.subTest(units=value), self.assertRaisesRegex(ChannelError, "ambiguous"):
                receive(events)
        for value in (float("nan"), 0.0, -1.0):
            events = copy.deepcopy(baseline)
            events[0]["units"] = value
            with self.subTest(value=value), self.assertRaises(ChannelError):
                receive(events)

    def test_early_long_pause_changes_framing_not_invisible_success(self):
        original = parse_program("10 001 01")
        events = make_stream([original])
        # Turn first real word boundary into a false program-end gap.
        for x in events:
            if x["kind"] == "gap" and x["units"] == 7:
                x["units"] = 21
                break
        got = receive(events)
        self.assertNotEqual(got, [original])
        self.assertEqual(len(got), 2)
        self.assertEqual(got[0], ["10"])
        self.assertEqual(got[1], ["001", "01"])
        # The receiver must NOT claim oracle/CRC confirmation for either frame.
        self.assertIn("NO_ORACLE", summary(got, events, unit_ms=60)["scope"])

    def test_missing_mark_or_extra_gap_cannot_be_considered_normal(self):
        events = make_stream([parse_program("10 01")])
        with self.assertRaises(ChannelError):
            receive(events[1:])
        inserted = copy.deepcopy(events)
        inserted.insert(2, {"kind": "gap", "units": 7})
        with self.assertRaises(ChannelError):
            receive(inserted)

    def test_mark_outside_short_long_band_is_rejected(self):
        events = make_stream([parse_program("10 01")])
        events[0]["units"] = 2.0
        with self.assertRaisesRegex(ChannelError, "keydown"):
            receive(events)

    def test_d1_to_d9_all_payload_values_file_packing_and_air(self):
        for width in range(1, 10):
            for integer in range(1 << width):
                program = [f"{integer:0{width}b}"]
                data = t5_pack(program)
                self.assertEqual(t5_unpack(data), program)
        sample = ["10", "111", "00", "000", "01"]
        self.assertEqual(t5_unpack(t5_pack(sample)), sample)

    def test_byte_extra_pad_and_out_of_range_are_rejected(self):
        data = t5_pack(parse_program("10 01"))
        self.assertEqual(data, b"\x64")  # raw .sens without EOS=22
        with self.assertRaises(ChannelError):
            t5_unpack(data + b"\xf2")  # 22222 redundant full byte
        with self.assertRaises(ChannelError):
            t5_unpack(b"\xf3")  # > 242 impossible trit-group
        with self.assertRaises(ChannelError):
            t5_unpack(b"")
        with self.assertRaises(ChannelError):
            parse_program("10 0000000000 01")

    def test_file_eof_and_air_eof_are_different_layers(self):
        program = parse_program("10 001 01")
        physical = t5_pack(program)
        self.assertEqual(t5_unpack(physical), program)
        # The file contains no separate terminal symbol 22.
        # The AIR event stream requires measured final SILENCE.
        timeline = make_stream([program])
        self.assertEqual(timeline[-1]["kind"], "gap")
        self.assertEqual(timeline[-1]["units"], 21.0)
        self.assertEqual(receive(timeline), [program])

    def test_single_stream_accepts_four_sequential_programs(self):
        programs = [
            parse_program("000"),
            parse_program("10 01"),
            parse_program("10 001 01"),
            parse_program("10 000 01"),
        ]
        receiver = Receiver()
        for event in make_stream(programs, jitter=0.1, seed=23):
            receiver.feed(event)
        self.assertEqual(receiver.finish(), programs)
        for original, reconstructed in zip(programs, receiver.frames):
            self.assertEqual(identity_sha256(original), identity_sha256(reconstructed))

    def test_invalid_empty_programs_and_jitter_are_rejected(self):
        with self.assertRaises(ChannelError):
            parse_program("")
        with self.assertRaises(ChannelError):
            make_stream([])
        with self.assertRaises(ChannelError):
            make_stream([parse_program("000")], jitter=0.51)


if __name__ == "__main__":
    unittest.main()
