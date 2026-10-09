"""Independent bounded reference witnesses for D10 hobby-derived PROPOSALS.

These tests do NOT execute donor implementations or prove SENS runtime/physical .sens parity.
"""
import cmath
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/d10-hobbies-source-laws-v1.json"


def julian_day_gregorian(year, month, day, ut_hours):
    # Independent Gregorian integer calendar arithmetic, not donor source code.
    if not (1 <= month <= 12 and 0 <= ut_hours < 24):
        raise ValueError("range")
    days_in_month = [31, 28 + (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)),
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if not 1 <= day <= days_in_month[month - 1]:
        raise ValueError("invalid date")
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn - 0.5 + ut_hours / 24


def gregorian_from_julian_day(jd):
    # Independent civil-from-JDN arithmetic over bounded modern Gregorian dates.
    jdn = math.floor(jd + 0.5)
    fractional_hours = (jd + 0.5 - jdn) * 24
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return (year, month, day, fractional_hours)


def leapfrog_constant_acceleration(x, vhalf, acceleration, dt):
    # One-body witness of synchronous snapshot semantics, not full N-body proof.
    new_x = x + dt * vhalf
    new_vhalf = vhalf + dt * acceleration
    return (new_x, new_vhalf)


def one_sided_spectrum(samples, window):
    if not samples or len(samples) != len(window):
        raise ValueError("bad frame")
    n = len(samples)
    weighted = [a * b for a, b in zip(samples, window)]
    results = []
    for k in range(n // 2 + 1):
        value = sum(weighted[j] * cmath.exp(-2j * math.pi * k * j / n)
                    for j in range(n))
        magnitude = abs(value)
        phase = math.atan2(value.imag, value.real) if magnitude > 1e-10 else 0.0
        results.append((magnitude, phase))
    return results


def coherent_bit(samples, reference, threshold):
    if not samples or len(samples) != len(reference) or not 0 < threshold <= 1:
        raise ValueError("bad samples or threshold")
    dot = sum(s * r for s, r in zip(samples, reference))
    energy = sum(s * s for s in samples) * sum(r * r for r in reference)
    confidence = abs(dot) / math.sqrt(energy) if energy else 0.0
    return (1 if dot >= 0 else 0, confidence) if confidence >= threshold else None


def phase_continuous_tones(bits, rate, symbols_per_second, tone0, tone1, amplitude):
    if (any(bit not in "01" for bit in bits) or rate <= 0 or
        symbols_per_second <= 0 or amplitude <= 0 or amplitude > 1 or
        tone0 <= 0 or tone1 <= 0 or tone0 == tone1 or
        max(tone0, tone1) >= rate / 2):
        raise ValueError("invalid tone configuration")
    samples_per_symbol = rate / symbols_per_second
    if samples_per_symbol != int(samples_per_symbol) or samples_per_symbol < 8:
        raise ValueError("nonintegral/too few samples per symbol")
    phase = 0.0
    output = []
    for bit in bits:
        tone = tone1 if bit == "1" else tone0
        for _ in range(int(samples_per_symbol)):
            output.append(amplitude * math.sin(phase))
            phase = (phase + 2 * math.pi * tone / rate) % (2 * math.pi)
    return output


class D10HobbiesSourceLawReview(unittest.TestCase):
    def test_ledger_stays_research_only(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(ledger["schema"], "d10-hobbies-source-laws/v1")
        self.assertEqual(ledger["baseline"]["selected_delta"], 0)
        self.assertEqual(ledger["baseline"]["new_coordinates"], 0)
        self.assertEqual(ledger["baseline"]["ratified_delta"], 0)
        rows = ledger["candidates"]
        self.assertEqual(len(rows), 9)
        self.assertEqual(len({row["semantic_name"] for row in rows}), 9)
        self.assertEqual(sum(row["decision"] == "PROPOSE-REVIEW" for row in rows), 6)
        self.assertEqual(sum(row["decision"].startswith("HOLD") for row in rows), 3)
        for row in rows:
            self.assertIsNone(row["coordinate"])
            self.assertFalse(row["ratified"])
            self.assertFalse(row["selected_in_canonical_inventory"])
            self.assertEqual(row["unblock_fanout"], "UNKNOWN")
            self.assertEqual(row["expressibility_gap"], "UNPROVEN")
            self.assertGreaterEqual(len(row["positives"]), 2)
            self.assertGreaterEqual(len(row["falsifiers"]), 1)
            self.assertEqual(len(row["source"]["blob_sha"]), 40)
            self.assertLessEqual(row["source"]["start_line"], row["source"]["end_line"])
            self.assertTrue(row["dedup_attack"])
            self.assertTrue(row["mechanism_attack"])

    def test_julian_day_noon_epoch(self):
        self.assertEqual(julian_day_gregorian(2000, 1, 1, 12), 2451545)
        self.assertEqual(julian_day_gregorian(2000, 1, 1, 0), 2451544.5)
        self.assertEqual(julian_day_gregorian(2000, 2, 29, 12), 2451604)
        with self.assertRaises(ValueError):
            julian_day_gregorian(2000, 2, 30, 0)
        with self.assertRaises(ValueError):
            julian_day_gregorian(1900, 2, 29, 0)

    def test_julian_day_inverse_noon_vs_midnight(self):
        self.assertEqual(gregorian_from_julian_day(2451545), (2000, 1, 1, 12))
        self.assertEqual(gregorian_from_julian_day(2451544.5), (2000, 1, 1, 0))
        for month, day, hour in [(1, 1, 0), (2, 29, 12), (12, 31, 18)]:
            self.assertEqual(gregorian_from_julian_day(
                julian_day_gregorian(2000, month, day, hour)),
                (2000, month, day, hour))

    def test_leapfrog_half_velocity_and_zero_step(self):
        self.assertEqual(leapfrog_constant_acceleration(0, 1, 2, 2), (2, 5))
        self.assertEqual(leapfrog_constant_acceleration(4, -2, 9, 0), (4, -2))
        self.assertNotEqual(leapfrog_constant_acceleration(0, 1, 2, 2)[0], 6)

    def test_one_sided_spectrum_and_invalid_window(self):
        first = one_sided_spectrum([1, 0, 0, 0], [1] * 4)
        self.assertEqual(len(first), 3)
        for mag, phase in first:
            self.assertAlmostEqual(mag, 1)
            self.assertAlmostEqual(phase, 0)
        dc = one_sided_spectrum([1, 1, 1, 1], [1] * 4)
        self.assertAlmostEqual(dc[0][0], 4)
        self.assertAlmostEqual(dc[1][0], 0)
        self.assertAlmostEqual(dc[2][0], 0)
        with self.assertRaises(ValueError):
            one_sided_spectrum([1, 0, 0], [1, 1])

    def test_coherent_polarity_and_ambiguity(self):
        self.assertEqual(coherent_bit([1, 1], [1, 1], 0.5), (1, 1))
        self.assertEqual(coherent_bit([-1, -1], [1, 1], 0.5), (0, 1))
        self.assertIsNone(coherent_bit([0, 0], [1, 1], 0.5))
        with self.assertRaises(ValueError):
            coherent_bit([1], [1, 1], 0.5)

    def test_tone_boundary_does_not_reset_phase(self):
        samples = phase_continuous_tones("01", 16, 2, 1.5, 2.5, 1)
        self.assertEqual(len(samples), 16)
        self.assertAlmostEqual(samples[8], -1)
        self.assertEqual(phase_continuous_tones("", 16, 2, 1.5, 2.5, 1), [])
        with self.assertRaises(ValueError):
            phase_continuous_tones("01", 16, 2, 8, 2.5, 1)
        with self.assertRaises(ValueError):
            phase_continuous_tones("0x1", 16, 2, 1.5, 2.5, 1)


if __name__ == "__main__":
    unittest.main()
