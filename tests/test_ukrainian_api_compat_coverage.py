#!/usr/bin/env python3
"""Verify exact public *historical* Ukrainian compatibility reference coverage.

The current semantic authority is the ratified exact D1..D9 domain tables.
This test only keeps the already-existing legacy surface registry's Markdown
reference complete for the existing SENS-hosted verify-repo.lisp policy.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "lib/surface/semantic-registry.lisp"
LEGACY_DOCS = ROOT / "lib/surface/uk-docs.lisp"
PUBLIC = ROOT / "docs/ukrainian-api.md"
REGISTRY_ROW = re.compile(r"^\s*\(([01]{8})\s+[^\n]*?\(ук ([^\s()]+)\)", re.MULTILINE)
DOC_ENTRY = re.compile(r"^\s*\(doc\s+\S+\s+([01]{8})\s+", re.MULTILINE)
MD_ROW = re.compile(r"^\| `([^|`]+)` \| `([01]{8})` \| [^\n]*\|$", re.MULTILINE)


def verify_reference(registry: str, old_docs: str, markdown: str) -> dict:
    pairs = [(id_, uk) for id_, uk in REGISTRY_ROW.findall(registry)]
    if not pairs:
        raise ValueError("empty historical source registry")
    if len(pairs) != len(set(pairs)):
        raise ValueError("duplicate stable historical pair in registry")
    if len(set(id_ for id_, _ in pairs)) != len(pairs):
        raise ValueError("duplicated stable historical ID")
    if len(set(uk for _, uk in pairs)) != len(pairs):
        raise ValueError("ambiguous historical Ukrainian spelling")
    documented = DOC_ENTRY.findall(old_docs)
    if not documented or len(documented) != len(set(documented)):
        raise ValueError("missing or repeated historical documentation IDs")
    ids = {id_ for id_, _ in pairs}
    if not set(documented).issubset(ids):
        raise ValueError("legacy function docs no longer correspond to stable registry")
    rows = [(id_, uk) for uk, id_ in MD_ROW.findall(markdown)]
    if len(rows) != len(set(rows)):
        raise ValueError("duplicate public compatibility Markdown entry")
    if set(rows) != set(pairs):
        missing = sorted(set(pairs) - set(rows))
        excess = sorted(set(rows) - set(pairs))
        raise ValueError(f"Markdown legacy surface mismatch missing={missing[:3]}, extra={excess[:3]}")
    if len(rows) != len(pairs):
        raise ValueError("public historical row count mismatch")
    if "лише історичні ключі сумісності" not in markdown:
        raise ValueError("historic compatibility keys must not be presented as ratified D8 meaning")
    if "D1–D9" not in markdown or "Точна ширина" not in markdown and "exact" not in markdown:
        raise ValueError("missing current exact-domain authority disclaimer")
    return {"stable_uk_rows": len(pairs),
            "legacy_docs_rows": len(documented),
            "extra_registry_only_rows": len(pairs) - len(documented),
            "current_semantic_authority_changed": False,
            "historical_executable_migrations_admitted": 0}


class UkrainianCompatReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = REGISTRY.read_text(encoding="utf-8")
        cls.legacy_docs = LEGACY_DOCS.read_text(encoding="utf-8")
        cls.markdown = PUBLIC.read_text(encoding="utf-8")

    def test_actual_policy_registry_coverage(self):
        state = verify_reference(self.registry, self.legacy_docs, self.markdown)
        self.assertGreaterEqual(state["stable_uk_rows"], 140)
        self.assertEqual(state["legacy_docs_rows"], 140)
        self.assertEqual(state["stable_uk_rows"], 163)
        self.assertEqual(state["extra_registry_only_rows"], 23)
        self.assertFalse(state["current_semantic_authority_changed"])
        self.assertEqual(state["historical_executable_migrations_admitted"], 0)

    def test_dropping_any_public_name_is_blocked(self):
        for name in ("як-є", "ланцюжок-першого-аргументу", "відповідь-тотожне"):
            marker = f"| `{name}` |"
            self.assertIn(marker, self.markdown)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "mismatch"):
                verify_reference(self.registry, self.legacy_docs,
                                 self.markdown.replace(marker, "| `HIDDEN` |"))

    def test_wrong_or_duplicate_historical_identity_is_blocked(self):
        pair = "| `як-є` | `00000001` |"
        self.assertIn(pair, self.markdown)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify_reference(self.registry, self.legacy_docs,
                             self.markdown.replace(pair, "| `як-є` | `11111111` |"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verify_reference(self.registry, self.legacy_docs,
                             self.markdown + "\n" + pair + " duplicate |\n")

    def test_no_implicit_domain_or_executable_admission(self):
        self.assertIn("не право виконання", self.markdown)
        self.assertIn("тільки ратифікований домен D1–D9", self.markdown)


if __name__ == "__main__":
    unittest.main()
