"""Перші п'ять функцій та три wire-функції x86: чинні D3/D4/D8/D9 проєкції, не семантичний оракул.

Відновлюємо оригінальний Git blob після виключно операторних замін.
Цей тест НЕ стверджує виконання x86/SENS і не тлумачить десяткові ISA-поля.
"""
from __future__ import annotations

import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import read_domain_table

ENCODER = ROOT / "lib" / "machine" / "encoding" / "x86-64.lisp"
BOUNDARY = "; ModR/M is a finite"
ORIGINAL_GIT_BLOB = "4c4768cc4730c8529b23238967e51e0b209c4cdd"

# Наступні три функції: SENS-коди D3/D4/D8/D9, не ISA-операнди.
WIRE_START = "(визначити x86-wire-split-integer"
WIRE_END = "; Exact finite 8-bit decode."
WIRE_PRIOR_GIT_BLOB = "9a247f42fb0b411ea239f659359195552156e8f3"
WIRE_EXPECTED = (
    (3, "100", "перше", 2),
    (3, "110", "за-умовою", 7),
    (3, "111", "сполучити", 3),
    (8, "11110100", "значення-у-текст", 1),
    (9, "110011100", "рядок-порожній?", 2),
    (9, "110011101", "рядок-решта", 8),
    (9, "110101010", "рядок-префікс?", 5),
    (4, "0011", "визначити", 3),
    (4, "0010", "функція", 5),
    (3, "001", "як-є", 8),
    (3, "010", "атом?", 8),
    (3, "011", "решта", 2),
    (4, "0100", "хибне?", 1),
    (4, "0101", "порожній?", 1),
)

# Рівно п'ять функцій: register, XMM register, low3, high1, REX.
# Ці координати — джерельні доменні ідентичності, не байти x86.
EXPECTED = (
    (4, "0011", "визначити", 5),
    (4, "0010", "функція", 5),
    (3, "110", "за-умовою", 19),
    (3, "101", "тотожне?", 110),
    (3, "001", "як-є", 86),
    (3, "010", "атом?", 19),
)


def git_blob(source: str) -> str:
    raw = source.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + bytes((0,)) + raw
    ).hexdigest()


def rollback_wire_three(source: str) -> str:
    """Обернути тільки 56 чинних D3/D4/D8/D9 callheads трьох wire-функцій."""
    assert source.count(WIRE_START) == 1, "втрачено початок трьох wire-функцій"
    assert source.count(WIRE_END) == 1, "втрачено кінець wire-ділянки"
    left, tail = source.split(WIRE_START, 1)
    mid, right = tail.split(WIRE_END, 1)
    mid = WIRE_START + mid
    for width, bits, peer, expected_count in WIRE_EXPECTED:
        current = {row.bits: row.ukr for row in read_domain_table(
            ROOT / "lib" / "domains" / f"d{width}.lisp"
        )}
        assert current[bits] == peer, f"D{width}:{bits}: нечинна укр-проєкція"
        pattern = re.compile(r"\(" + re.escape(peer) + r"(?=\s|\))")
        actual_count = len(pattern.findall(mid))
        assert actual_count == expected_count, (
            f"D{width}:{bits}: expected {expected_count}, got {actual_count}"
        )
        mid = pattern.sub("(" + bits, mid)
    return left + mid + WIRE_END + right


def rollback_only_current_heads(source: str) -> str:
    source = rollback_wire_three(source)
    assert source.count(BOUNDARY) == 1, "Порушено межу п'ятої функції"
    prefix, suffix = source.split(BOUNDARY, 1)
    for width, bits, surface, expected_count in EXPECTED:
        rows = {row.bits: row.ukr for row in read_domain_table(
            ROOT / "lib" / "domains" / f"d{width}.lisp"
        )}
        assert rows[bits] == surface, f"D{width}:{bits}: змінився чинний укр peer"
        pattern = re.compile(r"\(" + re.escape(surface) + r"(?=\s|\))")
        matches = pattern.findall(prefix)
        assert len(matches) == expected_count, (
            f"D{width}:{bits}: очікувано {expected_count}, отримано {len(matches)}"
        )
        prefix = pattern.sub("(" + bits, prefix)
    # Жодних сирих голів лишатися не повинно в цій обраній ділянці.
    return prefix + BOUNDARY + suffix


class UkrX86EncoderFirstFiveTests(unittest.TestCase):
    def test_exact_current_peers_restore_full_original_git_blob(self):
        current = ENCODER.read_text(encoding="utf-8")
        self.assertEqual(git_blob(rollback_only_current_heads(current)),
                         ORIGINAL_GIT_BLOB)

    def test_three_wire_functions_restore_exact_previous_git_blob(self):
        current = ENCODER.read_text(encoding="utf-8")
        self.assertEqual(git_blob(rollback_wire_three(current)), WIRE_PRIOR_GIT_BLOB)

    def test_three_wire_functions_wrong_peer_rejected(self):
        current = ENCODER.read_text(encoding="utf-8")
        self.assertIn("(рядок-порожній? text)", current)
        mutant = current.replace(
            "(рядок-порожній? text)", "(рядок-префікс? text)", 1
        )
        with self.assertRaises(AssertionError):
            rollback_wire_three(mutant)

    def test_no_old_binary_heads_in_five_migrated_functions(self):
        prefix = ENCODER.read_text(encoding="utf-8").split(BOUNDARY, 1)[0]
        self.assertNotRegex(prefix, r"\((?:0011|0010|110|101|001|010)(?=\s|\))")
        # Ці літерали — незмінні існуючі машинні операнди, не доменні ключі.
        self.assertIn("#d10", prefix)
        self.assertIn("#d11", prefix)

    def test_wrong_ukr_peer_cannot_pass_inverse_check(self):
        current = ENCODER.read_text(encoding="utf-8")
        self.assertIn("(тотожне? register (як-є rax))", current)
        mutant = current.replace(
            "(тотожне? register (як-є rax))",
            "(атом? register (як-є rax))",
            1,
        )
        with self.assertRaises(AssertionError):
            rollback_only_current_heads(mutant)


if __name__ == "__main__":
    unittest.main()
