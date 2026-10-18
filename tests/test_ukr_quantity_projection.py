"""Quantity: exact D1/D3–D6 ukr source projection, not a Python SENS evaluator."""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/quantity.lisp"
BASE_BLOB = "e06af39b35862b3f993009fbcff17e5649fa2d56"
NATIVE = {
    3: {"001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити"},
    4: {"0010": "функція", "0011": "визначити", "0101": "порожній?",
        "1001": "друге", "1110": "список", "1111": "приєднати"},
    5: {"01011": "відняти", "10011": "третє"},
    6: {"001000": "нехай", "100111": "четверте"},
}
HEAD_COUNTS = {
    "100": 7, "101": 34, "110": 12, "1001": 6, "1110": 20,
    "10011": 6, "100111": 2, "0011": 37, "001": 69, "0010": 33,
    "010": 7, "011": 15, "01011": 1,
}
D1_LITERAL_COUNTS = {"#d1:1": 19}
MAP = {bits: name for table in NATIVE.values() for bits, name in table.items()}
REVERSE = {name: bits for bits, name in MAP.items()}
D1 = {"#d1:1": "так", "#d1:0": "ні"}
D1_REVERSE = {value: key for key, value in D1.items()}
D9 = {"110101100": "символ?", "110110101": "п'ятий"}
D9_REVERSE = {name: bits for bits, name in D9.items()}
FALSE_EXPR = "(тотожне? (як-є (0)) (як-є (1)))"
PRE_REPAIR_BLOB = "8ed44251876053a778837c7739427b7c20427026"

# Новий незалежний локальний шар. Він НЕ стає D9/D10 identity:
# English aliases в кінці файла посилаються на ті самі SENS-замикання.
LOCAL_QUANTITY_BLOB = "9baec7d8c33011bb52944cf0cd4cbe63e2910e8c"
LOCAL_HELPERS = (
    ("science-proper-list?", "науковий-список-правильний?", 7),
    ("science-list-length-equals?", "науковий-список-довжина-дорівнює?", 5),
    ("science-sixth", "науковий-шостий", 2),
    ("science-seventh", "науковий-сьомий", 2),
)
LOCAL_ALIASES = "\n; Українські локальні імена є тими самими Lisp-замиканнями.\n; Старі імена лишаються сумісними проєкціями для зовнішніх споживачів.\n; Це не нові D9/D10 identity, не новий механізм і не D24+ математика.\n(визначити science-proper-list? науковий-список-правильний?)\n(визначити science-list-length-equals? науковий-список-довжина-дорівнює?)\n(визначити science-sixth науковий-шостий)\n(визначити science-seventh науковий-сьомий)\n"


def restore_local_helper_layer(source: str) -> str:
    """Exact source-only inverse; refusal on wrong peer, not semantic evaluation."""
    if not source.endswith(LOCAL_ALIASES):
        raise AssertionError("відсутні сумісні локальні аліаси Quantity")
    body = source[:-len(LOCAL_ALIASES)]
    for english, ukrainian, calls in LOCAL_HELPERS:
        if (body.count("(" + ukrainian) != calls
                or body.count("(визначити " + ukrainian) != 1):
            raise AssertionError("порушена локальна українська проєкція: " + ukrainian)
        body = body.replace("(" + ukrainian, "(" + english)
        body = body.replace("(визначити " + ukrainian, "(визначити " + english)
    if git_blob(body) != LOCAL_QUANTITY_BLOB:
        raise AssertionError("оригінальний Git blob локальної проєкції не відновлено")
    return body


def apply_local_helper_layer(source: str) -> str:
    """Forward receipt, ensuring new live source is independently reconstructible."""
    body = source
    for english, ukrainian, calls in LOCAL_HELPERS:
        if (body.count("(" + english) != calls
                or body.count("(визначити " + english) != 1):
            raise AssertionError("порушено зворотну локальну проєкцію: " + english)
        body = body.replace("(" + english, "(" + ukrainian)
        body = body.replace("(визначити " + english, "(визначити " + ukrainian)
    return body + LOCAL_ALIASES


