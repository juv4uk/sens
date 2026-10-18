"""Source-only exact Ukrainian projection regression for semantic-authority-guard.lisp."""
from __future__ import annotations

import hashlib
import re
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = "scripts/semantic-authority-guard.lisp"
OLD_BLOB_SHA = "d3006a7442065f3e6a1cb5b2ebf9c4e68a336de3"
PROJECTED_BLOB_SHA = "45f54c7cea67c426af94cc9a096c327ecc3abbaf"
LATEST_BLOB_SHA = "f9787223dde7b63439445af951d0fd008059161d"

# Exact current full-surface values from the ratified D3/D4 tables.
PROJECTIONS = {
    "100": "перше",
    "101": "тотожне?",
    "110": "за-умовою",
    "1001": "друге",
    "001": "як-є",
    "010": "атом?",
    "011": "решта",
    "0010": "функція",
    "0011": "визначити",
    "0100": "хибне?"
}
EXPECTED_COUNTS = {
    "101": 1,
    "110": 7,
    "1001": 1,
    "0011": 8,
    "0010": 7,
    "010": 2,
    "011": 1,
    "001": 10,
    "0100": 2
}
MIGRATED_HEADS_BY_LINE = {
    11: ("0011",),
    14: ("0011",),
    15: ("0010",),
    16: ("110",),
    20: ("0011",),
    21: ("0010",),
    22: ("110",),
    23: ("010",),
    25: ("011",),
    27: ("0011",),
    28: ("0010",),
    39: ("0011",),
    40: ("0010",),
    43: ("001",),
    53: ("0011",),
    54: ("0010",),
    57: ("001",),
    65: ("0011",),
    66: ("0010",),
    67: ("110",),
    70: ("0100",),
    71: ("001",),
    78: ("001",),
    79: ("001",),
    81: ("0011",),
    82: ("0010",),
    83: ("110",),
    84: ("010", "001"),
    87: ("1001",),
    88: ("110",),
    90: ("0100",),
    94: ("110",),
    97: ("001",),
    99: ("001",),
    103: ("110",),
    104: ("101", "001"),
    106: ("001",),
}
NEXT_BATCH_BY_LINE = {
    86: ("001001", "100"),
    93: ("001000",),
    102: ("001000",),
}
NEXT_PROJECTIONS = {
    "001001": "нехай-послідовно",
    "100": "перше",
    "001000": "нехай",
}
INVERSE = {surface: bits for bits, surface in PROJECTIONS.items()}


def git_blob_sha(source: str) -> str:
    data = source.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def mask_lisp_code(source: str) -> str:
    """Hide strings and semicolon comments while preserving offsets/newlines."""
    chars = list(source)
    in_string = escaped = in_comment = False
    for index, char in enumerate(source):
        if in_comment:
            if char == "\n":
                in_comment = False
            else:
                chars[index] = " "
            continue
        if in_string:
            if char != "\n":
                chars[index] = " "
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = False
            continue
        if char == ";":
            chars[index] = " "
            in_comment = True
        elif char == '"':
            chars[index] = " "
            in_string = True
            escaped = False
    return "".join(chars)


def numeric_heads(source: str) -> list[tuple[str, int, int, int]]:
    masked = mask_lisp_code(source)
    found = []
    for match in re.finditer(r"\(([01]{3,11})(?=\s)", masked):
        line = source.count("\n", 0, match.start()) + 1
        found.append((match.group(1), match.start() + 1,
                      match.start() + 1 + len(match.group(1)), line))
    return found


def named_heads(source: str, names: set[str]) -> list[tuple[str, int, int, int]]:
    masked = mask_lisp_code(source)
    found = []
    for index, char in enumerate(masked):
        if char != "(":
            continue
        start = index + 1
        while start < len(masked) and masked[start] in " \t\r\n":
            start += 1
        end = start
        while end < len(masked) and masked[end] not in " \t\r\n();\"":
            end += 1
        token = masked[start:end]
        if token in names and end > start and (
            end == len(masked) or masked[end] in " \t\r\n"
        ):
            line = source.count("\n", 0, index) + 1
            found.append((token, start, end, line))
    return found


def eligible_numeric_heads(source: str) -> list[tuple[str, int, int, int]]:
    heads = numeric_heads(source)
    by_line: dict[int, list[tuple[str, int, int, int]]] = defaultdict(list)
    for head in heads:
        by_line[head[3]].append(head)
    return [
        head for head in heads
        if all(item[0] in PROJECTIONS for item in by_line[head[3]])
    ]


def project_exact_heads(source: str) -> str:
    result = source
    for bits, start, end, _line in sorted(
        eligible_numeric_heads(source), key=lambda item: item[1], reverse=True
    ):
        result = result[:start] + PROJECTIONS[bits] + result[end:]
    return result


