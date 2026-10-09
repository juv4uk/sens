"""Independent mathematical reference witnesses for D10 hardware-root triage.

Not SENS execution, not D10 residency, and not concurrent hardware verification.
"""
import unittest
from fractions import Fraction


def _unsigned(width, *values):
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError('width must be a positive integer')
    ceiling = (1 << width) - 1
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= ceiling for v in values):
        raise ValueError('unsigned operand out of range')
    return ceiling


def saturating_add(width, left, right):
    ceiling = _unsigned(width, left, right)
    return min(ceiling, left + right)


def saturating_sub(width, left, right):
    _unsigned(width, left, right)
    return max(0, left - right)


def gf2_remainder(dividend, divisor):
    if not isinstance(dividend, int) or dividend < 0 or not isinstance(divisor, int) or divisor <= 0:
        raise ValueError('polynomial arguments must be nonnegative, divisor nonzero')
    remainder = dividend
    while remainder and remainder.bit_length() >= divisor.bit_length():
        remainder ^= divisor << (remainder.bit_length() - divisor.bit_length())
    return remainder


def linear_convolution(left, right):
    if not left or not right:
        return []
    result = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return result


def encode_exact_words(width, words):
    _unsigned(width)
    bits = []
    for word in words:
        _unsigned(width, word)
        bits.append(format(word, f'0{width}b'))
    return ''.join(bits)


def decode_exact_words(width, bits):
    _unsigned(width)
    if not isinstance(bits, str) or any(b not in '01' for b in bits) or len(bits) % width:
        raise ValueError('noncanonical wordstream')
    return [int(bits[i:i+width], 2) for i in range(0, len(bits), width)]


def compare_exchange_spec(value, expected, replacement):
    """Sequential abstract state transition only; NOT a CAS implementation."""
    success = value == expected
    return value, success, replacement if success else value


def quantize_nearest_even(value, step):
    value = Fraction(value)
    step = Fraction(step)
    if step <= 0:
        raise ValueError('step must be positive')
    ratio = value / step
    low = ratio.numerator // ratio.denominator
    fraction = ratio - low
    if fraction > Fraction(1, 2):
        return low + 1
    if fraction < Fraction(1, 2):
        return low
    return low if low % 2 == 0 else low + 1


class HardwareReferenceWitness(unittest.TestCase):
    def test_saturating_add_vectors(self):
        self.assertEqual(saturating_add(3, 6, 1), 7)
        self.assertEqual(saturating_add(3, 2, 3), 5)
        self.assertNotEqual(saturating_add(3, 7, 1), 0)

    def test_saturating_sub_vectors(self):
        self.assertEqual(saturating_sub(3, 4, 2), 2)
        self.assertEqual(saturating_sub(3, 0, 1), 0)
        self.assertNotEqual(saturating_sub(3, 0, 1), 7)

    def test_unsigned_invalid(self):
        for op in (saturating_add, saturating_sub):
            with self.assertRaises(ValueError):
                op(3, -1, 1)
            with self.assertRaises(ValueError):
                op(3, 8, 0)
            with self.assertRaises(ValueError):
                op(0, 0, 0)

    def test_gf2_vectors(self):
        self.assertEqual(gf2_remainder(0b1011, 0b11), 1)
        self.assertEqual(gf2_remainder(0b110, 0b11), 0)
        self.assertNotEqual(gf2_remainder(0b1011, 0b11), 11 % 3)

    def test_gf2_falsifier(self):
        with self.assertRaises(ValueError):
            gf2_remainder(11, 0)
        for dividend in range(32):
            for divisor in range(1, 16):
                rem = gf2_remainder(dividend, divisor)
                self.assertLess(rem.bit_length(), divisor.bit_length())

    def test_convolution_vectors(self):
        self.assertEqual(linear_convolution([1, 2], [3, 4]), [3, 10, 8])
        self.assertEqual(linear_convolution([1], [0, 2]), [0, 2])
        self.assertEqual(linear_convolution([], [1]), [])
        self.assertNotEqual(linear_convolution([1, 2], [3, 4]), [11, 10])

    def test_exact_words_vectors(self):
        self.assertEqual(encode_exact_words(3, [5, 1]), '101001')
        self.assertEqual(decode_exact_words(3, '101001'), [5, 1])
        bits = encode_exact_words(10, [1, 1023])
        self.assertEqual(len(bits), 20)
        self.assertEqual(decode_exact_words(10, bits), [1, 1023])
        self.assertEqual(len(encode_exact_words(10, [1])), 10)

    def test_exact_words_reject_truncation(self):
        with self.assertRaises(ValueError):
            decode_exact_words(10, '0000000001000000')
        with self.assertRaises(ValueError):
            encode_exact_words(10, [1024])
        with self.assertRaises(ValueError):
            decode_exact_words(3, '1002')

    def test_cas_sequential_model(self):
        old, ok, state = compare_exchange_spec(5, 5, 7)
        self.assertEqual((old, ok, state), (5, True, 7))
        self.assertEqual(compare_exchange_spec(state, 5, 9), (7, False, 7))

    def test_cas_two_contenders_cannot_both_win_in_either_serial_order(self):
        for first, second in ((6, 7), (7, 6)):
            _, ok1, state = compare_exchange_spec(5, 5, first)
            _, ok2, state = compare_exchange_spec(state, 5, second)
            self.assertTrue(ok1)
            self.assertFalse(ok2)
            self.assertEqual(state, first)

    def test_quantize_nearest_even(self):
        self.assertEqual(quantize_nearest_even(Fraction(5, 2), 1), 2)
        self.assertEqual(quantize_nearest_even(Fraction(7, 2), 1), 4)
        self.assertEqual(quantize_nearest_even(Fraction(-5, 2), 1), -2)
        self.assertNotEqual(quantize_nearest_even(Fraction(5, 2), 1), 3)
        self.assertEqual(quantize_nearest_even(Fraction(3, 4), Fraction(1, 2)), 2)
        with self.assertRaises(ValueError):
            quantize_nearest_even(1, 0)


if __name__ == '__main__':
    unittest.main()
