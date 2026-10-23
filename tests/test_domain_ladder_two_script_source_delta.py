"""Exact, source-only audit for two newly migrated Lisp service scripts.

Replay the owner-audited mapping against the original Git blobs. Unknown
historical code words are explicitly pinned to themselves in this witness:
they are NOT admitted successors and are never silently mapped.
"""
import json
import re
import runpy
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = runpy.run_path(str(ROOT / "scripts/migrate-domain-ladder-source-batch.py"))

CASES = (
    (
        "scripts/generate-functions-md.lisp",
        "478f608a7d5a3032b8138dc995b744fbefb3ccf4",
        138,
        {"01000111": 1},  # internal helper without a resident
    ),
    (
        "scripts/benchmark-semantic-registry-read.lisp",
        "37e91a09af154a33b46b88aa1c24b0abecdb04ab",
        23,
        {"01011010": 3},  # MONO-NS is an unratified D10 candidate
    ),
)


def old_blob(sha):
    cp = subprocess.run(
        ["git", "cat-file", "-p", sha],
        cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return cp.stdout



def pinned_historical_words(ukr_mapping):
    """Reconstruct the *archived* bit-stage witness, never current Lisp output.

    Current migration writes full укр. The old source-delta proof intentionally
    replays an intermediate bit-stage Git blob, so it needs the exact historical
    domain successor rather than a human source spelling.
    """
    corpus = json.loads(
        (ROOT / "knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8")
    )
    surfaces = {
        f"D{width}": {
            row.bits: row.ukr
            for row in MIGRATION["read_domain_table"](ROOT / f"lib/domains/d{width}.lisp")
        }
        for width in (3, 4, 5, 6, 8, 9)
    }
    words = {}
    for record in corpus["rows"]:
        legacy = record["legacy_code"]
        if legacy not in ukr_mapping:
            continue
        exact = set(re.findall(r"D(10|[1-9]):([01]+)", record.get("current_target") or ""))
        if len(exact) != 1:
            raise AssertionError(f"{legacy}: historical successor is not unique")
        width, bits = next(iter(exact))
        if surfaces.get(f"D{width}", {}).get(bits) != ukr_mapping[legacy]:
            raise AssertionError(f"{legacy}: archived successor differs from current укр")
        words[legacy] = bits
    if set(words) != set(ukr_mapping):
        raise AssertionError("historical crosswalk no longer covers admitted callers")
    return words


class HistoricalScriptSourceDelta(unittest.TestCase):
    def test_ratifed_current_authority_and_unresolved_holds(self):
        mapping, blocked = MIGRATION["authority"](ROOT)
        self.assertEqual(len(mapping), 171)
        self.assertEqual(mapping["00001001"], "визначити")
        self.assertNotIn("01011010", mapping)
        self.assertNotIn("01000111", mapping)
        self.assertEqual(blocked["01011010"], "D10-RECOVERY-CANDIDATE")
        self.assertEqual(blocked["01000111"], "INTERNAL-NO-SEMANTIC-SLOT")

    def test_exact_source_change_only_admitted_call_heads(self):
        mapping, blocked = MIGRATION["authority"](ROOT)
        archived_bits = pinned_historical_words(mapping)
        for path, blob_sha, number_replaced, holds in CASES:
            with self.subTest(path=path):
                original = old_blob(blob_sha)
                current = (ROOT / path).read_text(encoding="utf-8")
                # This overlay is test-only: unresolved code words must retain
                # identical bytes, NOT gain current language identities.
                test_mapping = dict(archived_bits)
                for word in holds:
                    test_mapping[word] = word
                projection, candidate_count, problems = MIGRATION["rewrite"](
                    original, test_mapping, blocked
                )
                self.assertFalse(problems)
                self.assertEqual(candidate_count, number_replaced + sum(holds.values()))
                # Генератор отримав наступний окремий ручний прохід
                # тільки по локальних іменах. Історичне бітове свідчення
                # зберігаємо на точному Git blob до цього проходу; зв'язок
                # із чинним source доводить окремий тест проєкції імен.
                before_name_pass = (
                    old_blob("d73eb60620842d226f33a4f8b5b0feb418be1723")
                    if path == "scripts/generate-functions-md.lisp" else current
                )
                self.assertEqual(projection, before_name_pass)
                self.assertNotEqual(original, current)
                for word in holds:
                    self.assertIn(word, current)


if __name__ == "__main__":
    unittest.main()
