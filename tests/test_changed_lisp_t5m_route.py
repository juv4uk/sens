"""Чинний Bash-маршрут Lisp → SENS reader → Zig/T5M → native SENS.

Заглушки нижче перевіряють лише помилки оркестрації shell.
Вони НЕ виконують семантику SENS і НЕ є свідком релізної готовності.
Фактичні закони перевіряє наявний native SENS/Zig CI.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/execute_changed_lisp_t5m.sh"
CI = ROOT / ".github/workflows/ci-heavy.yml"

# Лише фальшивий CLI для перевірки shell exit-code/output parity.
# Жоден результат цього тесту не зараховується як виконання SENS.
ENTRY = """#!/bin/sh
if [ -f invoked ]; then :; else : > invoked; fi
case "$1" in
  --t5m-mint|--t5m-mint-pair)
    if [ -f reject-mint ]; then echo 'mint refused' >&2; exit 17; fi
    printf 'physical from native mint\n' > "$3"
    ;;
  --t5m-pair)
    if [ -f reject-pair ]; then echo 'paired refused' >&2; exit 19; fi
    printf '1\n'
    ;;
  *)
    if [ -f reject-standalone ]; then
      echo 'unknown error' >&2; exit 23
    fi
    if [ -f known-d24 ]; then
      echo 'T5M requires exact source projection to D24+ before transport' >&2
      exit 3
    fi
    if [ -f disagree ]; then printf '0\n'; else printf '1\n'; fi
    ;;
esac
"""
OPEN = """#!/bin/sh
case "$1" in
  open)
    if [ -f reject-open ]; then echo 'view refused' >&2; exit 25; fi
    printf '10 001 00 000 01 01\n'
    ;;
  verify-view)
    if [ -f reject-inverse ]; then echo 'inverse refused' >&2; exit 31; fi
    ;;
  *)
    exit 32
    ;;
