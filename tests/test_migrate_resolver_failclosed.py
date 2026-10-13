#!/usr/bin/env python3
"""Mechanical SourceResolver consistency: must reject false-positive admission under -O.

This is NOT an alternative SENS semantics oracle. It tests only the transport
boundary where resolved=True MUST have a current exact-domain identity.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "sens_migrator_resolver_integrity", SCRIPTS / "migrate-to-sens-codes.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import production SENS migrator")
migrator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migrator
SPEC.loader.exec_module(migrator)


class ResolverWithContradictoryVerdict:
    def __init__(self, bad_token: str | None = None):
        self.bad_token = bad_token

    def resolve_head(self, token: str):
        if token == self.bad_token:
            return SimpleNamespace(resolved=True, current=None, ambiguous=(), kind="resolved")
        if token == "100":
            exact = migrator.Entry("D3", 3, "100", "CAR", "test-exact-domain")
            return SimpleNamespace(resolved=True, current=exact, ambiguous=(), kind="exact")
        raise RuntimeError(f"unexpected resolver lookup: {token!r}")


class MigratorFailClosedTests(unittest.TestCase):
    def rewrite(self, source: str, bad_token: str | None = None):
        return migrator.binary_rewrite(
            source, {}, None, None, None,
            ResolverWithContradictoryVerdict(bad_token)
        )

    def test_three_resolution_boundaries_reject_missing_identity(self):
        cases = (
            ("executable-head", "(100 ())\n", "100"),
            ("historical-eight-bit-data", "(100 00000001)\n", "00000001"),
            ("exact-three-bit-data", "(100 101)\n", "101"),
        )
        for label, source, token in cases:
            with self.subTest(test_id=label, token=token):
                with self.assertRaisesRegex(
                    migrator.BinaryMigrationError, "INCONSISTENT_DOMAIN_RESOLUTION"
                ) as failure:
                    self.rewrite(source, bad_token=token)
                self.assertIn(repr(token), str(failure.exception))
                self.assertIn("1:", str(failure.exception))

    def test_normal_exact_head_still_serializes_unchanged(self):
        result, hits, _ = self.rewrite("(100 ())\n")
        self.assertEqual(result, "10 100 00 000 01\n")
        self.assertEqual([(hit.domain, hit.bits) for hit in hits], [("D3", "100")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
