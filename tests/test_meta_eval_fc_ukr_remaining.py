"""Точна українська міграція першокласового метаобчислювача.

Старий Git blob — лише незалежний контроль зворотності правок; не
джерело семантичної identity. Чинні resident-и — lib/domains/dN.lisp.
T5M не надає функції права виклику, Python не імітує виконання SENS.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/meta-eval-first-class.lisp"
OLD_BLOB = "ea9c7a89b02777058b9f2704bd96cead69a7608c"
# offset у Python Unicode codepoints, exact-width identity та чинна укр проєкція.
EDIT_RECEIPT = [[3013,"101","тотожне?"],[3026,"001","як-є"],[3036,"11010","менше?"],[3044,"100","перше"],[3057,"1001","друге"],[3082,"101","тотожне?"],[3095,"001","як-є"],[3105,"11110111","однакові?"],[3116,"100","перше"],[3129,"1001","друге"],[3154,"101","тотожне?"],[3167,"001","як-є"],[3177,"11011","більше?"],[3186,"100","перше"],[3199,"1001","друге"],[3697,"101","тотожне?"],[3712,"001","як-є"],[3722,"01010","додати"],[3730,"100","перше"],[3743,"1001","друге"],[3765,"101","тотожне?"],[3780,"001","як-є"],[3790,"01011","відняти"],[3799,"100","перше"],[3812,"1001","друге"],[3834,"101","тотожне?"],[3849,"001","як-є"],[3859,"10110","помножити"],[3870,"100","перше"],[3883,"1001","друге"],[4356,"10011","третє"]]


ALPHA_TO_HISTORY = {
    "назва": "name",
    "оточення": "ctx",
    "значення": "value",
    "параметри": "params",
    "аргументи": "args",
    "вирази": "exprs",
    "тіло": "body",
    "умови": "clauses",
    "оператор": "op",
    "виклична-функція": "fn",
    "вираз": "expr",
}


def undo_alpha(text: str) -> str:
    """Інверсія тільки лексичних імен; цитати та рядки не змінюються."""
    token = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();"]+|\s+|.')
    return token.sub(lambda match: ALPHA_TO_HISTORY.get(match.group(), match.group()), text)


def reconstruct(text: str) -> str:
    text = undo_alpha(text)
    for offset, bits, peer in reversed(EDIT_RECEIPT):
        new = "(" + peer
        if text[offset:offset + len(new)] != new:
            raise AssertionError(f"неправильна/зсунута поверхня при offset={offset}: {bits} → {peer}")
        text = text[:offset] + "(" + bits + text[offset + len(new):]
    return text


def git_blob_sha(source: str) -> str:
    encoded = source.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(encoded)).encode() + b"\0" + encoded).hexdigest()


class MetaFirstClassUkrRemaining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = SOURCE.read_text(encoding="utf-8")

    def test_current_authority_matches_exact_rung_not_old_sid(self):
        self.assertEqual(len(EDIT_RECEIPT), 31)
        for _offset, bits, peer in EDIT_RECEIPT:
            width = len(bits)
            self.assertIn(width, (3, 4, 5, 8))
            table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            match = re.search(r"(?m)^\s*\(" + re.escape(bits) +
                              r"\s+\(ук .*?\(укр ([^()]*)\)", table)
            self.assertIsNotNone(match, f"немає ratified D{width}:{bits}")
            self.assertEqual(match.group(1), peer)

    def test_exact_inverse_recovers_historical_git_blob(self):
        previous = reconstruct(self.current)
        self.assertEqual(git_blob_sha(previous), OLD_BLOB)

    def test_no_remaining_encoded_call_heads(self):
        # Цей source не містить інших двійкових головів у quoted data.
        start = self.current.index("(визначити my-fc-primitive")
        self.assertEqual(re.findall(r"\([01]{3,9}(?=[\s(])", self.current[start:]), [])
        self.assertIn("(функція (вираз оточення)", self.current)
        self.assertNotIn("(функція (expr ctx)", self.current)

    def test_negative_wrong_peer_fails_closed(self):
        offset, bits, peer = EDIT_RECEIPT[0]
        pre_alpha = undo_alpha(self.current)
        mutant = pre_alpha[:offset] + "(хибна-проєкція" + pre_alpha[offset + len(peer) + 1:]
        with self.assertRaisesRegex(AssertionError, "неправильна/зсунута"):
            reconstruct(mutant)

    def test_negative_reintroduced_old_byte_fails_closed(self):
        offset, bits, peer = EDIT_RECEIPT[-1]
        pre_alpha = undo_alpha(self.current)
        mutant = pre_alpha[:offset] + "(" + bits + pre_alpha[offset + len(peer) + 1:]
        with self.assertRaisesRegex(AssertionError, "неправильна/зсунута"):
            reconstruct(mutant)


if __name__ == "__main__":
    unittest.main(verbosity=2)
