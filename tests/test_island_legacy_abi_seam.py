#!/usr/bin/env python3
"""Незалежний свідок: історичний W8 обмежений зовнішньою ABI-межею CLI."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "crates/sens-cli/src/island_invoke.rs"
OLD_GIT_BLOB = "5506c0dadc3dc58d0a172fcb03579714896d2fe2"

REWRITES = (
    (
        "fn invoke_common_lisp(sens: Sens8, payload: &str) -> Result<Vec<u8>, String> {",
        "fn invoke_common_lisp(id: CommonLispLegacyAbiSemanticId, payload: &str) -> Result<Vec<u8>, String> {",
    ),
    (
        "            CommonLispLegacyAbiSemanticId(sens.packed_byte()),\n            payload,",
        "            id,\n            payload,",
    ),
    (
        "fn invoke_prolog(sens: Sens8, payload: &str) -> Result<Vec<u8>, String> {",
        "fn invoke_prolog(id: PrologLegacyAbiSemanticId, payload: &str) -> Result<Vec<u8>, String> {",
    ),
    (
        "            PrologLegacyAbiSemanticId(sens.packed_byte()),\n            PrologQuery::new(payload, template),",
        "            id,\n            PrologQuery::new(payload, template),",
    ),
    (
        '        "common-lisp" => ("common-lisp", invoke_common_lisp(sens, &payload)),\n'
        '        "prolog" => ("prolog", invoke_prolog(sens, &payload)),',
        '        // Окрема історична ABI-межа: W8 тут не є D8:10101000 ROUND.\n'
        '        "common-lisp" => (\n'
        '            "common-lisp",\n'
        '            invoke_common_lisp(CommonLispLegacyAbiSemanticId(sens.packed_byte()), &payload),\n'
        '        ),\n'
        '        "prolog" => (\n'
        '            "prolog",\n'
        '            invoke_prolog(PrologLegacyAbiSemanticId(sens.packed_byte()), &payload),\n'
        '        ),',
    ),
)


def expected_source() -> str:
    raw = subprocess.run(
        ["git", "cat-file", "blob", OLD_GIT_BLOB],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if sha != OLD_GIT_BLOB:
        raise ValueError("GIT_PIN_DRIFT: вихідний blob не тотожний")
    source = raw.decode("utf-8")
    for old, new in REWRITES:
        if source.count(old) != 1:
            raise ValueError("SOURCE_DRIFT: стара голова або ABI-межа змінилась")
        source = source.replace(old, new)
    return source


def verify(source: str) -> None:
    if source != expected_source():
        raise ValueError("SOURCE_DELTA_BLOCK: заборонено змінювати механізми або дані")
    # Саме історичний ABI, а не сучасний резидент D8.
    if "const RAW_INVOKE_SENS: Sens8 = sens::sens!(10101000);" not in source:
        raise ValueError("HISTORICAL_BOUNDARY_BLOCK: потрібна окрема W8-сумісність")
    if "register_sens_capability(RAW_INVOKE_SENS, evaluate_raw_invoke)" not in source:
        raise ValueError("HISTORICAL_BOUNDARY_BLOCK: перевірено той самий суміснісний слот")


class IslandBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_only_abi_boundary_is_rewritten(self):
        verify(self.source)

    def test_d8_equal_payload_has_different_meaning(self):
        foundation = json.loads(
            (ROOT / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(foundation["domains"]["D8"]["residents"]["10101000"], "ROUND")
        self.assertIn("W8 тут не є D8:10101000 ROUND", self.source)

    def test_reintroduced_sens8_in_kernel_is_blocked(self):
        modified = self.source.replace(
            "fn invoke_prolog(id: PrologLegacyAbiSemanticId,",
            "fn invoke_prolog(sens: Sens8,",
            1,
        )
        self.assertNotEqual(modified, self.source)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            verify(modified)

    def test_native_payload_mutation_is_blocked(self):
        modified = self.source.replace(
            'if payload.trim() != "run" {',
            'if payload.trim() != "changed" {',
            1,
        )
        self.assertNotEqual(modified, self.source)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            verify(modified)


if __name__ == "__main__":
    unittest.main()
