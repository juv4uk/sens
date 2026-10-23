#!/usr/bin/env python3
"""Інструментальна перевірка табло «Драбини», не тест семантики SENS."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("domain_game", ROOT / "scripts" / "domain-game.py")
assert SPEC is not None and SPEC.loader is not None
game = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(game)

FILES = [
    "tests/semantic/d2-frame-law.lisp",
    "tests/semantic/d2-frame-mutant.lisp",
    "tests/semantic/d24-ratio-law.lisp",
    "tests/semantic/d24-ratio-mutant.lisp",
    "tests/semantic/d48-width-law.lisp",
]


class DomainGameTests(unittest.TestCase):
    def test_display_includes_every_counted_domain(self) -> None:
        # Злам: загальна сума враховує D24/D48, але табло їх приховує.
        output = io.StringIO()
        with patch.object(game, "tracked", return_value=FILES):
            with contextlib.redirect_stdout(output):
                self.assertEqual(game.main([]), 0)
        shown = output.getvalue()
        self.assertIn("D24", shown)
        self.assertIn("D48", shown)
        self.assertIn("Усього файлів Lisp із доменним префіксом: 5", shown)

    def test_brief_counts_visible_levels_including_new_domains(self) -> None:
        # Злам: --brief звітує лише про жорстко записані рівні.
        output = io.StringIO()
        with patch.object(game, "tracked", return_value=FILES):
            with contextlib.redirect_stdout(output):
                self.assertEqual(game.main(["--brief"]), 0)
        self.assertIn("рівнів 14, файлів Lisp 5", output.getvalue())

    def test_d13_research_candidates_are_distinct_and_not_ratified(self) -> None:
        # Лише дослідницькі гіпотези: жодна координата чи викличність не виникає.
        source = (ROOT / "research/d13/function-candidates.lisp").read_text(encoding="utf-8")
        candidates = game.d13_candidates(source)
        self.assertEqual(len(candidates), 10)
        self.assertEqual(len({name for name, _ in candidates}), 10)
        self.assertIn(("розширений-нсд", "extended-gcd"), candidates)
        self.assertIn(("цілий-корінь", "integer-square-root"), candidates)

    def test_d13_research_rejects_implicit_ratification_and_missing_law(self) -> None:
        source = (ROOT / "research/d13/function-candidates.lisp").read_text(encoding="utf-8")
        for broken in (
            source.replace("(status . experimental-unratified)",
                           "(status . owner-ratified)", 1),
            source.replace("(coordinates . unassigned)",
                           "(coordinates . assigned)", 1),
            source.replace("(law .", "(missing-law .", 1),
        ):
            with self.subTest(broken=broken[:80]):
                with self.assertRaises(ValueError):
                    game.d13_candidates(broken)


    def test_d13_numeric_signatures_are_exact_and_cover_edge_cases(self) -> None:
        import re

        source = (ROOT / "research/d13/function-candidates.lisp").read_text(encoding="utf-8")
        signatures = re.findall(r'\(signature \.\s*"([^"]+)"\)', source)
        self.assertEqual(10, len(signatures))
        self.assertTrue(all("Z*" not in signature and "Q*" not in signature for signature in signatures))
        self.assertIn("ℤ", source)
        self.assertIn("ℚ", source)
        self.assertIn("a=b=0,c=0 — ALL_PAIRS", source)
        self.assertIn("n=15", source)
        ambiguous = source.replace('(signature . "ℤ × ℤ ->', '(signature . "Z* × Z* ->', 1)
        with self.assertRaises(ValueError):
            game.d13_candidates(ambiguous)

    def test_d13_game_shows_candidates_without_semantic_points(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(game.main(["--track", "d13-candidates", "--brief"]), 0)
        shown = output.getvalue()
        self.assertIn("кандидатів=10", shown)
        self.assertIn("семантика=НЕ_ДОВЕДЕНО", shown)

    def test_d11_codec_game_lists_native_gates_and_needs_a_run_for_points(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(game.main(["--track", "d11-codec", "--brief"]), 0)
        self.assertIn("CODEC-D11: verified=0/7 native=NOT_RUN", output.getvalue())

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(game.main(["--track", "d11-codec"]), 0)
        self.assertIn("--track d11-codec --verify", output.getvalue())

        source = (ROOT / "research/zig-codecs/d11_selector_contest.zig").read_text(encoding="utf-8")
        declared = set(game.re.findall(r'^test "([^"]+)"', source, flags=game.re.MULTILINE))
        for _, _, tests in game.D11_CODEC_LEVELS:
            self.assertIsNotNone(tests)
            self.assertTrue(all(name in declared for name in tests or ()))

    def test_codec_quest_and_d12_remain_visible(self) -> None:
        # Злам: виправлення табло прибрало чинний дослід D2 та щабель D12.
        output = io.StringIO()
        with patch.object(game, "tracked", return_value=FILES):
            with contextlib.redirect_stdout(output):
                self.assertEqual(game.main([]), 0)
        shown = output.getvalue()
        self.assertIn("D12", shown)
        self.assertIn("ЕКСПЕРИМЕНТ КОДЕКУ", shown)


if __name__ == "__main__":
    unittest.main()
