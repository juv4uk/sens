"""Regression: exact Ukrainian D3/D4 call-head projection in Jev-like experiment.

No domain-table write and no runtime F1-F4 admission claim. This is a static
S-expression/byte-inverse check; original Git blob must survive all substitutions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = "experiments/probabilistic-decision-jev-like.lisp"
ORIGINAL_BLOB = "24b90a16fbbb8c486b29e56fb63749d5144c70df"
PEERS = {
    "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
    "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
    "0010": "функція", "0011": "визначити", "1001": "друге",
    "1110": "список",
}
EXPECTED = {
    "001": 57, "011": 8, "110": 28, "111": 1,
    "0010": 22, "0011": 22, "1001": 1, "1110": 29,
}

spec = importlib.util.spec_from_file_location(
    "check_ukr_callsite_migration",
    ROOT / "scripts" / "check_ukr_callsite_migration.py",
)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


def sha(text: str) -> str:
    value = text.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(value)).encode("ascii") + b"\0" + value
    ).hexdigest()


def verify(source: str):
    inverse = {v: k for k, v in PEERS.items()}
    tokens = [
        h for h in audit.candidate_heads(audit.parse(source))
        if h.text in inverse
    ]
    counts = Counter(inverse[h.text] for h in tokens)
    assert dict(counts) == EXPECTED, (
        "expected exact Ukrainian D3/D4 head census", dict(counts), EXPECTED
    )
    offset = [0]
    offset.extend(m.end() for m in re.finditer("\n", source))
    patches = [
        (offset[t.line - 1] + t.column - 1, t.text, inverse[t.text])
        for t in tokens
    ]
    restored = source
    for pos, ukr, bits in sorted(patches, reverse=True):
        assert restored[pos:pos + len(ukr)] == ukr
        restored = restored[:pos] + bits + restored[pos + len(ukr):]
    assert sha(restored) == ORIGINAL_BLOB, (
        "byte-exact inverse failed", sha(restored), ORIGINAL_BLOB
    )
    assert len(audit.parse(restored)) == len(audit.parse(source))
    before, after = restored.splitlines(), source.splitlines()
    assert len(before) == len(after)
    changed = [i for i, (left, right) in enumerate(zip(before, after))
               if left != right]
    assert len(changed) == 150, (len(changed), "unexpected line delta")
    for i in changed:
        # The strict source-literal guard scans newly added lines.
        # No encoded D1+ head or quoted numerical carrier may be exposed there.
        assert not re.search(r"\([01]{1,11}(?=\s|\))", after[i]), (
            i + 1, after[i]
        )
    return tokens


class UkrProbabilisticProjectionTests(unittest.TestCase):
    def test_ratified_full_ukr_names_have_the_same_exact_domain_identity(self):
        for bits, name in PEERS.items():
            doc = (ROOT / "lib" / "domains" /
                   f"d{len(bits)}.lisp").read_text(encoding="utf-8")
            rows = [line for line in doc.splitlines()
                    if line.strip().startswith(f"({bits} (ук ")]
            self.assertEqual(len(rows), 1)
            self.assertIn(f"(укр {name})", rows[0])

    def test_exact_source_inverse_and_no_encoded_head_on_added_lines(self):
        source = (ROOT / PATH).read_text(encoding="utf-8")
        found = verify(source)
        self.assertEqual(len(found), 168)

    def test_wrong_peer_head_mutation_is_detected(self):
        source = (ROOT / PATH).read_text(encoding="utf-8")
        token = next(h for h in audit.candidate_heads(audit.parse(source))
                     if h.text == "визначити")
        parts = source.splitlines(keepends=True)
        line = parts[token.line - 1]
        idx = token.column - 1
        self.assertEqual(line[idx:idx + len(token.text)], token.text)
        parts[token.line - 1] = (
            line[:idx] + "функція" + line[idx + len(token.text):]
        )
        with self.assertRaises(AssertionError):
            verify("".join(parts))

    def test_quote_safety_is_proved_by_original_blob_not_only_counts(self):
        source = (ROOT / PATH).read_text(encoding="utf-8")
        self.assertTrue(verify(source))
        # There is no automatic assumption that compact ук equals full укр.
        self.assertEqual(len(set(PEERS.values())), len(PEERS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
