"""Focused regression for the machine capability axis' full Ukrainian call-head projection.

The test is mechanical, not a second SENS evaluator. The inverse witness must
reconstruct the exact pre-migration Git blob byte-for-byte; this pins all
quoted capability data, metadata values, function bodies and numeric keys.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/capability-axis.lisp"
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"
ORIGINAL_GIT_BLOB = "d4c82f26368cec3107921444ada137145a36d079"

HEADS = {
    "0011": "визначити",
    "0010": "функція",
    "001": "як-є",
    "110": "за-умовою",
    "010": "атом?",
    "101": "тотожне?",
    "100": "перше",
    "011": "решта",
}
RESTORE = {surface: bits for bits, surface in HEADS.items()}
HEAD_PATTERN = re.compile(
    r"[(](" + "|".join(re.escape(surface) for surface in HEADS.values()) + r")(?=\s)"
)
RAW_PATTERN = re.compile(
    r"[(](" + "|".join(HEADS.keys()) + r")(?=\s)"
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def restore_operator_heads(source: str) -> str:
    return HEAD_PATTERN.sub(lambda match: "(" + RESTORE[match.group(1)], source)


def assert_exact_projection(testcase, table_path, bits, surface, english, lisp):
    table = table_path.read_text(encoding="utf-8")
    rows = [
        line for line in table.splitlines()
        if re.match(rf"^\s*[(]{re.escape(bits)}\s", line)
    ]
    testcase.assertEqual(len(rows), 1, f"{bits}: expected one exact-width row")
    testcase.assertIn(f"(укр {surface})", rows[0])
    testcase.assertIn(f"(en {english})", rows[0])
    testcase.assertIn(f"(LISP {lisp})", rows[0])


class CapabilityAxisUkrProjectionTests(unittest.TestCase):
    def test_full_ukr_operator_heads_match_ratified_domain_rows(self):
        for bits, surface, english, lisp in (
            ("001", "як-є", "quote", "QUOTE"),
            ("010", "атом?", "atom?", "ATOM"),
            ("011", "решта", "cdr", "CDR"),
            ("100", "перше", "car", "CAR"),
            ("101", "тотожне?", "eq?", "EQ"),
            ("110", "за-умовою", "cond", "COND"),
        ):
            assert_exact_projection(self, D3, bits, surface, english, lisp)
        for bits, surface, english, lisp in (
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0011", "визначити", "define", "DEFINE"),
        ):
            assert_exact_projection(self, D4, bits, surface, english, lisp)

    def test_no_encoded_operator_heads_and_exact_expected_counts(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIsNone(RAW_PATTERN.search(source),
                          "no raw D1-D4 operation heads in this source")
        for surface, count in (
            ("визначити", 7), ("функція", 4), ("як-є", 4), ("за-умовою", 5),
            ("атом?", 4), ("тотожне?", 3), ("перше", 10), ("решта", 7),
        ):
            pattern = re.compile(r"[(]" + re.escape(surface) + r"(?=\s)")
            self.assertEqual(len(pattern.findall(source)), count, surface)

    def test_inverse_witness_preserves_all_non_operator_bytes(self):
        source = SOURCE.read_text(encoding="utf-8")
        restored = restore_operator_heads(source).encode("utf-8")
        self.assertEqual(
            git_blob_sha(restored), ORIGINAL_GIT_BLOB,
            "inverse substitution must reconstruct the exact original Git blob",
        )

    def test_wrong_peer_surface_fails_the_inverse_witness(self):
        source = SOURCE.read_text(encoding="utf-8")
        mutated = source.replace("(тотожне? width", "(хибне? width", 1)
        self.assertNotEqual(mutated, source)
        self.assertNotEqual(
            git_blob_sha(restore_operator_heads(mutated).encode("utf-8")),
            ORIGINAL_GIT_BLOB,
            "a wrong peer surface must not satisfy the exact-source witness",
        )


if __name__ == "__main__":
    unittest.main()
