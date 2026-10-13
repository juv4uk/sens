#!/usr/bin/env python3
"""Точкові свідки D7 v2: 7-бітність, компактність і fail-closed генерація."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "generate-domain-owner-registry.py"
OUT = ROOT / "crates" / "sens" / "src" / "domain_owner_generated.rs"
spec = importlib.util.spec_from_file_location("sens_d7_owner_v2", GEN)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load ratified owner generator")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class D7OwnerV2Test(unittest.TestCase):
    def setUp(self) -> None:
        self.source = json.loads(mod.D7.read_text(encoding="utf-8"))

    def test_128_exact_w7_owner_rows_and_generated_bitmask(self) -> None:
        rows = mod.owner_rows()
        seven = [word for width, word, source in rows if width == 7 and source == 3]
        self.assertEqual(len(seven), 128)
        self.assertEqual(seven, [format(n, "07b") for n in range(128)])
        self.assertEqual(len(rows), 245)
        for width, word, _ in rows:
            self.assertEqual(len(word), width)
            self.assertEqual(set(word).difference("01"), set())
        generated = mod.render(rows)
        self.assertEqual(generated, OUT.read_text(encoding="utf-8"))
        self.assertIn(
            "DomainOwnerBitmap { width: 7, slots: "
            "[0xffffffffffffffff, 0xffffffffffffffff] }",
            generated,
        )
        self.assertIn("fn d7_keyboard_v2_occupies_all_128_without_callability", generated)

    def reject_mutation(self, mutate) -> None:
        wrong = json.loads(json.dumps(self.source))
        mutate(wrong)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "d7-invalid.json"
            source.write_text(json.dumps(wrong, ensure_ascii=False), encoding="utf-8")
            with patch.object(mod, "D7", source):
                with self.assertRaises(SystemExit):
                    mod.owner_rows()

    def test_wrong_d7_width_and_coordinate_fail_closed(self) -> None:
        self.reject_mutation(lambda data: data.update(width=8))
        self.reject_mutation(lambda data: data["table"][33].update(bits="00100001"))
        self.reject_mutation(lambda data: data["table"][65].update(bits="1000010"))

    def test_equal_ukrainian_glyphs_cannot_share_two_codes(self) -> None:
        self.reject_mutation(
            lambda data: data["table"][65].update(uk=data["table"][66]["uk"])
        )

    def test_legacy_126_cell_authority_is_rejected(self) -> None:
        old = ROOT / "knowledge" / "d7-ratified.json"
        with patch.object(mod, "D7", old):
            with self.assertRaises(SystemExit):
                mod.owner_rows()


if __name__ == "__main__":
    unittest.main()
