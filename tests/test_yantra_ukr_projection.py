"""Поточні українські D3/D4 проєкції Yantra; structural oracle, не host SENS semantics."""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/yantra.lisp"
BEFORE = "09ab1eec0fa025a746f97f2181383fd71954c439"
PROJECTION = {
    "0011": "визначити", "0010": "функція",
    "001": "як-є", "100": "перше", "011": "решта",
}
COUNTS = {"0011": 61, "0010": 57, "001": 12, "100": 3, "011": 3}


def restore(source: str) -> str:
    inverse = {name: bits for bits, name in PROJECTION.items()}
    return re.sub(
        r"\((визначити|функція|як-є|перше|решта)(?=\s|\)|$)",
        lambda match: "(" + inverse[match.group(1)], source,
    )


def verify(source: str):
    original = restore(source).encode("utf-8")
    blob = hashlib.sha1(b"blob " + str(len(original)).encode("ascii")
                        + b"\0" + original).hexdigest()
    if blob != BEFORE:
        raise AssertionError("Yantra: змінено точний закон, цитату чи аргумент")
    for bits, name in PROJECTION.items():
        table = (ROOT / f"lib/domains/d{len(bits)}.lisp").read_text(encoding="utf-8")
        m = re.search(r"(?m)^  \(" + bits +
                      r" \(ук [^()]+\) \(укр ([^()]+)\)", table)
        if m is None or m.group(1) != name:
            raise AssertionError(f"D{len(bits)}:{bits} drift нормативної укр")
        actual = len(re.findall(r"\(" + re.escape(name) + r"(?=\s|\)|$)", source))
        if actual != COUNTS[bits]:
            raise AssertionError(f"D{len(bits)}:{bits} кількість {actual} != {COUNTS[bits]}")
    if len(re.findall(r"\(0010(?=\s|\)|$)", source)) != 2:
        raise AssertionError("Дві непереведені змішані D6/D9 голови слід зберегти")


class YantraUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_exact_source_identity_and_ratified_peers(self):
        verify(self.source)

    def test_changed_lines_have_no_numeric_opcodes_or_wire_literals(self):
        before = restore(self.source).splitlines()
        after = self.source.splitlines()
        self.assertEqual(len(before), len(after))
        changed = [(old, new) for old, new in zip(before, after) if old != new]
        self.assertEqual(len(changed), 103)
        for _old, new in changed:
            code = new.split(";", 1)[0]
            self.assertNotRegex(code, r"\(\s*[+-]?\d+(?:[.,]\d+)?(?=\s|\)|$)")
            self.assertNotRegex(code, r"#(?:d\d+:[01]+|b[01]+|q2:[01]+)")

    def test_negative_wrong_peer_and_modified_quoted_data(self):
        with self.assertRaisesRegex(AssertionError, "точний закон"):
            verify(self.source.replace("(функція ", "(визначити ", 1))
        with self.assertRaisesRegex(AssertionError, "точний закон"):
            verify(self.source.replace("(як-є ", "(як-є змінено-", 1))

    def test_other_domain_context_not_guessed_by_width(self):
        self.assertIn("(0010 (s) (110011110", self.source)
        self.assertIn("(0010 (m) (101000", self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
