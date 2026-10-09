#!/usr/bin/env python3
"""Регресійні тести fail-closed для історичного сканера COND (#5029)."""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cond-modernize.py"
_SPEC = importlib.util.spec_from_file_location("sens_cond_modernize", SCRIPT)
assert _SPEC and _SPEC.loader
cond_modernize = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = cond_modernize
_SPEC.loader.exec_module(cond_modernize)

LEGACY = """(00000111
  ((00000011 x y) (0) (00000001 no-branch))
  ((00000010 x) (1) (00000001 yes-branch)))
"""


def _walk_executable(form):
    """Walk parsed Lisp AST while excluding quoted/discarded program data."""
    if form.opaque:
        return
    yield form
    if cond_modernize.head(form) in cond_modernize.QUOTE_HEADS:
        return
    for child in form.children:
        yield from _walk_executable(child)


def _cond_arity_errors(source: str) -> list[tuple[int, int, int]]:
    """Find COND clauses outside the ratified two-field (test expression) shape."""
    cond_heads = {
        cond_modernize.CURRENT_COND,
        *cond_modernize.LEGACY_COND,
    }
    errors = []
    for root in cond_modernize.parse(source):
        for node in _walk_executable(root):
            if cond_modernize.head(node) not in cond_heads:
                continue
            for clause in node.children[1:]:
                arity = len(clause.children)
                if arity != 2:
                    errors.append((node.line, clause.line, arity))
    return errors


class CondModernizeGuardTests(unittest.TestCase):
    def run_scanner(self, root: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_yes_and_no_never_rewrite_source_or_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = root / "legacy.lisp"
            source.write_text(LEGACY, encoding="utf-8")
            stage = root / "stage"
            for extra in ((), ("--out", str(stage))):
                with self.subTest(extra=extra):
                    run = self.run_scanner(root, str(source), *extra)
                    self.assertEqual(run.returncode, 4, run.stdout + run.stderr)
                    self.assertIn("BLOCK:", run.stdout)
                    self.assertEqual(source.read_bytes(), LEGACY.encode("utf-8"))
                    self.assertFalse(stage.exists(), "No preview artifact is authorized")

    def test_unrecognized_patterns_never_get_false_green(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = root / "other.lisp"
            original = '; (00000111 ((00000011 x y) (0) (00000001 quoted)))\n"not executable"\n'
            source.write_text(original, encoding="utf-8")
            run = self.run_scanner(root, str(source))
            self.assertEqual(run.returncode, 4, run.stdout + run.stderr)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_scan_remains_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            library = root / "lib"
            library.mkdir()
            source = library / "legacy.lisp"
            source.write_text(LEGACY, encoding="utf-8")
            run = self.run_scanner(root, "--scan")
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("# файлів зі старими cond-клаузами: 1", run.stdout)
            self.assertEqual(source.read_text(encoding="utf-8"), LEGACY)

    def test_arity_guard_detects_legacy_clause_and_skips_quoted_data(self) -> None:
        self.assertEqual(len(_cond_arity_errors(LEGACY)), 2)
        self.assertEqual(_cond_arity_errors("'" + LEGACY), [])

    def test_live_pairlis_and_let_star_use_only_two_field_cond_clauses(self) -> None:
        # These macro definitions caused the real Hosted CI failure. Read their
        # live canonical sources with the shared AST parser, not grep.
        for relative in ("lib/core.lisp", "lib/core4.lisp"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            roots = cond_modernize.parse(source)
            for symbol in ("спарувати", "let*"):
                with self.subTest(file=relative, definition=symbol):
                    matches = [
                        form for form in roots
                        if len(form.children) > 2
                        and form.children[1].atom == symbol
                    ]
                    self.assertEqual(
                        len(matches), 1,
                        f"{relative}: expected exactly one live definition for {symbol}",
                    )
                    form = matches[0]
                    definition_source = source[form.start:form.end]
                    errors = _cond_arity_errors(definition_source)
                    self.assertEqual(
                        errors, [],
                        f"{relative}:{symbol}: executable COND clause arity errors: {errors}",
                    )


if __name__ == "__main__":
    unittest.main()
