#!/usr/bin/env python3
"""Два незалежні скінченні оракули D10 для префіксного коду й точної суми Крафта.

Описує тільки семантичний закон; НЕ енкодер .sens/.senc чи дозвіл фізичного формату.
"""
from fractions import Fraction
from itertools import product


def validate_words(words):
    if not isinstance(words, (tuple, list)):
        raise ValueError("finite ordered codeword collection required")
    for idx, word in enumerate(words):
        if not isinstance(word, str) or any(bit not in "01" for bit in word):
            raise ValueError("nonbinary word at index " + str(idx))


def pairwise_certificate(words):
    """Оракул A: точні пари рядків і Fraction, канонічна перша колізія."""
    validate_words(words)
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            a, b = words[i], words[j]
            if a.startswith(b) or b.startswith(a):
                prefix = a if len(a) <= len(b) else b
                return ("NOT_PREFIX_FREE", i, j, prefix)
    value = sum((Fraction(1, 1 << len(w)) for w in words), Fraction())
    if value > 1:
        raise RuntimeError("Kraft inequality violated by prefix-free input")
    return ("CERTIFIED", value.numerator, value.denominator)


def interval_certificate(words):
    """Оракул B: неперетинні двійкові циліндри на спільній глибині."""
    validate_words(words)
    level = max(map(len, words), default=0)
    occupied = []
    volume = 0
    for word in words:
        width = 1 << (level - len(word))
        start = (int(word, 2) if word else 0) * width
        end = start + width
        for left, right in occupied:
            if max(left, start) < min(right, end):
                return ("NOT_PREFIX_FREE",)
        occupied.append((start, end))
        volume += width
    value = Fraction(volume, 1 << level)
    return ("CERTIFIED", value.numerator, value.denominator)


def verify():
    # Всі впорядковані набори довжини 0..3 зі слів довжини 0..3.
    alphabet = [""] + ["".join(bits) for length in range(1, 4)
                        for bits in product("01", repeat=length)]
    trials = 0
    for size in range(4):
        for words in product(alphabet, repeat=size):
            a = pairwise_certificate(words)
            b = interval_certificate(words)
            if a[0] != b[0] or (a[0] == "CERTIFIED" and a != b):
                raise RuntimeError("oracle disagreement for " + repr(words))
            trials += 1
    known = [
        (("0", "10", "11"), ("CERTIFIED", 1, 1)),
        (("00", "01"), ("CERTIFIED", 1, 2)),
        (("0", "00"), ("NOT_PREFIX_FREE", 0, 1, "0")),
        (("0", "0"), ("NOT_PREFIX_FREE", 0, 1, "0")),
        (("",), ("CERTIFIED", 1, 1)),
        (("", "0"), ("NOT_PREFIX_FREE", 0, 1, "")),
        ((), ("CERTIFIED", 0, 1)),
        (("0", "01"), ("NOT_PREFIX_FREE", 0, 1, "0")),
    ]
    for words, expected in known:
        if pairwise_certificate(words) != expected:
            raise RuntimeError("witness failed: " + repr(words))
    for invalid in (("0", "2"), ("0", 1), (None,), "010"):
        try:
            pairwise_certificate(invalid)
        except ValueError:
            continue
        raise RuntimeError("invalid input escaped: " + repr(invalid))
    print(f"D10 PREFIX-FREE-KRAFT-CERTIFICATE PASS: {trials} exhaustive oracle pairs, {len(known)} witnesses, 4 rejects")


if __name__ == "__main__":
    verify()
