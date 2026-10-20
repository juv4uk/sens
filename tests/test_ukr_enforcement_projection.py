"""Regression for exact-width D3/D4 Ukrainian source projection in 3 enforcement scripts.

The reverse transformation must reproduce the PRE-MIGRATION GIT BLOB bit-for-bit.
No Git checkout history, runtime D10 admission or external Python semantics oracle
is required; this is a source-identity guard, not a SENS execution proof.
"""
import hashlib
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ratified identities read from current domain tables, never inferred from bytes.
PROJECTIONS = {
    "0011": ("визначити", 4),
    "001": ("як-є", 3),
    "010": ("атом?", 3),
    "100": ("перше", 3),
    "101": ("тотожне?", 3),
    "110": ("за-умовою", 3),
    "11110111": ("однакові?", 8),
}
OLD_SHA = {
    "scripts/semantic-authority-guard-enforce.lisp": "09aeeb298e81b7967a01fd4557b1190d89b15214",
    "scripts/enforce-island-math-evidence.lisp": "3846a25962d3674ab9df578032ea6d3851ac5ed3",
    "scripts/enforce-function-table-mechanisms.lisp": "94cd3dd8966582ba4a5df95e8a1e800507999438",
}
EXPECTED = {
    "scripts/semantic-authority-guard-enforce.lisp": {"0011": 3, "001": 10, "010": 4, "100": 4, "101": 3, "110": 3, "11110111": 0},
    "scripts/enforce-island-math-evidence.lisp": {"0011": 2, "001": 4, "010": 1, "100": 2, "101": 0, "110": 1, "11110111": 1},
    "scripts/enforce-function-table-mechanisms.lisp": {"0011": 2, "001": 4, "010": 1, "100": 2, "101": 0, "110": 1, "11110111": 1},
}
# Поточні D9 resident-и з lib/domains/d9.lisp. Ідентичність не виводимо
# із історичного сід8 або ширини W8: reader peers мають власний D9 код.
D9_READERS = {"110101001": "читати-всі", "110110111": "читати-файл"}
D9_INVERSE = {value: key for key, value in D9_READERS.items()}
# Git blob-и безпосередньо перед ЦІЄЮ D9 партією, вже після D3/D4 cutover.
D9_BEFORE_SHA = {
    "scripts/enforce-island-math-evidence.lisp": "df91dcd10b4be60059feef7705d5aab8876a1f11",
    "scripts/enforce-function-table-mechanisms.lisp": "cf2de15689cfbb987e7b182690a5adf3308ae6ec",
    "scripts/semantic-authority-guard-enforce.lisp": "9e47c58902e9785eef852a8e2f52d3cf6a7328ea",
}

NAMES = {bits: name for bits, (name, _) in PROJECTIONS.items()}
INVERSE = {name: bits for bits, name in NAMES.items()}


def heads(source, names):
    """Only syntactic heads, excluding strings and semicolon comments."""
    found = []
    i = 0
    in_string = escaped = in_comment = False
    while i < len(source):
        ch = source[i]
        if ch == "\n":
            in_comment = False
        elif in_comment:
            pass
        elif in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == ";":
            in_comment = True
        elif ch == '"':
            in_string = True
        elif ch == "(":
            j = i + 1
            while j < len(source) and source[j] in " \t\n":
                j += 1
            m = re.match(r'[^\s();"\']+', source[j:])
            if m and m.group() in names and (
                j + len(m.group()) < len(source)
                and source[j + len(m.group())].isspace()
            ):
                found.append((j, j + len(m.group()), m.group()))
        i += 1
    return found


def replace_heads(source, names):
    changes = heads(source, names)
    result = source
    for start, end, old in reversed(changes):
        result = result[:start] + names[old] + result[end:]
    return result


def git_blob_sha(source):
    data = source.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