def inverse_projected_heads(source: str) -> str:
    found = named_heads(source, set(INVERSE))
    operations = []
    for line, bits in MIGRATED_HEADS_BY_LINE.items():
        actual = [head for head in found if head[3] == line]
        expected = [PROJECTIONS[bit] for bit in bits]
        if [head[0] for head in actual] != list(expected):
            raise AssertionError(
                f"line {line}: expected projected heads {expected}, "
                f"found {[head[0] for head in actual]}"
            )
        operations.extend(
            (head[1], head[2], bit)
            for head, bit in zip(actual, bits, strict=True)
        )
    result = source
    for start, end, bits in sorted(operations, key=lambda item: item[0], reverse=True):
        result = result[:start] + bits + result[end:]
    return result


def rollback_next_exact_batch(source: str) -> str:
    """Undo only the later, domain-ratified D3/D6 heads before the older inverse."""
    lines = source.splitlines(keepends=True)
    names = set(NEXT_PROJECTIONS.values())
    for line, bits in NEXT_BATCH_BY_LINE.items():
        index = line - 1
        if index >= len(lines):
            raise AssertionError(f"lost migrated line {line}")
        found = named_heads(lines[index], names)
        expected = [NEXT_PROJECTIONS[bit] for bit in bits]
        if [head[0] for head in found] != expected:
            raise AssertionError(f"line {line}: expected {expected}, found {[head[0] for head in found]}")
        current = lines[index]
        for _name, start, end, _local_line in reversed(found):
            bit = next((b for b in bits if NEXT_PROJECTIONS[b] == _name), None)
            if bit is None:
                raise AssertionError("unratified peer")
            current = current[:start] + bit + current[end:]
        lines[index] = current
    original = "".join(lines)
    if git_blob_sha(original) != PROJECTED_BLOB_SHA:
        raise AssertionError("lost exact pre-batch Git blob")
    return original


class UkrainianSemanticAuthorityGuardProjection(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")

    def test_exact_ratified_projection_and_width(self):
        for bits, surface in PROJECTIONS.items():
            domain = ROOT / f"lib/domains/d{len(bits)}.lisp"
            rows = [
                line for line in domain.read_text(encoding="utf-8").splitlines()
                if re.match(r"\s*\(" + re.escape(bits) + r"\s", line)
            ]
            with self.subTest(bits=bits):
                self.assertEqual(len(bits), 3 if len(bits) == 3 else 4)
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(укр {surface})", rows[0])

    def test_exact_inverse_restores_original_blob(self):
        self.assertEqual(git_blob_sha(self.source), LATEST_BLOB_SHA)
        previous = rollback_next_exact_batch(self.source)
        restored = inverse_projected_heads(previous)
        self.assertEqual(git_blob_sha(restored), OLD_BLOB_SHA)
        self.assertEqual(len(restored.splitlines()), len(self.source.splitlines()))
        self.assertEqual(project_exact_heads(restored), previous)

    def test_exact_head_counts_and_idempotence(self):
        self.assertEqual(
            Counter(bits for heads in MIGRATED_HEADS_BY_LINE.values() for bits in heads),
            Counter(EXPECTED_COUNTS),
        )
        self.assertEqual(sum(map(len, MIGRATED_HEADS_BY_LINE.values())), 39)
        self.assertEqual(len(MIGRATED_HEADS_BY_LINE), 37)
        self.assertEqual(project_exact_heads(self.source), self.source)
        observed_residuals = defaultdict(list)
        for bits, _start, _end, line in numeric_heads(self.source):
            observed_residuals[line].append(bits)
        self.assertEqual(observed_residuals, {})
        previous = rollback_next_exact_batch(self.source)
        self.assertEqual(
            {line: tuple(bits) for line, bits in (
                (line, [item[0] for item in numeric_heads(previous) if item[3] == line])
                for line in NEXT_BATCH_BY_LINE
            )},
            NEXT_BATCH_BY_LINE,
        )

    def test_later_exact_d3_d6_heads_fail_closed_for_wrong_peer(self):
        lines = self.source.splitlines()
        self.assertIn("(нехай-послідовно ((row (перше rows))", lines[85])
        self.assertIn("(нехай ((raw-source", lines[92])
        self.assertIn("(нехай ((class", lines[101])
        self.assertEqual(numeric_heads(self.source), [])
        wrong = self.source.replace("(нехай ((raw-source", "(функція ((raw-source", 1)
        self.assertNotEqual(wrong, self.source)
        with self.assertRaises(AssertionError):
            rollback_next_exact_batch(wrong)


if __name__ == "__main__":
    unittest.main(verbosity=2)
