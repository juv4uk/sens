"""Перевірки зупинки release.lisp; усі зовнішні команди підмінені."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
BINARY = os.environ.get("MY_LISP_RELEASE_TEST_BINARY")
MANIFESTS = ("my-lisp", "my-lisp-cli", "my-lisp-literate", "my-lisp-wasm",
             "my-lisp-lsp", "my-lisp-host", "my-lisp-semantic")


@unittest.skipUnless(BINARY, "потрібен MY_LISP_RELEASE_TEST_BINARY")
class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="release-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls"
        self.log.touch()
        for name in MANIFESTS:
            manifest = self.root / "crates" / name / "Cargo.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('[package]\nversion = "0.40.2"\n')
        self.env = dict(os.environ, PATH=str(self.bin), TEST_LOG=str(self.log))
        self.stub("timeout", 'shift\nexec "$@"')
        self.stub("python3", 'echo "python3 $*" >> "$TEST_LOG"\nexit "${TEST_PYTHON_EXIT:-0}"')
        self.stub("gh", 'echo "gh $*" >> "$TEST_LOG"\necho "${TEST_CI:-true}"')
        self.stub("git", '''echo "git $*" >> "$TEST_LOG"
case "$1" in
  status) printf '%s' "${TEST_DIRTY:-}" ;;
  fetch) exit "${TEST_FETCH_EXIT:-0}" ;;
  log)
    if [ "${4:-}" = FETCH_HEAD ]; then
      printf '%s' "${TEST_REMOTE_HEAD:-abc123}"
    else
      printf '%s' abc123
    fi ;;
  ls-remote) printf '%s' "${TEST_TAG:-}" ;;
  tag) exit "${TEST_TAG_EXIT:-0}" ;;
  push) exit "${TEST_PUSH_EXIT:-0}" ;;
esac
''')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -eu\n" + body + "\n")
        path.chmod(0o755)

    def run_release(self, args=("0.40.2",)):
        return subprocess.run([BINARY, str(ROOT / "scripts/release.lisp"), *args],
                              cwd=self.root, env=self.env, capture_output=True,
                              text=True, timeout=15)

    def test_success_pushes_only_new_tag(self):
        result = self.run_release()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text()
        self.assertIn("git tag l0.40.2 abc123\n", calls)
        self.assertIn("git push origin refs/tags/l0.40.2\n", calls)
        self.assertIn("--commit abc123 --workflow CI", calls)
        self.assertNotIn("--force", calls)

    def test_preflight_failures_never_push(self):
        for variable, value in (("TEST_DIRTY", " M file"), ("TEST_FETCH_EXIT", "1"),
                                ("TEST_CI", "false"), ("TEST_PYTHON_EXIT", "1"),
                                ("TEST_TAG", "abc123 refs/tags/l0.40.2"),
                                ("TEST_TAG_EXIT", "1"),
                                ("TEST_REMOTE_HEAD", "different")):
            with self.subTest(variable=variable):
                self.log.write_text("")
                self.env[variable] = value
                result = self.run_release()
                del self.env[variable]
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("git push", self.log.read_text())

    def test_invalid_arguments_never_execute_commands(self):
        for args in ((), ("0.40.2", "extra")):
            with self.subTest(args=args):
                self.log.write_text("")
                result = self.run_release(args)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.log.read_text(), "")

    def test_mismatched_version_never_pushes(self):
        result = self.run_release(("0.40.3",))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("git push", self.log.read_text())

    def test_push_failure_is_not_reported_as_success(self):
        self.env["TEST_PUSH_EXIT"] = "1"
        result = self.run_release()
        self.assertNotEqual(result.returncode, 0)