class UkrainianEnforcementProjection(unittest.TestCase):
    def test_authority_at_exact_width(self):
        for bits, (ukr, width) in PROJECTIONS.items():
            with self.subTest(bits=bits):
                table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
                self.assertEqual(len(bits), width)
                rows = [line for line in table.splitlines()
                        if re.match(r"\s*\(" + bits + r"\s", line)]
                self.assertEqual(len(rows), 1)
                self.assertIn("(укр " + ukr + ")", rows[0])

    def test_inverse_restores_original_git_blob_without_other_changes(self):
        for path, old_sha in OLD_SHA.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                # Спочатку повернути 6 нових D9-голів, далі стару перевірену
                # D3/D4 міграцію. OLD_SHA лишається незмінним.
                before_d9 = replace_heads(source, D9_INVERSE)
                self.assertEqual(git_blob_sha(before_d9), D9_BEFORE_SHA[path])
                inverse = replace_heads(before_d9, INVERSE)
                self.assertEqual(git_blob_sha(inverse), old_sha)
                self.assertEqual(
                    replace_heads(replace_heads(inverse, NAMES), D9_READERS),
                    source,
                )
                self.assertEqual(source.count("\n"), inverse.count("\n"))

    def test_exact_projection_counts(self):
        for path, expected in EXPECTED.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                projected = Counter(name for _, _, name in heads(source, INVERSE))
                self.assertEqual(
                    projected,
                    Counter({NAMES[code]: count for code, count in expected.items() if count}),
                )
                self.assertEqual(heads(source, NAMES), [])

    def test_quoted_verdict_data_and_other_domains_unchanged(self):
        original_tags = {
            "scripts/semantic-authority-guard-enforce.lisp":
                ("(як-є semantic-authority-ok)", "(як-є semantic-authority-violation)", "(як-є empty-verdict)"),
            "scripts/enforce-island-math-evidence.lisp":
                ("(як-є island-math-evidence-ok)", "(однакові? verdict"),
            "scripts/enforce-function-table-mechanisms.lisp":
                ("(як-є function-table-mechanisms-ok)", "(однакові? verdict"),
        }
        for path, snippets in original_tags.items():
            source = (ROOT / path).read_text(encoding="utf-8")
            for snippet in snippets:
                with self.subTest(path=path, text=snippet):
                    self.assertIn(snippet, source)

    def test_d9_readers_current_authority_and_exact_lexical_counts(self):
        table = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        for bits, ukrainian in D9_READERS.items():
            with self.subTest(bits=bits):
                rows = [line for line in table.splitlines()
                        if re.match(r"\s*\(" + bits + r"\s", line)]
                self.assertEqual(len(rows), 1)
                self.assertIn("(укр " + ukrainian + ")", rows[0])
        for path, old_sha in D9_BEFORE_SHA.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(Counter(item[2] for item in heads(
                    source, D9_INVERSE)), Counter(D9_READERS.values()))
                self.assertEqual(heads(source, D9_READERS), [])
                prior = replace_heads(source, D9_INVERSE)
                self.assertEqual(git_blob_sha(prior), old_sha)
                self.assertEqual(replace_heads(prior, D9_READERS), source)

    def test_d9_wrong_peer_mutant_is_detected_without_loosening_old_ledger(self):
        for path, old_sha in D9_BEFORE_SHA.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                wrong = source.replace("(читати-файл ", "(читати-всі ", 1)
                self.assertNotEqual(wrong, source)
                restored = replace_heads(wrong, D9_INVERSE)
                self.assertNotEqual(git_blob_sha(restored), old_sha)

    def test_comments_and_strings_must_not_be_rewritten(self):
        sample = '; (0011 X)\n" (001 X) " (0011 x)\n(0011 alive)\n'
        new = replace_heads(sample, NAMES)
        self.assertEqual(new, '; (0011 X)\n" (001 X) " (визначити x)\n(визначити alive)\n')
        self.assertEqual(replace_heads(new, INVERSE), sample)


if __name__ == "__main__":
    unittest.main(verbosity=2)