esac
"""


class ChangedLispT5MRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-current-native-route-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "module.lisp"
        self.source.write_text("(атом? (як-є ()))\n", encoding="utf-8")
        (self.root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
        self.binary = self.root / "sens-entry"
        self.binary.write_text(ENTRY, encoding="utf-8")
        self.binary.chmod(0o755)
        self.reader = self.root / "sens-trit"
        self.reader.write_text(OPEN, encoding="utf-8")
        self.reader.chmod(0o755)

    def run_shell(self, mode=None):
        env = dict(os.environ, SENS_T5M_OPEN=str(self.reader))
        if mode is not None:
            env["SENS_NATIVE_T5M"] = mode
        else:
            env.pop("SENS_NATIVE_T5M", None)
        return subprocess.run(
            ["bash", str(RUNNER), str(self.binary), "changed.txt", "evidence"],
            cwd=self.root, env=env, text=True, capture_output=True,
            timeout=15,
        )

    def stamp(self, name):
        (self.root / name).touch()

    def test_default_route_is_native_without_python_json_fallback(self):
        script = RUNNER.read_text(encoding="utf-8")
        workflow = CI.read_text(encoding="utf-8")
        self.assertIn("run_native_t5m_program", script)
        self.assertIn('"$binary" "$mint_flag" "$file" "$physical"', script)
        self.assertIn('"$native_open" open "$physical"', script)
        self.assertIn('"$native_open" verify-view "$physical"', script)
        self.assertIn('"$binary" --t5m-pair "$file" "$physical"', script)
        self.assertNotIn("python3 scripts/migrate-three-pass.py", script)
        self.assertIn("SENS_NATIVE_T5M=1", workflow)
        self.assertIn("cargo build --locked -p sens-cli --bin sens --bin sens-trit", workflow)

    def test_default_native_roundtrip_and_execution_parity(self):
        result = self.run_shell()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", result.stdout)
        self.assertIn("files_checked=1 files_failed=0", result.stdout)
        self.assertIn("native_view_roundtrip=1 native_paired_executed=1 native_standalone_parity=1", result.stdout)
        self.assertIn("semantic=NOT_CERTIFIED release=NOT_CERTIFIED", result.stdout)
        self.assertNotIn("release=GO", result.stdout)
        self.assertEqual(len(list((self.root / "evidence").glob("*/module.sens"))), 1)
        self.assertEqual(len(list((self.root / "evidence").glob("*/module"))), 1)

    def test_invalid_mode_never_calls_native_or_python(self):
        result = self.run_shell("python-by-accident")
        self.assertEqual(result.returncode, 2)
        self.assertIn("SENS_NATIVE_T5M_INVALID", result.stderr)
        self.assertFalse((self.root / "invoked").exists())

    def test_explicit_zero_mode_is_also_rejected(self):
        result = self.run_shell("0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("historical Python fallback retired", result.stderr)
        self.assertFalse((self.root / "invoked").exists())

    def test_missing_source_stays_red_without_invoking_sens(self):
        (self.root / "changed.txt").write_text("absent.lisp\n", encoding="utf-8")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2)
        self.assertIn("T5M_CHANGED_SOURCE_INVALID", result.stderr)
        self.assertIn("files_checked=1 files_failed=1", result.stdout)
        self.assertFalse((self.root / "invoked").exists())

    def test_nonregular_committed_pair_rejected_before_mint(self):
        committed = self.root / "module.sens"
        for kind in ("directory", "symlink"):
            with self.subTest(kind=kind):
                if kind == "directory":
                    committed.mkdir()
                else:
                    committed.symlink_to(self.root / "absent.sens")
                result = self.run_shell()
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("T5M_COMMITTED_PAIR_NOT_REGULAR", result.stderr)
                self.assertIn("files_checked=1 files_failed=1", result.stdout)
                self.assertFalse((self.root / "invoked").exists())
                if kind == "directory":
                    committed.rmdir()
                else:
                    committed.unlink()

    def test_native_mint_failure_propagates_without_false_execution(self):
        self.stamp("reject-mint")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2)
        self.assertIn("T5M_NATIVE_MINT_FAILED", result.stderr)
        self.assertIn("native_view_roundtrip=0 native_paired_executed=0 native_standalone_parity=0", result.stdout)
        self.assertNotIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", result.stdout)

    def test_open_and_inverse_fail_closed(self):
        for failure, diagnostic in (
            ("reject-open", "T5M_NATIVE_VIEW_FAILED"),
            ("reject-inverse", "T5M_NATIVE_VIEW_ROUNDTRIP_FAILED"),
        ):
            with self.subTest(failure=failure):
                self.stamp(failure)
                result = self.run_shell()
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(diagnostic, result.stderr)
                self.assertIn("native_paired_executed=0", result.stdout)
                (self.root / failure).unlink()

    def test_paired_execution_failure_is_a_real_red(self):
        self.stamp("reject-pair")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2)
        self.assertIn("T5M_NATIVE_PAIRED_EXECUTION_FAIL", result.stderr)
        self.assertIn("native_view_roundtrip=1 native_paired_executed=0 native_standalone_parity=0", result.stdout)
        self.assertNotIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", result.stdout)

    def test_unexpected_standalone_failure_is_red(self):
        self.stamp("reject-standalone")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2)
        self.assertIn("T5M_NATIVE_STANDALONE_UNEXPECTED_FAIL", result.stderr)
        self.assertIn("native_view_roundtrip=1 native_paired_executed=1 native_standalone_parity=0", result.stdout)

    def test_wrong_standalone_answer_is_red_not_parity(self):
        self.stamp("disagree")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2)
        self.assertIn("T5M_NATIVE_EXECUTION_OUTPUT_DRIFT", result.stderr)
        self.assertIn("files_checked=1 files_failed=1", result.stdout)
        self.assertNotIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", result.stdout)

    def test_known_d24_standalone_limit_only_gives_paired_only(self):
        self.stamp("known-d24")
        result = self.run_shell()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("T5M_NATIVE_PAIRED_ONLY", result.stdout)
        self.assertIn("native_view_roundtrip=1 native_paired_executed=1 native_standalone_parity=0", result.stdout)
        self.assertIn("release=NOT_CERTIFIED", result.stdout)
        self.assertNotIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", result.stdout)

    def test_committed_drift_never_becomes_green_but_still_executes(self):
        (self.root / "module.sens").write_bytes(b"old physical")
        (self.root / "module").write_text("old view\n", encoding="utf-8")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2)
        self.assertIn("T5M_COMMITTED_PAIR_DRIFT", result.stderr)
        self.assertIn("T5M_COMMITTED_VIEW_DRIFT", result.stderr)
        self.assertIn("native_paired_executed=1 native_standalone_parity=1", result.stdout)
        self.assertIn("files_checked=1 files_failed=1", result.stdout)

    def test_orphan_view_is_not_silently_admitted(self):
        (self.root / "module").write_text("stray view\n", encoding="utf-8")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2)
        self.assertIn("T5M_ORPHAN_VIEW", result.stderr)
        self.assertIn("files_checked=1 files_failed=1", result.stdout)

    def test_failed_file_does_not_hide_next_valid_file(self):
        (self.root / "changed.txt").write_text("absent.lisp\nmodule.lisp\n", encoding="utf-8")
        result = self.run_shell()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("T5M_CHANGED_SOURCE_INVALID", result.stderr)
        self.assertIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", result.stdout)
        self.assertIn("files_checked=2 files_failed=1", result.stdout)
        self.assertIn("native_paired_executed=1 native_standalone_parity=1", result.stdout)


if __name__ == "__main__":
    unittest.main()
