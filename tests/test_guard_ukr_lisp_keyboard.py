"""Адресні регресії Git-guard: staged, push-range, повний вміст Lisp."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch


GUARD = Path(__file__).resolve().parents[1] / "scripts/guard_ukr_lisp_keyboard.py"
sys.path.insert(0, str(GUARD.parent))
import guard_ukr_lisp_keyboard as guard


class UkrainianLispGitGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Тест")
        self.git("config", "user.email", "test@example.invalid")
        self.write("lib/діюче.lisp", "(визначити ім'я 1)\n")
        self.git("add", ".")
        self.git("commit", "-qm", "початковий")
        self.base = self.git("rev-parse", "HEAD").stdout.decode().strip()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True)

    def write(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source if isinstance(source, bytes)
                         else source.encode("utf-8"))

    def check(self, *args, stdin=None):
        return subprocess.run(
            [sys.executable, str(GUARD), *args], cwd=self.root,
            input=stdin, text=True, capture_output=True,
        )

    def test_comments_are_exempt_but_strings_and_code_are_not(self):
        # Коментарі НЕ кодуються у фізичний носій (strip_comments у мінтері),
        # тож у Д7-перевірці їх не чіпаємо.
        for source in (
            "(визначити ім'я 1)\n; TODO\n",
            "; знак —\n",
            "; смайлик 🙂\n",
        ):
            with self.subTest(exempt=source.strip()):
                self.write("lib/діюче.lisp", source)
                self.git("add", "lib/діюче.lisp")
                self.assertEqual(self.check("--staged").returncode, 0)
        # Рядки та код кодуються у носій — перевіряються далі.
        for source, codepoint in (
            ('(визначити рядок "hello")\n', "U+0068"),
            ("(визначити імʼя 1)\n", "U+02BC"),
            ("(визначити ім'я #d1:1)\n", "U+0023"),
        ):
            with self.subTest(codepoint=codepoint):
                self.write("lib/діюче.lisp", source)
                self.git("add", "lib/діюче.lisp")
                outcome = self.check("--staged")
                self.assertEqual(outcome.returncode, 1)
                self.assertIn("lib/діюче.lisp: ", outcome.stderr)
                self.assertIn(codepoint, outcome.stderr)

    def test_staged_not_worktree_and_genuine_keyboard_positive(self):
        self.write("lib/діюче.lisp", "(визначити ім'я x)\n")
        self.git("add", "lib/діюче.lisp")
        self.write("lib/діюче.lisp", "(визначити ім'я 1)\n")
        self.assertEqual(self.check("--staged").returncode, 1)
        self.git("add", "lib/діюче.lisp")
        self.assertEqual(self.check("--staged").returncode, 0)
        self.write("lib/діюче.lisp", "(визначити ім'я 10)\r\n; Ґрунт №1 ₴\n")
        self.git("add", "lib/діюче.lisp")
        self.assertEqual(self.check("--staged").returncode, 0)

    def test_modified_only_and_pre_push_range(self):
        self.write("research/історія.lisp", "; LEGACY\n")
        self.git("add", ".")
        self.git("commit", "-qm", "історичне")
        before = self.git("rev-parse", "HEAD").stdout.decode().strip()
        self.write("lib/діюче.lisp", "(визначити ім'я 2)\n")
        self.git("add", ".")
        self.git("commit", "-qm", "українське")
        head = self.git("rev-parse", "HEAD").stdout.decode().strip()
        self.assertEqual(self.check("--range", before, head).returncode, 0)
        protocol = f"refs/heads/main {head} refs/heads/main {before}\n"
        self.assertEqual(self.check("--pre-push", stdin=protocol).returncode, 0)
        self.write("lib/діюче.lisp", "(визначити ім'я x)\n")
        self.git("add", ".")
        self.git("commit", "-qm", "неприпустиме")
        bad = self.git("rev-parse", "HEAD").stdout.decode().strip()
        outcome = self.check("--pre-push",
                             stdin=f"refs/heads/main {bad} refs/heads/main {before}\n")
        self.assertEqual(outcome.returncode, 1)
        self.assertIn("U+0078", outcome.stderr)

    def test_utf8_corruption_symlink_and_ci_paths(self):
        self.write("lib/діюче.lisp", b"( \xff )\n")
        self.git("add", ".")
        self.assertIn("неправильний UTF-8", self.check("--staged").stderr)
        self.git("reset", "--hard", "HEAD")
        self.write("lib/додано.lisp", "(визначити нове 1)\n")
        self.git("add", ".")
        self.git("commit", "-qm", "додане")
        names = self.root / "changed.txt"
        names.write_text("lib/додано.lisp\nREADME.md\n", encoding="utf-8")
        self.assertEqual(self.check("--paths-from", str(names)).returncode, 0)
        self.write("lib/додано.lisp", "(визначити нове x)\n")
        self.git("add", ".")
        self.git("commit", "-qm", "зламане")
        self.assertEqual(self.check("--paths-from", str(names)).returncode, 1)

    def test_pre_push_fetches_an_unseen_advertised_remote_base_with_timeout(self):
        responses = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"missing"),
            SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
            SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
        ]
        with patch.object(guard.subprocess, "run", side_effect=responses) as run:
            guard.ensure_remote_revision("a" * 40, "refs/heads/main")

        self.assertEqual(run.call_count, 3)
        fetch = run.call_args_list[1]
        self.assertEqual(
            fetch.args[0],
            ["git", "fetch", "--no-tags", "origin", "refs/heads/main"],
        )
        self.assertEqual(fetch.kwargs["timeout"], 20)

    def test_pre_push_fails_closed_if_bounded_fetch_does_not_restore_base(self):
        responses = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"missing"),
            SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"still missing"),
        ]
        with patch.object(guard.subprocess, "run", side_effect=responses):
            with self.assertRaisesRegex(ValueError, "відсутня після bounded fetch"):
                guard.ensure_remote_revision("b" * 40, "refs/heads/main")


if __name__ == "__main__":
    unittest.main()
