#!/usr/bin/env python3
"""Verify the pinned golden x86-64 encoder corpus fixture.

Checks performed:

  * the fixture parses and uses the expected schema;
  * every per-case `sha256` matches the case's `bytes_hex`;
  * the top-level `corpus_sha256` matches the canonical corpus digest;
  * when `as`, `nasm` and `objcopy` are present, the corpus is re-derived by
    both independent assemblers and must be byte-identical to the fixture.

Run: python3 scripts/test-machine-asm-corpus.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "crates" / "sens" / "tests" / "fixtures" / "machine-asm-corpus.json"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_machine_asm_fixtures", ROOT / "scripts" / "gen-machine-asm-fixtures.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GoldenCorpusWitnesses(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not FIXTURE.is_file():
            raise AssertionError(f"missing golden corpus fixture: {FIXTURE}")
        cls.corpus = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.generator = _load_generator()

    def test_schema(self) -> None:
        self.assertEqual(self.corpus["schema"], "sens.machine-asm-corpus/v1")
        self.assertTrue(self.corpus["cases"], "corpus must not be empty")
        for case in self.corpus["cases"]:
            for key in ("name", "form", "gas", "nasm", "bytes_hex", "sha256"):
                self.assertIn(key, case)
            self.assertTrue(case["form"].strip(), f"empty form for {case['name']}")

    def test_per_case_sha256_matches_bytes(self) -> None:
        for case in self.corpus["cases"]:
            digest = hashlib.sha256(bytes.fromhex(case["bytes_hex"])).hexdigest()
            self.assertEqual(digest, case["sha256"], case["name"])

    def test_corpus_digest_matches(self) -> None:
        digest = self.generator._corpus_digest(self.corpus["cases"])
        self.assertEqual(digest, self.corpus["corpus_sha256"])

    def test_fixture_reproducible_with_external_assemblers(self) -> None:
        import shutil
        if any(shutil.which(tool) is None for tool in ("as", "nasm", "objcopy")):
            self.skipTest("external assemblers unavailable; pinning check only")
        live = self.generator.build_corpus()
        self.assertEqual(live["corpus_sha256"], self.corpus["corpus_sha256"])


if __name__ == "__main__":
    unittest.main()