def project_heads(text: str, mapping: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Only first source atom after (. Strings/comments and every other byte copy."""
    chunks: list[str] = []
    seen: dict[str, int] = {}
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == ";":
            j = text.find("\n", i)
            if j < 0:
                j = n
            chunks.append(text[i:j])
            i = j
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            chunks.append(text[i:j])
            i = j
            continue
        if ch == "(":
            chunks.append(ch)
            i += 1
            j = i
            while j < n and text[j].isspace():
                j += 1
            chunks.append(text[i:j])
            if j < n and not (text[j].isspace() or text[j] in '();"\''):
                k = j
                while k < n and not (text[k].isspace() or text[k] in '();'):
                    k += 1
                word = text[j:k]
                mapped = mapping.get(word)
                chunks.append(word if mapped is None else mapped)
                if mapped is not None:
                    seen[word] = seen.get(word, 0) + 1
                i = k
            else:
                i = j
            continue
        chunks.append(ch)
        i += 1
    return "".join(chunks), seen


def project_literals(text: str, mapping: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Exact atom projection outside strings/comments; quoted (0)/(1) remain data."""
    chunks: list[str] = []
    seen: dict[str, int] = {}
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == ";":
            j = text.find("\n", i)
            if j < 0:
                j = n
            chunks.append(text[i:j])
            i = j
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            chunks.append(text[i:j])
            i = j
            continue
        if ch.isspace() or ch in "();":
            chunks.append(ch)
            i += 1
            continue
        j = i
        while j < n and not (text[j].isspace() or text[j] in '();"'):
            j += 1
        word = text[i:j]
        mapped = mapping.get(word)
        chunks.append(word if mapped is None else mapped)
        if mapped is not None:
            seen[word] = seen.get(word, 0) + 1
        i = j
    return "".join(chunks), seen


def git_blob(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class QuantityUkrProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_ratifed_exact_domain_keys(self):
        self.assertEqual(len(MAP), len(REVERSE), "ambiguous peer inversion")
        for domain, values in NATIVE.items():
            table = (ROOT / f"lib/domains/d{domain}.lisp").read_text(encoding="utf-8")
            for bits, ukr in values.items():
                with self.subTest(domain=domain, bits=bits):
                    self.assertRegex(table, re.compile(
                        r"^\s*\(" + bits + r"\s+\(ук\s+[^()]+\)\s+\(укр\s+"
                        + re.escape(ukr) + r"\)", re.MULTILINE))
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        self.assertIn("(0 (ук ні) (укр ні)", d1)
        self.assertIn("(1 (ук так) (укр так)", d1)

    def restore_previous(self):
        canonical_local = restore_local_helper_layer(self.source)
        expanded, false_count = project_literals(canonical_local, {"ні": FALSE_EXPR})
        previous, peer_counts = project_heads(expanded, D9_REVERSE)
        self.assertEqual(false_count, {"ні": 5})
        self.assertEqual(peer_counts, {"символ?": 3, "п'ятий": 2})
        self.assertEqual(git_blob(previous), PRE_REPAIR_BLOB)
        return previous

    def test_exact_original_git_blob_recoverable(self):
        previous = self.restore_previous()
        old_d1, seen_d1 = project_literals(previous, D1_REVERSE)
        old, seen = project_heads(old_d1, REVERSE)
        self.assertEqual(seen, {MAP[bits]: n for bits, n in HEAD_COUNTS.items()})
        self.assertEqual(seen_d1, {"так": 19})
        self.assertEqual(git_blob(old), BASE_BLOB)

    def test_no_remaining_claimed_numeric_heads_or_d1_literals(self):
        same, left = project_heads(self.source, MAP)
        self.assertEqual(left, {})
        self.assertEqual(same, self.source)
        same, left = project_literals(self.source, D1)
        self.assertEqual(left, {})
        self.assertEqual(same, self.source)
        same, left = project_heads(self.source, D9)
        self.assertEqual(left, {})
        self.assertEqual(same, self.source)

    def test_two_way_projection_idempotence(self):
        previous = self.restore_previous()
        raw, _ = project_heads(project_literals(previous, D1_REVERSE)[0], REVERSE)
        again, _ = project_heads(raw, MAP)
        again, _ = project_literals(again, D1)
        again, _ = project_heads(again, D9)
        self.assertEqual(again.count(FALSE_EXPR), 5)
        again = again.replace(FALSE_EXPR, "ні")
        self.assertEqual(again, restore_local_helper_layer(self.source))
        self.assertEqual(apply_local_helper_layer(again), self.source)

    def test_comments_strings_and_quoted_data_unchanged(self):
        synthetic = '; #d1:1 (0011 ignored)\n"(010 not-code) #d1:1"\n(0011 x (001 (0)))\n'
        migrated, counts = project_heads(synthetic, MAP)
        migrated, d1counts = project_literals(migrated, D1)
        self.assertEqual(counts, {"0011": 1, "001": 1})
        self.assertEqual(d1counts, {})
        self.assertIn('; #d1:1 (0011 ignored)', migrated)
        self.assertIn('"(010 not-code) #d1:1"', migrated)
        self.assertIn("(визначити x (як-є (0)))", migrated)

    def test_data_tags_d9_and_exact_d1_false(self):
        self.assertIn("(як-є dimension/1)", self.source)
        self.assertIn("(як-є scientific-constant)", self.source)
        self.assertNotIn("(як-є (0))", self.source)
        self.assertNotIn("(як-є (1))", self.source)
        self.assertNotIn("(110101100", self.source)
        self.assertNotIn("(110110101", self.source)
        self.assertIn("(символ?", self.source)
        self.assertIn("(п'ятий", self.source)
        self.assertIn("(так", self.source)
        self.assertEqual(project_literals(self.source, {"ні": FALSE_EXPR})[1], {"ні": 5})

    def test_d9_peer_names_have_exact_domain_and_core4_authority(self):
        table = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        core = (ROOT / "lib/core4.lisp").read_text(encoding="utf-8")
        for bits, ukr in D9.items():
            with self.subTest(bits=bits):
                self.assertRegex(table, re.compile(
                    r"^\s*\(" + bits + r"\s+\(ук\s+" + re.escape(ukr)
                    + r"\)\s+\(укр\s+" + re.escape(ukr) + r"\)", re.MULTILINE))
                self.assertRegex(core, re.compile(
                    r"^\(визначити\s+" + re.escape(ukr) + r"[\s()]", re.MULTILINE))

    def test_definition_names_remain_historical(self):
        old, _ = project_heads(project_literals(self.restore_previous(), D1_REVERSE)[0], REVERSE)
        definitions_old = re.findall(r"\(0011\s+([^\s()]+)", old)
        historical = restore_local_helper_layer(self.source)
        definitions_new = re.findall(r"\(визначити\s+([^\s()]+)", historical)
        self.assertEqual(definitions_old, definitions_new)
        self.assertEqual(len(definitions_new), 37)

    def test_wrong_local_helper_mutant_fails_strict_inverse(self):
        bad = self.source.replace(
            "(науковий-шостий x)", "(науковий-сьомий x)", 1
        )
        self.assertNotEqual(bad, self.source)
        with self.assertRaisesRegex(AssertionError, "порушена локальна"):
            restore_local_helper_layer(bad)

    def test_lisp_delimiters_balanced_without_python_semantics(self):
        code = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"', "", self.source)
        depth = 0
        for char in code:
            depth += (char == "(") - (char == ")")
            self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
