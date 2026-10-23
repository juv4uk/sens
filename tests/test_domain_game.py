"""Перевірки лише інструмента гри; семантичний вердикт належить SENS."""

import contextlib
import importlib.util
import io
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "domain-game.py"
spec = importlib.util.spec_from_file_location("domain_game", SCRIPT)
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)

class DomainGameTests(TestCase):
    def test_numeric_ladder_has_d12_and_d24(self):
        domains = {domain: description for domain, description in game.LEVELS}
        self.assertIn("D12", domains)
        self.assertIn("D24", domains)

    def test_codec_quest_counts_present_artifacts_without_claiming_pass(self):
        artifacts = {"tests/semantic/d12-signed-width-law.lisp"}
        with patch.object(game, "tracked", return_value=list(artifacts)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = game.main(["--codec"])
        self.assertEqual(code, 0)
        result = out.getvalue()
        self.assertIn("C12-01", result)
        self.assertIn("1/2", result)
        self.assertIn("наявність файлів не означає PASS", result)
        self.assertIn("НАСТУПНИЙ КВЕСТ", result)

    def test_default_progress_labels_scenarios_not_proven_laws(self):
        with patch.object(game, "tracked", return_value=["tests/semantic/d12-signed-width-law.lisp"]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = game.main(["--brief"])
        self.assertEqual(code, 0)
        self.assertIn("сценаріїв", out.getvalue())
        self.assertNotIn("законів", out.getvalue())

    def test_codec_brief_has_quest_counter(self):
        with patch.object(game, "tracked", return_value=[]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = game.main(["--codec", "--brief"])
        self.assertEqual(code, 0)
        self.assertIn("кодек", out.getvalue().lower())
        self.assertIn("0/8", out.getvalue())

if __name__ == "__main__":
    main()
